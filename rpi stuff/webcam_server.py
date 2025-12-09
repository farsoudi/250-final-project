#!/usr/bin/env python3
"""
RPi Webcam Server
Captures frames from the webcam and sends them to the GPU server for face recognition.
"""

import cv2
import requests
import json
import time
import sys
from threading import Thread, Event
from queue import Queue
from datetime import datetime
from urllib.parse import quote

# Configuration
GPU_SERVER_URL = "http://76.175.119.31:3005"  # Update with your GPU server IP
RECOGNITION_ENDPOINT = f"{GPU_SERVER_URL}/recognize"
HEALTH_CHECK_ENDPOINT = f"{GPU_SERVER_URL}/health"

# API Configuration
API_BASE_URL = "https://gpu.tailab42b6.ts.net"
LOGIN_EMAIL = "admin@scope.com"
LOGIN_PASSWORD = "admin123"
CHECKOFF_COOLDOWN_SECONDS = 10

# Frame capture configuration
FRAME_CAPTURE_INTERVAL = 0.5  # Capture a frame every 0.5 seconds
RECOGNITION_TIMEOUT = 10  # Timeout for recognition requests
ATTENDANCE_LOG_FILE = "attendance.log"  # File to log attendance

# Load face cascade classifier for local face detection
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Global API token
_API_TOKEN = None
_last_checkoff_time = {}


class WebcamFrameCapture:
    """Handles webcam frame capture in a separate thread."""
    
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.frame_queue = Queue(maxsize=5)
        self.stop_event = Event()
        self.cap = None
        self.thread = None
        
    def start(self):
        """Start the frame capture thread."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")
        
        print("✔ Webcam opened successfully")
        self.thread = Thread(target=self._capture_frames, daemon=True)
        self.thread.start()
    
    def _capture_frames(self):
        """Continuously capture frames from the webcam."""
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to grab frame")
                continue
            
            # Remove old frames if queue is full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
            
            self.frame_queue.put(frame)
            time.sleep(FRAME_CAPTURE_INTERVAL)
    
    def get_frame(self):
        """Get the latest captured frame."""
        try:
            return self.frame_queue.get_nowait()
        except:
            return None
    
    def stop(self):
        """Stop the frame capture thread."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        print("✔ Webcam closed")


def detect_faces(frame):
    """
    Detect faces in a frame using Haar Cascade.
    
    Args:
        frame: numpy array (BGR format from OpenCV)
    
    Returns:
        list: List of (x, y, w, h) tuples for detected faces
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # More lenient parameters for better detection on RPi
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(20, 20)
    )
    return faces


def log_attendance(name, distance, confidence):
    """
    Log face recognition to file and console.
    
    Args:
        name: Recognized person's name
        distance: Distance metric from GPU server
        confidence: Confidence percentage
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Console output
    if name != 'Unknown':
        distance_str = f"{distance:.4f}" if distance is not None else "N/A"
        print(f"✔ [{timestamp}] Recognized: {name} | Confidence: {confidence:.2%} | Distance: {distance_str}")
    else:
        distance_str = f"{distance:.4f}" if distance is not None else "N/A"
        print(f"⚠ [{timestamp}] Unknown person | Distance: {distance_str}")
    
    # Log to file
    try:
        with open(ATTENDANCE_LOG_FILE, 'a') as f:
            log_entry = {
                "timestamp": timestamp,
                "name": name,
                "distance": distance,
                "confidence": confidence
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"❌ Failed to write to log file: {e}")


def authenticate():
    """
    Log in to the API and cache the JWT token.
    POST /api/auth/login -> { token: "..." }
    """
    global _API_TOKEN

    url = f"{API_BASE_URL}/api/auth/login"
    payload = {"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}

    try:
        # Suppress SSL warnings if using self-signed cert
        resp = requests.post(url, json=payload, timeout=5, verify=False)
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

    except requests.exceptions.ConnectionError as e:
        print(f"[AUTH ERROR] Cannot connect to API server at {API_BASE_URL}: {e}")
        _API_TOKEN = None
        return None
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
    Name must be URL encoded.
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

    # URL encode the name as per API.md
    encoded_name = quote(name)
    url = f"{API_BASE_URL}/api/checkoff/{encoded_name}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        resp = requests.post(url, headers=headers, timeout=5, verify=False)

        # Retry once if token is expired
        if resp.status_code == 401:
            print("[API] Token expired, refreshing...")
            authenticate()
            if _API_TOKEN:
                headers["Authorization"] = f"Bearer {_API_TOKEN}"
                resp = requests.post(url, headers=headers, timeout=5, verify=False)

        if resp.status_code == 200:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"✔ [{timestamp}] API Checkoff called for {name}: {resp.json()}")
            _last_checkoff_time[name] = now
        else:
            print(f"[API] Checkoff failed ({resp.status_code}): {resp.text}")

    except requests.exceptions.ConnectionError as e:
        print(f"[API] Cannot connect to API server at {API_BASE_URL}: {e}")
    except Exception as e:
        print(f"[API EXCEPTION] Failed to POST {url}: {e}")


class GPUServerClient:
    """Client for communicating with the GPU server."""
    
    def __init__(self, base_url=GPU_SERVER_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check if the GPU server is running."""
        try:
            response = self.session.get(
                HEALTH_CHECK_ENDPOINT,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            print(f"✔ GPU Server health: {data}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ GPU Server health check failed: {e}")
            return False
    
    def send_frame_for_recognition(self, frame):
        """
        Send a frame to the GPU server for face recognition.
        
        Args:
            frame: numpy array (BGR format from OpenCV)
        
        Returns:
            dict: Response with 'name', 'distance', and 'confidence'
            None: If recognition failed
        """
        try:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("❌ Failed to encode frame")
                return None
            
            frame_bytes = buffer.tobytes()
            
            # Send frame to GPU server
            files = {'image': ('frame.jpg', frame_bytes, 'image/jpeg')}
            response = self.session.post(
                RECOGNITION_ENDPOINT,
                files=files,
                timeout=RECOGNITION_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            return result
        
        except requests.exceptions.Timeout:
            print("⚠ GPU server recognition timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ GPU server request failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Error during recognition: {e}")
            return None
    
    def close(self):
        """Close the session."""
        self.session.close()


def main():
    """Main function to run the webcam server."""
    print("[INFO] Starting RPi Webcam Server")
    print(f"[INFO] GPU Server URL: {GPU_SERVER_URL}")
    
    # Initialize GPU client
    gpu_client = GPUServerClient()
    
    # Check GPU server health
    print("[INFO] Checking GPU server health...")
    if not gpu_client.health_check():
        print("[ERROR] GPU server is not accessible. Please check the connection and server status.")
        return 1
    
    # Initialize webcam capture
    try:
        webcam = WebcamFrameCapture()
        webcam.start()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 1
    
    print("[INFO] Webcam server is running. Press Ctrl+C to stop.")
    print("[INFO] Capturing frames and sending to GPU server every {} seconds".format(FRAME_CAPTURE_INTERVAL))
    
    try:
        while True:
            # Get latest frame
            frame = webcam.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Detect faces locally first
            faces = detect_faces(frame)
            
            # Only send to GPU if faces detected
            if len(faces) == 0:
                time.sleep(FRAME_CAPTURE_INTERVAL)
                continue
            
            print(f"[INFO] Face detected ({len(faces)} face(s)), sending to GPU server...")
            
            # Send frame for recognition
            result = gpu_client.send_frame_for_recognition(frame)
            if result:
                name = result.get('name', 'Unknown')
                distance = result.get('distance')
                confidence = result.get('confidence')
                
                log_attendance(name, distance, confidence)
                
                # Send checkoff to API if recognized
                if name != 'Unknown':
                    send_checkoff(name)
            
            time.sleep(FRAME_CAPTURE_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        webcam.stop()
        gpu_client.close()
        print("[INFO] Webcam server stopped")


if __name__ == "__main__":
    main()
