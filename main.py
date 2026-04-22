"""
main.py — Dos ventanas:
1) Webcam + (FaceMesh si está disponible) + overlays de nombre/confianza/estados/liveness
2) Webcam (raw)
PLC: solo probar conexión (prints). Reintentar con tecla 'P'.
ESC = salir.   Q = reanudar (NO ENTRENADA) o regresar de menú (ENTRENADA).
"""
import time, traceback, urllib.request, urllib.parse
import cv2
import config
import ui
from camera_open import open_camera
from classifier import Classifier
from timer import should_run
from plc_client import PLCClient
from liveness import LivenessGuard, _eye_aspect_ratio, LEFT_EYE, RIGHT_EYE
from antispoof_video import VideoAntispoofGuard

# ===== Candado: bloquea HTTP hasta que biometría autorice =====
GATE_ENABLED = False

AUTO_OFF_ON_EXIT = False

# --- Enviar status a n8n usando tu módulo CLI (misma carpeta que main.py)
try:
    from plc_status_cli import send_status as n8n_send_status
except Exception as _e:
    def n8n_send_status(value: int):
        print("[WARN] plc_status_cli.py no encontrado o 'requests' no instalado:", repr(_e))

# ===== Cliente HTTP con HMAC-SHA256 (usa llave_cliente.py) =====
import hmac as _hmac, hashlib as _hashlib, uuid as _uuid
import llave_cliente as _lc

def _http_call(action: str, extra_params=None) -> str:
    global GATE_ENABLED
    if not GATE_ENABLED:
        return "[HTTP] BLOQUEADO: biometría aún no habilitó el paso."

    ts    = str(int(time.time()))
    nonce = _uuid.uuid4().hex
    msg   = f"{action}{ts}{nonce}".encode()
    sig   = _hmac.new(_lc.SHARED_KEY, msg, _hashlib.sha256).hexdigest()

    path   = "/status" if action == "status" else "/set"
    params = {"action": action, "ts": ts, "nonce": nonce, "sig": sig}
    qs     = urllib.parse.urlencode(params)
    url    = f"http://{_lc.HOST}:{_lc.PORT}{path}?{qs}"
    with urllib.request.urlopen(url, timeout=8) as r:
        return r.read().decode(errors="replace").strip()

# FaceMesh opcional
mesh_enabled = True
fm = None
try:
    from mediapipe_face_mesh import FaceMeshDrawer
except Exception as e:
    print("[WARN] No se pudo importar FaceMeshDrawer. Continuando sin malla. Detalle:", repr(e))
    mesh_enabled = False

WIN_MESH = "Webcam + FaceMesh"
WIN_RAW  = "Webcam (raw)"
WIN_SIZE = config.CAM_RES if config.CAM_RES else (640, 480)

def _position_windows():
    cv2.resizeWindow(WIN_MESH, WIN_SIZE[0], WIN_SIZE[1])
    cv2.resizeWindow(WIN_RAW,  WIN_SIZE[0], WIN_SIZE[1])
    cv2.moveWindow(WIN_MESH, 50, 50)
    cv2.moveWindow(WIN_RAW,  50 + WIN_SIZE[0] + 20, 50)

def _pause_noauth_freeze(mesh_img, raw_img):
    t0 = time.time()
    while True:
        f1 = mesh_img.copy()
        f2 = raw_img.copy() if raw_img is not None else None
        ui.draw_big_alert(f1, ui.MSG_NOTRAINED)
        ui.draw_hint(f1, ui.MSG_WAITING, 40)
        if (time.time() - t0) >= getattr(config, "NOAUTH_OVERLAY_S", 3.0):
            ui.draw_hint(f1, ui.MSG_PAUSED_HINT, f1.shape[0] - 12)
        cv2.imshow(WIN_MESH, f1)
        if f2 is not None: cv2.imshow(WIN_RAW, f2)
        _position_windows()
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            return "resume"
        if k == 27:
            return "exit"

def _pause_trained_console_menu(mesh_img, raw_img, ident_label):
    t0 = time.time()
    while (time.time() - t0) < getattr(config, "TRAINED_OVERLAY_S", 3.0):
        f1 = mesh_img.copy()
        f2 = raw_img.copy() if raw_img is not None else None
        ui.draw_big_success(f1, ui.MSG_TRAINED)
        ui.draw_hint(f1, f"Identificado: {ident_label}", 40)
        cv2.imshow(WIN_MESH, f1)
        if f2 is not None: cv2.imshow(WIN_RAW, f2)
        _position_windows()
        if (cv2.waitKey(1) & 0xFF) == 27:
            return "exit"

    f1 = mesh_img.copy()
    f2 = raw_img.copy() if raw_img is not None else None
    ui.draw_big_success(f1, ui.MSG_TRAINED)
    ui.draw_hint(f1, f"Identificado: {ident_label}", 40)
    ui.draw_hint(f1, ui.MSG_PAUSED_HINT, f1.shape[0] - 12)
    cv2.imshow(WIN_MESH, f1)
    if f2 is not None: cv2.imshow(WIN_RAW, f2)
    _position_windows()
    cv2.waitKey(1)

    while True:
        try:
            op = input("\n1=activar, 0=desactivar, 2=status, q=salir: ").strip().lower()
        except EOFError:
            op = "q"

        if op == "1":
            # RPi: ON
            try:
                print(_http_call("on"))
            except Exception as e:
                print(f"[HTTP] ERROR (RPi on): {e}")
            # n8n: status=1
            try:
                n8n_send_status(1)
            except Exception as e:
                print(f"[N8N] ERROR (status=1): {e}")

        elif op == "0":
            # RPi: OFF
            try:
                print(_http_call("off"))
            except Exception as e:
                print(f"[HTTP] ERROR (RPi off): {e}")
            # n8n: status=0
            try:
                n8n_send_status(0)
            except Exception as e:
                print(f"[N8N] ERROR (status=0): {e}")

        elif op == "2":
            # Solo consulta estado en la RPi (no manda a n8n)
            try:
                print(_http_call("status"))
            except Exception as e:
                print(f"[HTTP] ERROR (status): {e}")

        elif op == "q":
            if AUTO_OFF_ON_EXIT:
                try:
                    print(_http_call("off"))
                except Exception as e:
                    print(f"[HTTP] ERROR OFF auto: {e}")
            print("Saliendo.")
            break
        else:
            print("Opción inválida.")

    return "resume"

def _show_message(cap, duration_s, title, subtitle="", color=(0, 255, 255)):
    """
    Dibuja un mensaje a pantalla completa sobre los frames de la cámara
    durante duration_s segundos. Devuelve 'exit' si ESC, si no 'ok'.
    """
    t0   = time.time()
    flip = getattr(config, "USE_SELFIE_FLIP", False)
    while time.time() - t0 < duration_s:
        ok, frame = cap.read()
        if not ok:
            cv2.waitKey(10)
            continue
        if flip:
            frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 130), (0, 0, 0), -1)
        cv2.putText(frame, title,
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2)
        if subtitle:
            cv2.putText(frame, subtitle,
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)
        cv2.imshow(WIN_MESH, frame)
        cv2.imshow(WIN_RAW,  frame)
        _position_windows()
        if (cv2.waitKey(1) & 0xFF) == 27:
            return "exit"
    return "ok"


def _run_antispoof_step(cap, fm_ref):
    """
    Ejecuta la secuencia de retos anti-video (desafío-respuesta).
    Devuelve 'passed', 'failed' o 'exit'.
    """
    # --- Intro A1: confirmación biométrica ---
    if _show_message(cap, 1.5,
                     "RECONOCIMIENTO BIOMETRICO EXITOSO",
                     "Identidad verificada",
                     (0, 255, 0)) == "exit":
        return "exit"

    # --- Intro A2: anuncio del anti-spoofing ---
    if _show_message(cap, 1.5,
                     "ANTI-SPOOFING LIVENESS CHALLENGE",
                     "Preparese para 5 pruebas...",
                     (0, 255, 255)) == "exit":
        return "exit"

    guard = VideoAntispoofGuard(
        num_challenges=5,
        selfie_flip=getattr(config, "USE_SELFIE_FLIP", False),
    )
    guard.challenge_start = time.time()   # reiniciar timer después del intro
    print("[ANTISPOOF] Secuencia:", guard.sequence)

    prev_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            if (cv2.waitKey(10) & 0xFF) == 27:
                return "exit"
            continue

        if getattr(config, "USE_SELFIE_FLIP", False):
            frame = cv2.flip(frame, 1)

        mesh_frame = frame.copy()
        raw_frame  = frame.copy()

        landmarks = None
        if fm_ref is not None:
            try:
                landmarks, mesh_frame = fm_ref.process(mesh_frame)
            except Exception:
                pass

        state = guard.update(landmarks, time.time())

        # --- Final exitoso ---
        if state["status"] == "completed":
            if _show_message(cap, 1.5,
                             "VERIFICACION COMPLETA",
                             "Autorizando acceso...",
                             (0, 255, 0)) == "exit":
                return "exit"
            return "passed"

        # --- Fallo por timeout ---
        if state["status"] == "failed":
            _show_message(cap, 1.5,
                          "VERIFICACION FALLIDA",
                          "Reintentando reconocimiento...",
                          (0, 0, 255))
            return "failed"

        # --- Transición entre retos ---
        if state["current_idx"] > prev_idx:
            if _show_message(cap, 1.5,
                             "CORRECTO",
                             "Siguiente reto...",
                             (0, 255, 0)) == "exit":
                return "exit"
            prev_idx = state["current_idx"]
            guard.challenge_start = time.time()   # no descontar el 1.5s del reto
            continue

        # --- HUD normal del reto actual ---
        h, w = mesh_frame.shape[:2]
        cv2.rectangle(mesh_frame, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.putText(mesh_frame,
                    f"Anti-Spoofing Liveness Challenge:",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(mesh_frame,
                    f"Total: {state['current_idx']+1}/{state['total']}: {state['instruction']}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(mesh_frame,
                    f"Limit Time: {state['time_left']:.1f}s   blinks: {state['blink_count']}",
                    (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 220, 220), 1)

        cv2.imshow(WIN_MESH, mesh_frame)
        cv2.imshow(WIN_RAW,  raw_frame)
        _position_windows()

        if (cv2.waitKey(1) & 0xFF) == 27:
            return "exit"


def main():
    print("[INFO] Abriendo cámara en índice {}...".format(config.CAM_INDEX))
    cap = open_camera()

    print("[STEP] Cargando Classifier (TensorFlow + modelo + labels)...")
    clf = Classifier()
    print("[OK  ] Classifier listo.")

    global fm, mesh_enabled
    if mesh_enabled:
        print("[STEP] Inicializando FaceMesh...")
        try:
            fm = FaceMeshDrawer()
            print("[OK  ] FaceMesh inicializado.")
        except Exception as e:
            print("[WARN] Falló crear FaceMesh. Continuando sin malla. Detalle:", repr(e))
            mesh_enabled = False

    plc = None
    if getattr(config, "USE_PLC", False):
        print("[STEP] Intentando conectar al PLC...")
        plc = PLCClient(config.PLC_IP, config.PLC_RACK, config.PLC_SLOT)
        plc.connect()

    live = LivenessGuard(config)

    cv2.namedWindow(WIN_MESH, cv2.WINDOW_NORMAL)
    cv2.namedWindow(WIN_RAW,  cv2.WINDOW_NORMAL)
    _position_windows()

    auth_start_time   = None
    noauth_start_time = None
    stable_active     = False
    liveness_passed   = False        # enganche de liveness
    liveness_reported = False        # imprime una sola vez "LIVENESS OK"

    while True:
        try:
            ok, frame = cap.read()
            if not ok:
                print("[WARN] No se pudo leer frame (reintentando)...")
                if (cv2.waitKey(10) & 0xFF) == 27:
                    break
                continue

            if getattr(config, "USE_SELFIE_FLIP", False):
                frame = cv2.flip(frame, 1)

            raw_frame  = frame.copy()
            mesh_frame = frame.copy()

            # FaceMesh
            landmarks = None
            if mesh_enabled and fm is not None:
                try:
                    landmarks, mesh_frame = fm.process(mesh_frame)
                except Exception as e:
                    print("[WARN] Error en FaceMesh.process(); deshabilitando malla. Detalle:", repr(e))
                    mesh_enabled = False

            # Predicción
            class_label, conf = clf.predict(raw_frame)

            # Liveness con enganche + reportes a terminal
            if getattr(config, "USE_LIVENESS", False):
                now_s = time.time()
                lv = live.update(landmarks, now_s)

                # Reportar reset de ventana (cada vez que ocurra)
                if lv.get("did_reset", False):
                    print("[LIVENESS] Reset: ventana expirada, reiniciando prueba.")

                # Reportar OK una sola vez por ciclo
                if lv.get("ok", False):
                    liveness_passed = True
                    if not liveness_reported:
                        print("[LIVENESS] OK: parpadeo + giro dentro de ventana.")
                        liveness_reported = True

                # Overlays de liveness
                ui.draw_liveness_hint(mesh_frame, lv.get("hint",""), 30)
                ui.draw_liveness_status(mesh_frame, lv.get("blink_ok", False),
                                        lv.get("yaw_ok", False), lv.get("yaw", 0.0), 60)

                # EAR en pantalla (no terminal)
                try:
                    if landmarks:
                        le = [landmarks[i] for i in LEFT_EYE]
                        re = [landmarks[i] for i in RIGHT_EYE]
                        ear = 0.5*(_eye_aspect_ratio(le) + _eye_aspect_ratio(re))
                        ui.draw_ear_debug(mesh_frame, ear, config.EAR_THRESHOLD, 90)
                except Exception:
                    pass
            else:
                liveness_passed = True

            # ---------- ENTRENADA (estable) ----------
            if conf >= config.STABLE_CONF and liveness_passed:
                if auth_start_time is None:
                    auth_start_time = time.time()
                    stable_active   = False
                else:
                    elapsed = time.time() - auth_start_time
                    if not stable_active and elapsed >= config.STABLE_TIME_S:
                        print(f"[AUTHORIZED] {ui.RECOGNIZER_NAME}: {class_label} | Confianza: {conf:.3f} | Estable: {elapsed:.1f}s")
                        stable_active = True

                        # --- Anti-spoof de video pre-grabado (desafío-respuesta) ---
                        print("[ANTISPOOF] Iniciando retos aleatorios...")
                        anti_res = _run_antispoof_step(cap, fm if mesh_enabled else None)
                        if anti_res == "exit":
                            break
                        if anti_res != "passed":
                            print("[ANTISPOOF] FALLÓ: no se habilita el gate. Reiniciando ciclo.")
                            live.reset()
                            liveness_passed   = False
                            liveness_reported = False
                            auth_start_time   = None
                            noauth_start_time = None
                            stable_active     = False
                            continue
                        print("[ANTISPOOF] OK: retos superados.")

                        # Habilitar el paso HTTP después de la autorización biométrica + anti-spoof
                        global GATE_ENABLED
                        GATE_ENABLED = True

                        last_mesh = mesh_frame.copy()
                        last_raw  = raw_frame.copy()
                        res = _pause_trained_console_menu(last_mesh, last_raw, class_label)

                        # (Opcional) cerrar el candado al salir del menú ENTRENADA
                        GATE_ENABLED = False

                        # Reset para el próximo ciclo
                        live.reset()
                        liveness_passed   = False
                        liveness_reported = False
                        if res == "exit":
                            break
                        auth_start_time   = None
                        noauth_start_time = None
                        stable_active     = False
            else:
                auth_start_time = None
                stable_active   = False

            # ---------- NO ENTRENADA ----------
            if conf < config.NOAUTH_CONF:
                if noauth_start_time is None:
                    noauth_start_time = time.time()
                else:
                    low_elapsed = time.time() - noauth_start_time
                    if low_elapsed >= config.NOAUTH_TIME_S:
                        print(f"[INFO] NO ENTRENADA disparado (conf={conf:.3f}).")
                        last_mesh = mesh_frame.copy()
                        last_raw  = raw_frame.copy()
                        res = _pause_noauth_freeze(last_mesh, last_raw)
                        live.reset()
                        liveness_passed   = False
                        liveness_reported = False
                        if res == "exit":
                            break
                        auth_start_time   = None
                        noauth_start_time = None
                        stable_active     = False
            else:
                noauth_start_time = None

            # Overlays
            ui.draw_name_and_confidence(mesh_frame, class_label, conf)

            # Mostrar
            cv2.imshow(WIN_MESH, mesh_frame)
            cv2.imshow(WIN_RAW,  raw_frame)
            _position_windows()

            # Teclado
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break
            if k in (ord('p'), ord('P')):
                if not getattr(config, "USE_PLC", False):
                    print("[PLC] USE_PLC=False en config; habilítalo para probar conexión.")
                else:
                    try:
                        if plc is None:
                            plc = PLCClient(config.PLC_IP, config.PLC_RACK, config.PLC_SLOT)
                        else:
                            plc.disconnect()
                            plc = PLCClient(config.PLC_IP, config.PLC_RACK, config.PLC_SLOT)
                        plc.connect()
                    except Exception as e:
                        print(f"[PLC] Error al reintentar conexión: {e}")

        except Exception:
            print("[EXCEPTION] Se capturó una excepción; el programa NO se cerrará.")
            traceback.print_exc()
            time.sleep(0.05)
            continue

    # ===== Cierre =====
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass
    try:
        if fm is not None:
            fm.close()
    except Exception:
        pass
    try:
        if plc is not None:
            plc.disconnect()
    except Exception:
        pass
    cv2.destroyAllWindows()
    print("[INFO] Cerrado OK.")

if __name__ == "__main__":
    main()
