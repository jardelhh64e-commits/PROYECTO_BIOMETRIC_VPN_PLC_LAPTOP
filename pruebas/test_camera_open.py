import cv2

cap = cv2.VideoCapture(0)  # prueba con 0, 1 o 2
if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
else:
    print("✅ Cámara abierta, mostrando...")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("❌ No se pudo leer frame")
            break
        cv2.imshow("Test Cam", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
    cap.release()
    cv2.destroyAllWindows()
