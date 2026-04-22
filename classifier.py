"""
classifier.py — Carga el modelo Keras y las etiquetas; expone .predict(frame).
- Preprocesa a FRAME_SIZE y normaliza a [-1,1].
- Retorna (class_label_str, confidence_float_0_1).
"""
import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model
import config

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
tf.get_logger().setLevel("ERROR")

class Classifier:
    def __init__(self):
        self.input_size = tuple(config.FRAME_SIZE)
        print("[INFO] Cargando modelo de:", config.MODEL_PATH)
        self.model = load_model(config.MODEL_PATH, compile=False)
        print("[INFO] Modelo cargado.")
        print("[INFO] Cargando labels de:", config.LABELS_PATH)
        self.class_names = self._load_labels(config.LABELS_PATH)
        print("[INFO] Labels:", self.class_names)

    def _load_labels(self, path):
        names = {}
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines()):
                label = line.strip()
                if label:
                    names[idx] = label
        if not names:
            raise RuntimeError("labels.txt está vacío o es inválido.")
        return names

    def _preprocess(self, bgr_frame):
        img = cv2.resize(bgr_frame, self.input_size, interpolation=cv2.INTER_AREA)
        arr = img.astype(np.float32)
        arr = (arr / 127.5) - 1.0
        arr = np.expand_dims(arr, axis=0)
        return arr

    def predict(self, bgr_frame):
        x = self._preprocess(bgr_frame)
        preds = self.model.predict(x, verbose=0)
        idx = int(np.argmax(preds, axis=1)[0])
        conf = float(preds[0][idx])
        label = self.class_names.get(idx, f"CLASE_{idx}")
        if config.DEBUG_PRED_PRINT:
            print(f"[PRED] {label}  conf={conf:.3f}")
        return label, conf
