"""
mediapipe_face_mesh.py — FaceMeshDrawer minimal y robusto (multi-cara).
Lee parámetros desde config.py. Expone landmarks en píxeles.
"""
import cv2
import config

class FaceMeshDrawer:
    def __init__(self):
        try:
            import mediapipe as mp
        except Exception as e:
            raise RuntimeError(f"No se pudo importar mediapipe: {e}")

        self._mp = mp
        mp_face_mesh = mp.solutions.face_mesh

        self._max_faces = getattr(config, "MEDIAPIPE_MAX_FACES", 1)
        self._refine    = getattr(config, "MEDIAPIPE_REFINE", False)
        self._det_conf  = getattr(config, "MEDIAPIPE_MIN_DET_CONF", 0.5)
        self._trk_conf  = getattr(config, "MEDIAPIPE_MIN_TRK_CONF", 0.5)

        try:
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=self._max_faces,
                refine_landmarks=self._refine,
                min_detection_confidence=self._det_conf,
                min_tracking_confidence=self._trk_conf,
            )
        except Exception as e:
            raise RuntimeError(f"Fallo creando FaceMesh: {e}")

        self._drawing      = mp.solutions.drawing_utils
        self._mesh_graph   = mp_face_mesh.FACEMESH_TESSELATION
        self._spec_points  = self._drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=2)
        self._spec_edges   = self._drawing.DrawingSpec(color=(255,0,0), thickness=1, circle_radius=0)

        self._draw_box = True
        self._box_len  = 30
        self._box_thk  = 2
        self._box_col  = (0,255,255)

        self.latest_landmarks_px = None
        self.face_count = 0

    def _draw_corners_box(self, frame, xs, ys):
        try:
            h, w = frame.shape[:2]
            x_min, x_max = max(min(xs), 0), min(max(xs), w-1)
            y_min, y_max = max(min(ys), 0), min(max(ys), h-1)
            L, t, c = self._box_len, self._box_thk, self._box_col
            cv2.line(frame, (x_min, y_min), (x_min+L, y_min), c, t)
            cv2.line(frame, (x_min, y_min), (x_min, y_min+L), c, t)
            cv2.line(frame, (x_max, y_min), (x_max-L, y_min), c, t)
            cv2.line(frame, (x_max, y_min), (x_max, y_min+L), c, t)
            cv2.line(frame, (x_min, y_max), (x_min+L, y_max), c, t)
            cv2.line(frame, (x_min, y_max), (x_min, y_max-L), c, t)
            cv2.line(frame, (x_max, y_max), (x_max-L, y_max), c, t)
            cv2.line(frame, (x_max, y_max), (x_max, y_max-L), c, t)
        except Exception:
            pass

    def process(self, frame_bgr):
        """
        Procesa frame, dibuja malla(s) y actualiza latest_landmarks_px (primer rostro).
        Devuelve (landmarks_px, frame_bgr_con_dibujo).
        """
        self.latest_landmarks_px = None
        self.face_count = 0

        try:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)
        except Exception:
            return None, frame_bgr

        if not results or not results.multi_face_landmarks:
            return None, frame_bgr

        h, w = frame_bgr.shape[:2]

        for fi, face_landmarks in enumerate(results.multi_face_landmarks):
            try:
                self._drawing.draw_landmarks(
                    image=frame_bgr,
                    landmark_list=face_landmarks,
                    connections=self._mesh_graph,
                    landmark_drawing_spec=self._spec_points,
                    connection_drawing_spec=self._spec_edges,
                )
            except Exception:
                pass

            if self._draw_box:
                try:
                    xs = [int(p.x * w) for p in face_landmarks.landmark]
                    ys = [int(p.y * h) for p in face_landmarks.landmark]
                    self._draw_corners_box(frame_bgr, xs, ys)
                except Exception:
                    pass

            if fi == 0:
                try:
                    self.latest_landmarks_px = [(int(p.x * w), int(p.y * h)) for p in face_landmarks.landmark]
                except Exception:
                    self.latest_landmarks_px = None

            self.face_count += 1

        return self.latest_landmarks_px, frame_bgr

    def draw(self, frame) -> bool:
        lm, _ = self.process(frame)
        return lm is not None

    def get_latest_landmarks(self):
        return self.latest_landmarks_px

    def close(self):
        try:
            self.face_mesh.close()
        except Exception:
            pass
