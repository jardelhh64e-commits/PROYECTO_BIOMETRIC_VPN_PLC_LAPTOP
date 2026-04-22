import cv2, mediapipe as mp, tensorflow as tf, google.protobuf
print("OpenCV:", cv2.__version__)
print("MediaPipe:", mp.__version__)
print("TensorFlow:", tf.__version__)
print("protobuf:", google.protobuf.__version__)

# Intenta crear FaceMesh con TF previamente importado
mp_face_mesh = mp.solutions.face_mesh
fm = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=False)
print("FaceMesh creado OK con TF importado.")
fm.close()
