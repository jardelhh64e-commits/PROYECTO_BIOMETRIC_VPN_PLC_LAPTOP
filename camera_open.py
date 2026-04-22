"""
camera_open.py — utilitario para abrir la cámara con bajo retardo en Windows.
"""
from typing import Optional
import cv2
import config

def open_camera(index: Optional[int] = None) -> cv2.VideoCapture:
    if index is None:
        index = getattr(config, "CAM_INDEX", 0)

    print("[INFO] Usando backend DirectShow (Windows) para la cámara...")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara en índice {}".format(index))

    # Forzar resolución si se especificó
    cam_res = getattr(config, "CAM_RES", None)
    if cam_res:
        print("[INFO] Forzando resolución {}x{}...".format(cam_res[0], cam_res[1]))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cam_res[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_res[1])

    # Sugerir FPS y reducir buffer para bajar latencia
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Warm-up: descartar algunos frames iniciales
    print("[INFO] Calentando cámara...")
    for _ in range(5):
        cap.read()

    print("[INFO] Cámara lista.")
    return cap
