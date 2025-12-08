import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Could not open webcam")
    exit()

print("✔ Webcam opened successfully")

ret, frame = cap.read()
if not ret:
    print("❌ Failed to grab frame")
else:
    print("Frame shape:", frame.shape)
    cv2.imwrite("webcam_test.jpg", frame)
    print("Saved frame to webcam_test.jpg")

cap.release()
