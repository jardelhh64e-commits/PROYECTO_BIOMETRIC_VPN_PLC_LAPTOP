"""
liveness.py — Prueba de vida: parpadeo (EAR) + giro de cabeza (yaw heurístico).
Auto-reinicia la ventana si expira sin lograr OK y reporta el reset.
"""
import math
import numpy as np

# Índices aproximados de ojos (FaceMesh 468 pts)
LEFT_EYE  = [33, 160, 158, 133, 153, 144]    # (p1,p2,p3,p4,p5,p6)
RIGHT_EYE = [263, 387, 385, 362, 380, 373]

def _dist(a, b):
    return math.dist(a, b)

def _eye_aspect_ratio(pts):
    p1, p2, p3, p4, p5, p6 = pts
    num = _dist(p2, p6) + _dist(p3, p5)
    den = 2.0 * _dist(p1, p4)
    if den <= 1e-6:
        return 0.0
    return num / den

def _estimate_yaw_deg(nose, left_eye, right_eye):
    mid_x = (left_eye[0] + right_eye[0]) * 0.5
    dx = nose[0] - mid_x
    eye_dist = abs(right_eye[0] - left_eye[0]) + 1e-6
    yaw_norm = dx / eye_dist
    return float(yaw_norm * 10.0)  # escala aprox a "grados"

class LivenessGuard:
    def __init__(self, cfg):
        self.cfg = cfg
        self.reset()

    def reset(self):
        self.start_t = None
        self.closed_frames = 0
        self.blinked = False
        self.yaw_ok = False
        self.last_yaw = 0.0

    def update(self, landmarks_px, now_s):
        """
        landmarks_px: lista/array de (x,y) en píxeles (468 puntos) o None.
        return: dict con flags y textos para UI.
                Incluye 'did_reset' = True si la ventana expiró y se reinició.
        """
        if landmarks_px is None:
            return {"blink_ok": False, "yaw_ok": False, "yaw": 0.0,
                    "ok": False, "hint": "Sin rostro", "did_reset": False}

        if self.start_t is None:
            self.start_t = now_s

        # EAR (promedio ambos ojos)
        try:
            le = [landmarks_px[i] for i in LEFT_EYE]
            re = [landmarks_px[i] for i in RIGHT_EYE]
            ear = 0.5 * (_eye_aspect_ratio(le) + _eye_aspect_ratio(re))
        except Exception:
            ear = 1.0  # considerar abierto

        if ear < self.cfg.EAR_THRESHOLD:
            self.closed_frames += 1
        else:
            if self.closed_frames >= self.cfg.EAR_MIN_FRAMES:
                self.blinked = True
            self.closed_frames = 0

        # Yaw con nariz y centro de ojos
        try:
            nose = landmarks_px[1]
            le_center = np.mean([landmarks_px[i] for i in [33, 133]], axis=0)
            re_center = np.mean([landmarks_px[i] for i in [263, 362]], axis=0)
            yaw_deg = _estimate_yaw_deg(tuple(nose), tuple(le_center), tuple(re_center))
        except Exception:
            yaw_deg = 0.0

        # Si usas espejo y se invierte el sentido, descomenta:
        # if getattr(self.cfg, "USE_SELFIE_FLIP", False):
        #     yaw_deg = -yaw_deg

        self.last_yaw = yaw_deg
        if abs(yaw_deg) >= self.cfg.YAW_DEG_TARGET:
            self.yaw_ok = True

        # Ventana temporal: si <=0, sin límite
        if getattr(self.cfg, "LIVENESS_WINDOW_S", 0) and self.cfg.LIVENESS_WINDOW_S > 0:
            window_ok = (now_s - self.start_t) <= self.cfg.LIVENESS_WINDOW_S
        else:
            window_ok = True

        ok = self.blinked and self.yaw_ok and window_ok

        # Mensaje
        if not self.blinked:
            hint = self.cfg.LIVENESS_MSG_BLINK
        elif not self.yaw_ok:
            hint = self.cfg.LIVENESS_MSG_TURN if yaw_deg >= 0 else self.cfg.LIVENESS_MSG_TURN.replace("IZQUIERDA", "DERECHA")
        elif not window_ok:
            hint = self.cfg.LIVENESS_MSG_FAIL
        else:
            hint = self.cfg.LIVENESS_MSG_OK

        did_reset = False
        # Auto-reset de ventana si expiró sin lograr OK
        if not ok and not window_ok:
            self.start_t = now_s
            self.blinked = False
            self.yaw_ok = False
            self.closed_frames = 0
            hint = "Reintenta: " + self.cfg.LIVENESS_MSG_BLINK
            did_reset = True

        return {"blink_ok": self.blinked, "yaw_ok": self.yaw_ok, "yaw": yaw_deg,
                "ok": ok, "hint": hint, "did_reset": did_reset}
