import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()

print("Camera opened:", ret)
if ret:
    print("Frame shape:", frame.shape)

cap.release()
