import cv2
import mediapipe as mp

class FaceMeshDrawer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.custom_spec = self.mp_draw.DrawingSpec(color=(255,255,255), thickness=1, circle_radius=0)
        self.highlight_spec = self.mp_draw.DrawingSpec(color=(255,255,0), thickness=1, circle_radius=1)

    def draw(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)
        if res.multi_face_landmarks:
            for fl in res.multi_face_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, fl, self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=self.highlight_spec,
                    connection_drawing_spec=self.custom_spec
                )
                # esquinas del bounding box (opcional)
                h, w, _ = frame.shape
                xs = [int(p.x * w) for p in fl.landmark]
                ys = [int(p.y * h) for p in fl.landmark]
                x_min, y_min, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
                L, t, c = 30, 3, (0,255,255)
                for (x,y,dx,dy) in [(x_min,y_min,L,0),(x_min,y_min,0,L),
                                    (x_max,y_min,-L,0),(x_max,y_min,0,L),
                                    (x_min,y_max,L,0),(x_min,y_max,0,-L),
                                    (x_max,y_max,-L,0),(x_max,y_max,0,-L)]:
                    cv2.line(frame,(x,y),(x+dx,y+dy),c,t)

    def close(self):
        self.face_mesh.close()

def open_camera(index=0):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")
    return cap
