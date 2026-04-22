"""
antispoof_video.py
Challenge-response anti-spoofing contra ataques por video pre-grabado.
Genera una secuencia aleatoria de gestos que el atacante no puede predecir.
"""
import math
import random
import time

LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [263, 387, 385, 362, 380, 373]
NOSE      = 1

EAR_CLOSED_TH      = 0.22   # por debajo = ojo cerrado (histéresis)
EAR_OPEN_TH        = 0.28   # por encima = ojo abierto
MIN_BLINK_GAP_S    = 0.20   # separación mínima entre parpadeos válidos
YAW_TARGET_DEG     = 8.0    # giro mínimo de cabeza
YAW_NEUTRAL_DEG    = 4.0    # |yaw| debe caer bajo este umbral antes de aceptar giro
CHALLENGE_WINDOW_S = 7.0    # tiempo máximo por cada reto
WINK_HOLD_FRAMES   = 3      # frames consecutivos para validar un guiño

ENABLE_WINK = False         # True = incluir retos de guiño de un solo ojo

_BASE_ACTIONS = [
    ("blink_2",    "Parpadee 2 veces"),
    ("blink_3",    "Parpadee 3 veces"),
    ("turn_left",  "Gire la cabeza a la IZQUIERDA"),
    ("turn_right", "Gire la cabeza a la DERECHA"),
]
_WINK_ACTIONS = [
    ("wink_left",  "Guiñe SOLO el ojo IZQUIERDO"),
    ("wink_right", "Guiñe SOLO el ojo DERECHO"),
]
ACTIONS = _BASE_ACTIONS + (_WINK_ACTIONS if ENABLE_WINK else [])


def _eye_aspect_ratio(pts):
    def d(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
    A = d(pts[1], pts[5]); B = d(pts[2], pts[4]); C = d(pts[0], pts[3])
    return (A + B) / (2.0 * C) if C > 0 else 0.0


def _estimate_yaw(landmarks, selfie_flip=False):
    try:
        nose = landmarks[NOSE]
        le_x = sum(landmarks[i][0] for i in LEFT_EYE)  / len(LEFT_EYE)
        re_x = sum(landmarks[i][0] for i in RIGHT_EYE) / len(RIGHT_EYE)
        eye_center = (le_x + re_x) / 2.0
        eye_dist   = abs(re_x - le_x)
        if eye_dist < 1: return 0.0
        offset = (nose[0] - eye_center) / eye_dist
        offset = max(-1.0, min(1.0, offset))
        yaw = math.degrees(math.asin(offset))
        return -yaw if selfie_flip else yaw
    except Exception:
        return 0.0


class VideoAntispoofGuard:
    def __init__(self, num_challenges=3, selfie_flip=False, seed=None):
        self.num_challenges = num_challenges
        self.selfie_flip    = selfie_flip
        self._rng           = random.Random(seed)
        self.reset()

    def _pick_sequence(self, n):
        seq, last = [], None
        for _ in range(n):
            options = [a for a in ACTIONS if a != last]
            pick = self._rng.choice(options)
            seq.append(pick)
            last = pick
        return seq

    def reset(self):
        self.sequence        = self._pick_sequence(self.num_challenges)
        self.current_idx     = 0
        self.challenge_start = time.time()
        self.blink_count     = 0
        self._eye_closed     = False
        self._last_blink_t   = 0.0
        self._wink_frames    = 0
        self._neutral_seen   = False
        self._open_seen      = False
        self.status          = "running"   # running | completed | failed

    def _advance(self):
        self.current_idx += 1
        self.challenge_start = time.time()
        self.blink_count     = 0
        self._eye_closed     = False
        self._last_blink_t   = 0.0
        self._wink_frames    = 0
        self._neutral_seen   = False
        self._open_seen      = False
        if self.current_idx >= len(self.sequence):
            self.status = "completed"

    def _current(self):
        if self.current_idx >= len(self.sequence): return None
        return self.sequence[self.current_idx]

    def update(self, landmarks, now_s):
        if self.status != "running":
            return self._state()

        if now_s - self.challenge_start > CHALLENGE_WINDOW_S:
            self.status = "failed"
            return self._state()

        ch = self._current()
        if ch is None or not landmarks:
            return self._state()

        key, _ = ch

        if key.startswith("blink_"):
            need = int(key.split("_")[1])
            le = [landmarks[i] for i in LEFT_EYE]
            re = [landmarks[i] for i in RIGHT_EYE]
            ear = 0.5 * (_eye_aspect_ratio(le) + _eye_aspect_ratio(re))

            # Exigir un estado inicial de ojos claramente abiertos
            if ear > EAR_OPEN_TH:
                self._open_seen = True

            if self._open_seen:
                if self._eye_closed:
                    if ear > EAR_OPEN_TH:
                        if now_s - self._last_blink_t > MIN_BLINK_GAP_S:
                            self.blink_count  += 1
                            self._last_blink_t = now_s
                        self._eye_closed = False
                else:
                    if ear < EAR_CLOSED_TH:
                        self._eye_closed = True

            if self.blink_count >= need:
                self._advance()

        elif key == "turn_left":
            yaw = _estimate_yaw(landmarks, self.selfie_flip)
            if abs(yaw) < YAW_NEUTRAL_DEG:
                self._neutral_seen = True
            if self._neutral_seen and yaw < -YAW_TARGET_DEG:
                self._advance()

        elif key == "turn_right":
            yaw = _estimate_yaw(landmarks, self.selfie_flip)
            if abs(yaw) < YAW_NEUTRAL_DEG:
                self._neutral_seen = True
            if self._neutral_seen and yaw > YAW_TARGET_DEG:
                self._advance()

        elif key in ("wink_left", "wink_right"):
            ear_L = _eye_aspect_ratio([landmarks[i] for i in LEFT_EYE])
            ear_R = _eye_aspect_ratio([landmarks[i] for i in RIGHT_EYE])
            # "wink_left" = usuario cierra su ojo izquierdo, mantiene abierto el derecho
            if key == "wink_left":
                closed, opened = ear_L, ear_R
            else:
                closed, opened = ear_R, ear_L
            if closed < EAR_CLOSED_TH and opened > EAR_OPEN_TH:
                self._wink_frames += 1
            else:
                self._wink_frames = 0
            if self._wink_frames >= WINK_HOLD_FRAMES:
                self._advance()

        return self._state()

    def _state(self):
        ch = self._current()
        return {
            "status":       self.status,
            "sequence":     [a[0] for a in self.sequence],
            "current_idx":  self.current_idx,
            "total":        len(self.sequence),
            "instruction":  ch[1] if ch else "",
            "blink_count":  self.blink_count,
            "time_left":    max(0.0, CHALLENGE_WINDOW_S - (time.time() - self.challenge_start)),
        }
