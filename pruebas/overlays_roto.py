import cv2
from config import FONT, FONT_SCALE, FONT_THICKNESS, TEXT_COLOR

def _center_x(frame, text, font=FONT, scale=FONT_SCALE, thick=FONT_THICKNESS):
    w = frame.shape[1]
    (tw, _), _ = cv2.getTextSize(text, font, scale, thick)
    return int((w - tw)//2)

def draw_authorized(frame, name, conf):
    top = f"Ingeniero : {name}"
    bot = f"Reconocimiento Bueno: {int(conf*100)} %"
    x_top = _center_x(frame, top);  y_top = 30
    x_bot = _center_x(frame, bot);  y_bot = frame.shape[0]-10
    cv2.putText(frame, top, (x_top,y_top), FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)
    cv2.putText(frame, bot, (x_bot,y_bot), FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

def draw_unauthorized(frame, conf):
    top = "Persona No Autorizada"
    bot = f"Reconocimiento Erroneo: {int(conf*100)} %"
    x_top = _center_x(frame, top);  y_top = 30
    x_bot = _center_x(frame, bot);  y_bot = frame.shape[0]-10
    cv2.putText(frame, top, (x_top,y_top), FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)
    cv2.putText(frame, bot, (x_bot,y_bot), FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

def draw_timer(window_name, text, color=(255,255,255)):
    import numpy as np
    img = np.zeros((100, 550, 3), dtype=np.uint8)
    cv2.putText(img, text, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow(window_name, img)
