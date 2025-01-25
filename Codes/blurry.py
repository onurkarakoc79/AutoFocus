import cv2
import numpy as np
def detect_focus(frame):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    focus_measure=[]
    for scale in range(1,6):
        kernel_size = scale * 5
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        laplacian=cv2.Laplacian(blurred,cv2.CV_64F)
        variance=laplacian.var()
        focus_measure.append(variance)
    max_focus_measure=max(focus_measure)
    if max_focus_measure>100:
        status="Focused"
    else:
        status="Unfocused"
    print(status,max_focus_measure)
    return status,max_focus_measure

def open_camera():
    cap=cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera açılmıyor")
        return
    while True:
        ret,frame=cap.read()
        if ret:
            status,focus_measure=detect_focus(frame)
            cv2.putText(frame, f"Focus: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera", frame)
        if cv2.waitKey(1) & 0xFF==ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


open_camera()