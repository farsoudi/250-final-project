import cv2
import numpy as np
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
import face_recognition
import time
import os
import requests
import time

API_BASE_URL = "https://gpu.tailab42b6.ts.net"  
LOGIN_EMAIL = "admin@scope.com"            
LOGIN_PASSWORD = "admin123"  

CHECKOFF_COOLDOWN_SECONDS = 10
_last_checkoff_time = {}

_API_TOKEN = None


def authenticate():
    """
    Log in to the API and cache the JWT token.
    POST /api/auth/login -> { token: "..." }
    """
    global _API_TOKEN

    url = f"{API_BASE_URL}/api/auth/login"
    payload = {"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}

    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            print(f"[AUTH ERROR] {resp.status_code}: {resp.text}")
            _API_TOKEN = None
            return None

        data = resp.json()
        token = data.get("token")
        if not token:
            print("[AUTH ERROR] Login succeeded but no token found:", data)
            _API_TOKEN = None
            return None

        _API_TOKEN = token
        print("[AUTH] Logged in successfully.")
        return _API_TOKEN

    except Exception as e:
        print(f"[AUTH EXCEPTION] {e}")
        _API_TOKEN = None
        return None


def get_token():
    """Return cached token or authenticate if missing."""
    global _API_TOKEN
    if _API_TOKEN:
        return _API_TOKEN
    return authenticate()

def send_checkoff(name: str):
    """
    POST /api/checkoff/{name} with JWT auth.
    Applies cooldown per name to prevent API spam.
    Automatically refreshes JWT token if expired (401).
    """
    if not name or name == "Unknown":
        return

    now = time.time()
    last_time = _last_checkoff_time.get(name, 0)

    if now - last_time < CHECKOFF_COOLDOWN_SECONDS:
        return  # cooldown active

    token = get_token()
    if not token:
        print("[API] No token available; cannot send checkoff.")
        return

    url = f"{API_BASE_URL}/api/checkoff/{name}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        resp = requests.post(url, headers=headers, timeout=5)

        # Retry once if token is expired
        if resp.status_code == 401:
            print("[API] Token expired, refreshing...")
            authenticate()
            if _API_TOKEN:
                headers["Authorization"] = f"Bearer {_API_TOKEN}"
                resp = requests.post(url, headers=headers, timeout=5)

        if resp.status_code == 200:
            print(f"[API] Checkoff OK for {name}: {resp.json()}")
            _last_checkoff_time[name] = now
        else:
            print(f"[API] Checkoff failed ({resp.status_code}): {resp.text}")

    except Exception as e:
        print(f"[API EXCEPTION] Failed to POST {url}: {e}")

ENCODINGS_PATH = "encodings/face_encodings.npz"
THRESHOLD = 0.5  # distance threshold for "same person" – tune as needed

def load_encodings(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run run_build_encodings.py first to create it."
        )
    data = np.load(path, allow_pickle=True)
    return data["encodings"], data["names"]

def load_yolo_face_model():
    # Download YOLOv8 face detection model from Hugging Face
    # per the example in the model card. :contentReference[oaicite:2]{index=2}
    model_path = hf_hub_download(
        repo_id="arnabdhar/YOLOv8-Face-Detection",
        filename="model.pt"
    )
    model = YOLO(model_path)
    return model

def recognize_face(face_image, known_encodings, known_names):
    """
    face_image: BGR (from OpenCV), cropped to the face region.
    Returns: best_name, best_distance
    """
    # Convert BGR -> RGB for face_recognition
    rgb_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

    encodings = face_recognition.face_encodings(rgb_face)
    if len(encodings) == 0:
        return "Unknown", None

    face_enc = encodings[0]
    # Compute L2 distance to all known encodings
    distances = np.linalg.norm(known_encodings - face_enc, axis=1)
    best_idx = np.argmin(distances)
    best_distance = distances[best_idx]

    if best_distance < THRESHOLD:
        return known_names[best_idx], float(best_distance)
    else:
        return "Unknown", float(best_distance)

def main():
    print("[INFO] Loading face encodings...")
    known_encodings, known_names = load_encodings(ENCODINGS_PATH)

    print("[INFO] Loading YOLOv8 face detection model...")
    yolo_model = load_yolo_face_model()

    print("[INFO] Opening webcam...")
    cap = cv2.VideoCapture(0)  # USB cam on Pi = /dev/video0

    # Try to set a smaller resolution for speed on Pi
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    fps_time = time.time()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame.")
            break

        frame_count += 1

        # Run YOLOv8 face detection
        # imgsz can be reduced (e.g. 320) for speed
        results = yolo_model(frame, imgsz=480, verbose=False)

        # results is a list; take first item
        boxes = results[0].boxes

        # Draw + recognize
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()  # N x 4
            confidences = boxes.conf.cpu().numpy()  # N
            # classes = boxes.cls.cpu().numpy()  # Not needed; it's all "face"

            for (x1, y1, x2, y2), conf in zip(xyxy, confidences):
                x1 = int(max(0, x1))
                y1 = int(max(0, y1))
                x2 = int(min(frame.shape[1] - 1, x2))
                y2 = int(min(frame.shape[0] - 1, y2))

                # Crop face from frame
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                name, dist = recognize_face(face_crop, known_encodings, known_names)

                if name != "Unknown":
                    send_checkoff(name)

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                label = f"{name}"
                if dist is not None:
                    label += f" ({dist:.2f})"
                label += f" conf:{conf:.2f}"

                # Put label above box
                cv2.putText(
                    frame,
                    label,
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

        # Simple FPS display
        if frame_count >= 10:
            now = time.time()
            fps = frame_count / (now - fps_time)
            fps_time = now
            frame_count = 0
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("YOLOv8 Face Recognition (Press q to quit)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Exiting.")

if __name__ == "__main__":
    main()
