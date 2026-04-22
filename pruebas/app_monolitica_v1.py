import os
import tensorflow as tf
import cv2
import numpy as np
import time
from keras.models import load_model
import mediapipe as mp
import snap7
from snap7.util import set_bool

# Configuración para suprimir mensajes de TensorFlow y Keras
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.get_logger().setLevel('ERROR')  # Configuración para evitar advertencias

# Modo de depuración, cambiar a True si deseas ver la salida de depuración
debug_mode = False  

# Deshabilitar notación científica para mayor claridad
np.set_printoptions(suppress=True)

# Cargar el modelo
model = load_model("keras_Model.h5", compile=False)

# Cargar las etiquetas desde el archivo labels.txt y crear el mapeo
class_names = {}
with open("labels.txt", "r") as file:
    for idx, label in enumerate(file.readlines()):
        label = label.strip()
        class_names[idx] = label

# Crear un diccionario inverso para mapear las etiquetas originales a etiquetas internas
original_labels = {v: k for k, v in class_names.items()}

# Inicialización de MediaPipe para detección facial y malla
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

# Estilo futurista personalizado para la malla facial
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
custom_drawing_spec = mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=0)
highlight_spec = mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1, circle_radius=1)

# La cámara puede ser 0 o 1 según la cámara predeterminada de tu computadora
camera = cv2.VideoCapture(0)

# Inicializar variables para el temporizador y la detección de clases
start_time = time.time()
current_class = None
current_confidence = 0.0

# Inicializar variables para el segundo temporizador
start_time2 = time.time()
elapsed_time2 = 0

# Nombre de quien está reconociendo
recognizer_name = "INGENIERO DE AUTOMATIZACIÓN"

# Variable para controlar el cierre después de 5 segundos
close_timer = None
class_printed_time = None  # Variable para guardar el tiempo cuando se imprime la clase

# Variable para evitar impresiones repetidas
class_printed = False

# Configuración de conexión al PLC
PLC_IP = '192.168.0.10'  # Cambia esto por la IP de tu PLC
RACK = 0                # Generalmente es 0 para la mayoría de PLCs Siemens
SLOT = 1                # Generalmente es 1 para la mayoría de PLCs Siemens

# Crear instancia del cliente Snap7 y conectar al PLC
plc = snap7.client.Client()

try:
    plc.connect(PLC_IP, RACK, SLOT)
except Exception as e:
    print(f"Error al conectar con el PLC: {e}")
    exit()

# Verificar que la conexión fue exitosa
if plc.get_connected():
    print("Conexión exitosa al PLC")

# Variables para el control de visualización de texto
show_text = False  # Controla si se debe mostrar el texto
text_displayed_time = None  # Para registrar el momento cuando el texto es mostrado

while True:
    # Capturar la imagen de la cámara web
    ret, frame = camera.read()

    if not ret:
        break

    # Crear una copia para la ventana sin la malla (usada para el modelo de objetos)
    frame_no_mesh = frame.copy()

    # Convertir la imagen a RGB (Mediapipe usa RGB en lugar de BGR)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detectar los puntos de la malla facial
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Dibujar malla facial
            mp_drawing.draw_landmarks(
                frame, 
                face_landmarks, 
                mp_face_mesh.FACEMESH_TESSELATION,  
                landmark_drawing_spec=highlight_spec, 
                connection_drawing_spec=custom_drawing_spec
            )

            # Dibujar un rectángulo en las esquinas de la cara
            h, w, _ = frame.shape
            x_min = min([int(p.x * w) for p in face_landmarks.landmark])
            y_min = min([int(p.y * h) for p in face_landmarks.landmark])
            x_max = max([int(p.x * w) for p in face_landmarks.landmark])
            y_max = max([int(p.y * h) for p in face_landmarks.landmark])

            corner_length = 30  
            line_thickness = 3  
            color = (0, 255, 255)  

            # Esquinas del rectángulo
            cv2.line(frame, (x_min, y_min), (x_min + corner_length, y_min), color, line_thickness)
            cv2.line(frame, (x_min, y_min), (x_min, y_min + corner_length), color, line_thickness)
            cv2.line(frame, (x_max, y_min), (x_max - corner_length, y_min), color, line_thickness)
            cv2.line(frame, (x_max, y_min), (x_max, y_min + corner_length), color, line_thickness)
            cv2.line(frame, (x_min, y_max), (x_min + corner_length, y_max), color, line_thickness)
            cv2.line(frame, (x_min, y_max), (x_min, y_max - corner_length), color, line_thickness)
            cv2.line(frame, (x_max, y_max), (x_max - corner_length, y_max), color, line_thickness)
            cv2.line(frame, (x_max, y_max), (x_max, y_max - corner_length), color, line_thickness)

    # Redimensionar la imagen para el modelo de objetos
    image_resized = cv2.resize(frame_no_mesh, (224, 224), interpolation=cv2.INTER_AREA)
    image_array = np.asarray(image_resized, dtype=np.float32).reshape(1, 224, 224, 3)
    normalized_image_array = (image_array / 127.5) - 1

    # Hacer la predicción con el modelo de objetos
    prediction = model.predict(normalized_image_array, verbose=0)
    index = np.argmax(prediction)
    class_label = class_names[index]
    class_name = class_label
    confidence_score = prediction[0][index]

    # Temporizador para confianza >= 70%
    if class_label != current_class or confidence_score < 0.97: 
        current_class = class_label
        start_time = time.time()

    elapsed_time = int(time.time() - start_time)

    if elapsed_time >= 5 and not class_printed:
        print(f"RECONOCIMIENTO DE PERSONAL DE LA EMPRESA")
        print(f"{recognizer_name}: {class_label}")
        start_time = time.time()

        # Si la clase detectada es "Ambiente", guardar el tiempo de impresión
        if class_label == "Rafael" or class_label == "Ambiente":
            # Guardar el tiempo en el que se imprime la clase y mostrar en la cámara
            class_printed_time = time.time()
            # Marcar que la clase ya fue impresa
            class_printed = True

    # Temporizador para confianza < 50%
    if confidence_score < 0.90:
        elapsed_time2 = int(time.time() - start_time2)
        class_printed_time2 = time.time()
    else:
        start_time2 = time.time()

    # Si elapsed_time2 alcanza 10 segundos, imprimir "Persona desconocida"
    if elapsed_time2 >= 5:
        
        # Mostrar "Persona desconocida" en la cámara inmediatamente
        show_text = True  # Mostrar el texto en pantalla
        text_displayed_time = time.time()  # Registrar el momento cuando el texto es mostrado

    # Mostrar "Persona No Autorizada" si el temporizador indica que debe mostrarse
    if show_text:
        print("Imprimiendo 'Persona desconocida'")
        cv2.putText(frame, f"Persona No Autorizada", (class_text_x, class_text_y), font, font_scale, text_color, font_thickness)
        cv2.putText(frame, f"Reconocimiento Erroneo: {str(np.round(confidence_score * 100))[:-2]} %", (confidence_text_x, confidence_text_y), font, font_scale, text_color, font_thickness)

    # Escuchar las teclas del teclado
    keyboard_input = cv2.waitKey(1)

    # Si presionas la tecla 'r', eliminar el texto
    if keyboard_input == ord('r'):
        show_text = False  # Eliminar el texto

    # Dibujar los textos en la imagen (para la predicción del objeto)
    text_color = (0, 0, 255)  # Color del texto en BGR (azul, verde, rojo)
    font_scale = 0.8  # Escala del texto
    font_thickness = 2  # Grosor del texto
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Obtener tamaños de texto
    class_text_size, _ = cv2.getTextSize(f"Ingeniero : {class_name}", font, font_scale, font_thickness)
    confidence_text_size, _ = cv2.getTextSize(f"Confidence: {str(np.round(confidence_score * 100))[:-2]} %", font, font_scale, font_thickness)

    # Calcular posiciones del texto
    class_text_x = int((frame.shape[1] - class_text_size[0]) / 2)
    class_text_y = 30

    confidence_text_x = int((frame.shape[1] - confidence_text_size[0]) / 2)
    confidence_text_y = frame.shape[0] - 10

    # Dibujar los textos en la imagen 
    if class_printed_time and time.time() - class_printed_time <= 5:  # Mostrar el nombre de la clase en la cámara inmediatamente
        cv2.putText(frame, f"Ingeniero : {class_name}", (class_text_x, class_text_y), font, font_scale, text_color, font_thickness)
        cv2.putText(frame, f"Reconocimiento Bueno: {str(np.round(confidence_score * 100))[:-2]} %", (confidence_text_x, confidence_text_y), font, font_scale, text_color, font_thickness)

    #cv2.putText(frame, f"Confidence: {str(np.round(confidence_score * 100))[:-2]} %", (confidence_text_x, confidence_text_y), font, font_scale, text_color, font_thickness)

    # Mostrar la imagen en una ventana
    cv2.imshow("Webcam Image", frame)

    # Mostrar el primer temporizador
    timer_text = f"Verificando Autorizacion: {elapsed_time} s"
    timer_image = np.zeros((100, 550, 3), dtype=np.uint8)
    cv2.putText(timer_image, timer_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Timer", timer_image)

    # Mostrar el segundo temporizador
    timer_text2 = f"Verificando No Autorizado: {elapsed_time2} s"
    timer_image2 = np.zeros((100, 550, 3), dtype=np.uint8)
    cv2.putText(timer_image2, timer_text2, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Timer 2", timer_image2)

    # Comprobar si han pasado 5 segundos desde que se imprimió "Personal: Jardel"
    if class_printed_time and time.time() - class_printed_time >= 5:
        time.sleep(1)  # Esperar un segundo antes de cerrar el programa
        entrada = input("Ingresa Contraseña de seguridad: ").strip()  # Solicitar entrada del usuario

        # Validar la entrada del usuario
        if entrada == "UDEM1":
            valor_bool = True
           # Enviar señal al PLC
            DB_NUMBER = 1       # Número de la DB donde está la variable
            START_OFFSET = 0    # Byte dentro de la DB
            BIT_OFFSET = 0      # Bit específico donde está el booleano
            print(f"Proceso de Inicio de Planta")
        elif entrada == "0":
            valor_bool = False
            # Enviar señal al PLC
            DB_NUMBER = 1       # Número de la DB donde está la variable
            START_OFFSET = 0    # Byte dentro de la DB
            BIT_OFFSET = 0      # Bit específico donde está el booleano
        elif entrada == "UDEM2":
            valor_bool = True
            # Enviar señal al PLC a otro DB
            DB_NUMBER = 2       # Cambia esto por el número del nuevo DB
            START_OFFSET = 0    # Byte dentro del nuevo DB
            BIT_OFFSET = 0      # Bit específico donde está el booleano en el nuevo DB
            print(f"Proceso de Supervision de Errores")
        elif entrada == "b":
            valor_bool = False
            # Enviar señal al PLC a otro DB
            DB_NUMBER = 2       # Cambia esto por el número del nuevo DB
            START_OFFSET = 0    # Byte dentro del nuevo DB
            BIT_OFFSET = 0      # Bit específico donde está el booleano en el nuevo DB
        else:
            print("Entrada no válida. Debes ingresar UDEM, 0, a o b.")
            break  # Salir del ciclo si la entrada no es válida

        # Crear buffer para el valor booleano
        data = bytearray(1)
        set_bool(data, 0, BIT_OFFSET, valor_bool)  # Enviar el valor booleano al PLC

        # Intentar escribir en el PLC
        try:
            plc.db_write(DB_NUMBER, START_OFFSET, data)
            #print(f"Valor booleano {valor_bool} enviado al PLC en DB {DB_NUMBER}, Byte {START_OFFSET}, Bit {BIT_OFFSET}.")
        except Exception as e:
            print(f"Error al escribir en la DB: {e}")

        print("Cerrando el programa...")  # Imprime mensaje antes de cerrar
        break  # Salir del ciclo y cerrar el programa

    # Escuchar las teclas del teclado
    keyboard_input = cv2.waitKey(1)

    # Cerrar la aplicación al presionar la tecla Escape
    if keyboard_input == 27:
        break

# Desconectar del PLC
plc.disconnect()
camera.release()
cv2.destroyAllWindows()
