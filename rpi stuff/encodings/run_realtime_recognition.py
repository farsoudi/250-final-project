import cv2
import numpy as np
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
import time
import requests
import base64

# API Configuration
API_BASE_URL = "https://gpu.tailab42b6.ts.net"  
LOGIN_EMAIL = "admin@scope.com"            
LOGIN_PASSWORD = "admin123"  

# GPU Server Configuration
GPU_SERVER_URL = "http://76.175.119.31:3005"

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

def recognize_face_gpu(face_image):
    """
    Send face image to GPU server for recognition.
    
    Args:
        face_image: numpy array (BGR format from OpenCV)
    
    Returns:
        tuple: (name, distance) or ("Unknown", None) on error
    """
    try:
        # Encode image to JPEG
        _, buffer = cv2.imencode('.jpg', face_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_bytes = buffer.tobytes()
        
        # Send to GPU server
        files = {'image': ('face.jpg', image_bytes, 'image/jpeg')}
        resp = requests.post(
            f"{GPU_SERVER_URL}/recognize",
            files=files,
            timeout=3  # Short timeout for real-time
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get("name", "Unknown"), data.get("distance")
        else:
            print(f"[GPU] Recognition failed ({resp.status_code}): {resp.text}")
            return "Unknown", None
    
    except requests.exceptions.Timeout:
        print("[GPU] Recognition timeout - server may be slow")
        return "Unknown", None
    except Exception as e:
        print(f"[GPU] Recognition error: {e}")
        return "Unknown", None

def check_gpu_server():
    """Check if GPU server is reachable."""
    try:
        resp = requests.get(f"{GPU_SERVER_URL}/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[GPU] Server is online. Encodings loaded: {data.get('encodings_loaded', False)}")
            return data.get('encodings_loaded', False)
        else:
            print(f"[GPU] Server responded with {resp.status_code}")
            return False
    except Exception as e:
        print(f"[GPU] Cannot reach server: {e}")
        return False

def load_yolo_face_model():
    # Download YOLOv8 face detection model from Hugging Face
    model_path = hf_hub_download(
        repo_id="arnabdhar/YOLOv8-Face-Detection",
        filename="model.pt"
    )
    model = YOLO(model_path)
    return model

def main():
    print("[INFO] Checking GPU server connection...")
    if not check_gpu_server():
        print("[WARN] GPU server not available. Continuing anyway, but recognition will fail.")
        print("[WARN] Make sure the GPU server is running at", GPU_SERVER_URL)
    
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
    recognition_count = 0

    print("[INFO] Starting face detection and recognition...")
    print("[INFO] Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame.")
            break

        frame_count += 1

        # Run YOLOv8 face detection
        # Reduced imgsz for speed on Pi
        results = yolo_model(frame, imgsz=320, verbose=False)

        # results is a list; take first item
        boxes = results[0].boxes

        # Draw + recognize
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()  # N x 4
            confidences = boxes.conf.cpu().numpy()  # N

            for (x1, y1, x2, y2), conf in zip(xyxy, confidences):
                x1 = int(max(0, x1))
                y1 = int(max(0, y1))
                x2 = int(min(frame.shape[1] - 1, x2))
                y2 = int(min(frame.shape[0] - 1, y2))

                # Crop face from frame
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                # Send to GPU server for recognition
                recognition_count += 1
                name, dist = recognize_face_gpu(face_crop)

                if name != "Unknown":
                    send_checkoff(name)

                # Draw bounding box
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

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
                    color,
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
                f"FPS: {fps:.1f} | Recognitions: {recognition_count}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("Face Recognition (GPU Server) - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Exiting.")

if __name__ == "__main__":
    main()
