"""
ui.py — Textos visibles, colores, fuente y helpers de dibujo para overlays.
"""
import cv2

# ===== Identidad del sistema / etiquetas visibles =====
RECOGNIZER_NAME = "MECHATRONIC ENGINEER"
MSG_CONFIDENCE  = "Confidence: {pct} %"
MSG_NOTRAINED   = "PERSONA NO ENTRENADA"
MSG_PAUSED_HINT = "Sistema pausado. Presiona 'q' para reiniciar."
MSG_WAITING     = "Esperando bloqueo..."
MSG_TRAINED     = "PERSONA SI ENTRENADA"

# ===== Estilos (colores BGR y fuente) =====
COLOR_PRIMARY = (0, 0, 255)     # rojo
COLOR_ALERT   = (0, 0, 255)     # rojo
COLOR_HINT    = (0, 255, 255)   # amarillo
COLOR_SUCCESS = (0, 200, 0)     # verde

FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.8
FONT_THICK = 2

def draw_centered_text(img, text, y, color=COLOR_PRIMARY, scale=FONT_SCALE, thick=FONT_THICK):
    (tw, th), _ = cv2.getTextSize(text, FONT, scale, thick)
    x = max((img.shape[1] - tw) // 2, 0)
    cv2.putText(img, text, (x, y), FONT, scale, color, thick, lineType=cv2.LINE_AA)

def draw_name_and_confidence(img, label, conf_float):
    top_text = f"{RECOGNIZER_NAME}: {label}"
    bot_text = MSG_CONFIDENCE.format(pct=int(conf_float * 100))
    draw_centered_text(img, top_text, 30, color=COLOR_PRIMARY)
    draw_centered_text(img, bot_text, img.shape[0] - 12, color=COLOR_PRIMARY)

def draw_big_alert(img, text=MSG_NOTRAINED):
    h, w = img.shape[:2]
    scale, thick = 1.4, 3
    (tw, th), _ = cv2.getTextSize(text, FONT, scale, thick)
    x = max((w - tw) // 2, 0)
    y = max((h + th) // 2, 0)
    cv2.putText(img, text, (x+2, y+2), FONT, scale, (0,0,0), thick+2, lineType=cv2.LINE_AA)
    cv2.putText(img, text, (x, y),     FONT, scale, COLOR_ALERT, thick,   lineType=cv2.LINE_AA)

def draw_hint(img, text, y):
    draw_centered_text(img, text, y, color=COLOR_HINT)

def draw_big_success(img, text=MSG_TRAINED):
    h, w = img.shape[:2]
    scale, thick = 1.4, 3
    (tw, th), _ = cv2.getTextSize(text, FONT, scale, thick)
    x = max((w - tw) // 2, 0)
    y = max((h + th) // 2, 0)
    cv2.putText(img, text, (x+2, y+2), FONT, scale, (0,0,0), thick+2, lineType=cv2.LINE_AA)
    cv2.putText(img, text, (x, y),     FONT, scale, COLOR_SUCCESS, thick,   lineType=cv2.LINE_AA)

# ===== Liveness overlays =====
def draw_liveness_hint(img, text, y=30):
    draw_hint(img, f"Liveness: {text}", y)

def draw_liveness_status(img, blink_ok, yaw_ok, yaw_deg, y=60):
    msg = f"Blink:{'OK' if blink_ok else '...'} | Yaw:{yaw_deg:+.1f}° {'OK' if yaw_ok else '...'}"
    draw_hint(img, msg, y)

def draw_ear_debug(img, ear, thr, y=90):
    msg = f"EAR: {ear:.3f}  Thr:{thr:.2f}"
    draw_hint(img, msg, y)
