#!/usr/bin/env python3
"""
Face Recognition Service for GPU Server
Receives face images from RPi, performs recognition, and returns name
"""

from flask import Flask, request, jsonify
import cv2
import numpy as np
import face_recognition
import os
import time
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)

# Configuration
ENCODINGS_PATH = "encodings/face_encodings.npz"
THRESHOLD = 0.8  # distance threshold for "same person" (higher = more lenient)
# With limited encodings (2-4 per person), need higher threshold
# Your distances are ~0.77, so 0.8 threshold should work
# Typical: 0.6-0.65 (many encodings), 0.7-0.8 (few encodings), 0.5 (strict)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB max

# Global variables
known_encodings = None
known_names = None

def load_encodings(path):
    """Load face encodings from file."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run build_encodings.py first to create it."
        )
    data = np.load(path, allow_pickle=True)
    return data["encodings"], data["names"]

def recognize_face(face_image):
    """
    Recognize a face from an image.
    
    Args:
        face_image: numpy array (BGR format from OpenCV)
    
    Returns:
        tuple: (name, distance) or ("Unknown", distance)
    """
    global known_encodings, known_names
    
    if known_encodings is None or known_names is None:
        raise RuntimeError("Encodings not loaded. Call load_encodings() first.")
    
    # Convert BGR -> RGB for face_recognition
    rgb_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    
    # Get face encodings
    encodings = face_recognition.face_encodings(rgb_face)
    if len(encodings) == 0:
        return "Unknown", None
    
    face_enc = encodings[0]
    
    # Compute L2 distance to all known encodings
    distances = np.linalg.norm(known_encodings - face_enc, axis=1)
    
    # For better accuracy with limited encodings, find best match per person
    # then use the best overall match
    unique_names = np.unique(known_names)
    best_person_distance = {}
    
    for name in unique_names:
        # Get all encodings for this person
        person_mask = known_names == name
        person_distances = distances[person_mask]
        # Use minimum distance (best match) for this person
        best_person_distance[name] = np.min(person_distances)
    
    # Find the person with the best (lowest) distance
    best_person = min(best_person_distance, key=best_person_distance.get)
    best_distance = best_person_distance[best_person]
    
    if best_distance < THRESHOLD:
        return best_person, float(best_distance)
    else:
        return "Unknown", float(best_distance)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "encodings_loaded": known_encodings is not None
    })

@app.route('/recognize', methods=['POST'])
def recognize():
    """
    Recognize face from uploaded image.
    
    Expected: multipart/form-data with 'image' field
    OR JSON with 'image' field containing base64 encoded image
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] POST /recognize - Processing recognition request...")
    
    try:
        # Handle multipart form data (image file)
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "No image provided"}), 400
            
            # Read image from file
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if face_image is None:
                return jsonify({"error": "Invalid image format"}), 400
        
        # Handle JSON with base64 image
        elif 'image' in request.json:
            image_data = request.json['image']
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            face_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if face_image is None:
                return jsonify({"error": "Invalid image format"}), 400
        
        else:
            return jsonify({"error": "No image provided. Use 'image' field in form data or JSON."}), 400
        
        # Perform recognition
        name, distance = recognize_face(face_image)
        
        # Log the recognition result
        if distance is not None:
            print(f"[RECOGNIZE] Name: {name}, Distance: {distance:.4f}, Threshold: {THRESHOLD}")
        else:
            print(f"[RECOGNIZE] Name: {name}, No face detected in image")
        
        response = {
            "name": name,
            "distance": distance,
            "confidence": 1.0 - min(distance / THRESHOLD, 1.0) if distance is not None else None
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    """Initialize and run the service."""
    global known_encodings, known_names
    
    print("[INFO] Loading face encodings...")
    try:
        known_encodings, known_names = load_encodings(ENCODINGS_PATH)
        print(f"[INFO] Loaded {len(known_encodings)} face encodings")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("[ERROR] Please run build_encodings.py first to create encodings.")
        return
    
    print("[INFO] Starting face recognition service on 0.0.0.0:3005")
    print("[INFO] Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /recognize - Recognize face from image")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=3005, debug=False)

if __name__ == "__main__":
    main()

