"""
config.py — Panel de configuración técnico.
"""

# ===== Cámara =====
CAM_INDEX = 0
CAM_RES   = (640, 480)
USE_SELFIE_FLIP = False  # Si usas espejo y el yaw te sale invertido, cambia a True y ajusta en liveness.py

# Tamaño de entrada del modelo (ancho, alto)
FRAME_SIZE = (224, 224)

# ===== Modelo / Etiquetas (Keras) =====
MODEL_PATH  = "keras_model.h5"
LABELS_PATH = "labels.txt"

# ===== Umbrales (clasificador) =====
STABLE_CONF  = 0.90   # umbral para empezar/contar autorización estable
NOAUTH_CONF  = 0.75   # umbral para disparar NO ENTRENADA (más bajo que STABLE_CONF)

# ===== Estabilidad (Autorizado) =====
STABLE_TIME_S  = 5.0  # segundos continuos con conf >= STABLE_CONF

# ===== NO ENTRENADA (Bloqueo) =====
NOAUTH_TIME_S    = 3.0
NOAUTH_OVERLAY_S = 3.0

# ===== ENTRENADA (Overlay de éxito + pausa) =====
TRAINED_OVERLAY_S = 3.0

# ===== Logs / prints =====
PRINT_INTERVAL_S = 5
DEBUG_PRED_PRINT = False  # no imprimir debug en consola

# ===== MediaPipe FaceMesh =====
MEDIAPIPE_MAX_FACES    = 2
MEDIAPIPE_REFINE       = True   # ojos/iris más precisos
MEDIAPIPE_MIN_DET_CONF = 0.5
MEDIAPIPE_MIN_TRK_CONF = 0.7

# ===== PLC (solo conexión / verificación) =====
USE_PLC  = False
PLC_IP   = "192.168.0.10"
PLC_RACK = 0
PLC_SLOT = 1

# ===== LIVENESS (Prueba de vida) =====
USE_LIVENESS = True

# Parpadeo (EAR)
EAR_THRESHOLD   = 0.26   # sube/baja si no detecta
EAR_MIN_FRAMES  = 1      # 1 frame cerrado basta

# Giro de cabeza (desafío)
YAW_DEG_TARGET   = 6.0   # pide giro leve (6–8º)

# Ventana combinada para completar blink + yaw
# Si pones 0 o negativo, NO hay límite (engancha cuando sea).
LIVENESS_WINDOW_S = 6.0

# Mensajes UI de liveness
LIVENESS_MSG_BLINK = "Parpadea una vez"
LIVENESS_MSG_TURN  = "Gira la cabeza a la IZQUIERDA"
LIVENESS_MSG_OK    = "Prueba de vida OK"
LIVENESS_MSG_FAIL  = "Presentación sospechosa"
