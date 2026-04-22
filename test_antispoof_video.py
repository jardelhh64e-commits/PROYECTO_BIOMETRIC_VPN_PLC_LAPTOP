"""
test_antispoof_video.py
Banco de pruebas para el modulo antispoof_video.VideoAntispoofGuard.

Uso:
  python test_antispoof_video.py --mode real  --trials 20 --subject S1
  python test_antispoof_video.py --mode video --trials 20 --subject S1 --distance 30

Cada intento (trial) corre una secuencia nueva de retos aleatorios.
Se registra en un CSV: modo, sujeto, distancia, retos, resultado, duracion.

Metricas derivadas:
  - FRR (False Rejection Rate) en modo 'real'   = trials_fallidos / total
  - VSDR (Video Spoof Detection Rate) en 'video' = trials_fallidos / total
"""
import argparse
import csv
import os
import time
from datetime import datetime

import cv2
import mediapipe as mp

from antispoof_video import VideoAntispoofGuard, CHALLENGE_WINDOW_S


CSV_PATH = "antispoof_results.csv"
CAM_INDEX = 0
NUM_CHALLENGES = 5


def _landmarks_from_frame(face_mesh, frame):
    h, w = frame.shape[:2]
    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res  = face_mesh.process(rgb)
    if not res.multi_face_landmarks:
        return None
    lm = res.multi_face_landmarks[0].landmark
    return [(p.x * w, p.y * h) for p in lm]


def _draw_hud(frame, state, trial_idx, trials_total, mode):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 90), (0, 0, 0), -1)

    cv2.putText(frame, f"Mode: {mode}  Trial: {trial_idx}/{trials_total}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    if state["status"] == "running":
        cv2.putText(frame, f"Reto {state['current_idx']+1}/{state['total']}: {state['instruction']}",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"t_restante: {state['time_left']:.1f}s   blinks: {state['blink_count']}",
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    else:
        color = (0, 255, 0) if state["status"] == "completed" else (0, 0, 255)
        cv2.putText(frame, f"RESULTADO: {state['status'].upper()}",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def run_trial(cap, face_mesh, guard, trial_idx, trials_total, mode):
    guard.reset()
    t0 = time.time()
    last_state = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)

        lms   = _landmarks_from_frame(face_mesh, frame)
        state = guard.update(lms, time.time())
        last_state = state

        _draw_hud(frame, state, trial_idx, trials_total, mode)
        cv2.imshow("antispoof_test", frame)

        key = cv2.waitKey(1) & 0xFF
        if state["status"] != "running":
            # muestro el resultado ~1s para poder filmarlo
            t_show = time.time()
            while time.time() - t_show < 1.0:
                ok2, f2 = cap.read()
                if ok2:
                    f2 = cv2.flip(f2, 1)
                    _draw_hud(f2, state, trial_idx, trials_total, mode)
                    cv2.imshow("antispoof_test", f2)
                cv2.waitKey(1)
            break
        if key == ord("q"):
            return None

    dur = time.time() - t0
    return {
        "status":   last_state["status"] if last_state else "failed",
        "sequence": "|".join(last_state["sequence"]) if last_state else "",
        "duration": round(dur, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["real", "video"], required=True,
                    help="real = persona frente a la camara; video = replay en celular/monitor")
    ap.add_argument("--trials",   type=int, default=20)
    ap.add_argument("--subject",  default="S1", help="etiqueta del sujeto/video")
    ap.add_argument("--distance", default="-", help="distancia camara-pantalla (cm) si mode=video")
    ap.add_argument("--seed",     type=int, default=None, help="semilla RNG (opcional, reproducible)")
    args = ap.parse_args()

    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise SystemExit("No pude abrir la webcam")

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True,
        min_detection_confidence=0.6, min_tracking_confidence=0.6,
    )

    guard = VideoAntispoofGuard(num_challenges=NUM_CHALLENGES, selfie_flip=True, seed=args.seed)

    new_file = not os.path.exists(CSV_PATH)
    fcsv = open(CSV_PATH, "a", newline="", encoding="utf-8")
    w = csv.writer(fcsv)
    if new_file:
        w.writerow(["timestamp", "mode", "subject", "distance_cm",
                    "trial", "sequence", "status", "duration_s",
                    "challenge_window_s"])

    print(f"[TEST] mode={args.mode} subject={args.subject} trials={args.trials}")
    print(f"[TEST] CSV -> {os.path.abspath(CSV_PATH)}")

    passed = failed = 0
    for i in range(1, args.trials + 1):
        res = run_trial(cap, face_mesh, guard, i, args.trials, args.mode)
        if res is None:
            print("[TEST] cancelado por el usuario (q).")
            break
        ts = datetime.now().isoformat(timespec="seconds")
        w.writerow([ts, args.mode, args.subject, args.distance,
                    i, res["sequence"], res["status"], res["duration"],
                    CHALLENGE_WINDOW_S])
        fcsv.flush()
        if res["status"] == "completed":
            passed += 1
        else:
            failed += 1
        print(f"  trial {i:02d}: {res['status']:10s}  seq={res['sequence']}  dur={res['duration']}s")

    fcsv.close()
    cap.release()
    cv2.destroyAllWindows()

    total = passed + failed
    if total:
        if args.mode == "real":
            frr = failed / total
            print(f"\n[RESUMEN real]  passed={passed}/{total}  FRR={frr:.2%}")
        else:
            vsdr = failed / total
            print(f"\n[RESUMEN video] detected={failed}/{total}  VSDR={vsdr:.2%}")


if __name__ == "__main__":
    main()
