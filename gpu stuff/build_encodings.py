#!/usr/bin/env python3
"""
Build face encodings from dataset for GPU server
This should be run on the GPU server with the dataset
"""

import os
import glob
import numpy as np
import face_recognition
from PIL import Image

# Paths - adjust these as needed
DATASET_DIR = "dataset"  # Dataset is now in gpu stuff directory
OUTPUT_PATH = "encodings/face_encodings.npz"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def try_detect_face(image, model='hog'):
    """
    Try to detect and encode a face using different methods.
    
    Args:
        image: numpy array image
        model: 'hog' (faster) or 'cnn' (more accurate)
    
    Returns:
        encoding or None
    """
    # First try: standard method
    try:
        encodings = face_recognition.face_encodings(image, model=model)
        if len(encodings) > 0:
            return encodings[0]
    except Exception as e:
        pass
    
    # Second try: detect faces first, then encode
    try:
        face_locations = face_recognition.face_locations(image, model=model)
        if len(face_locations) > 0:
            encodings = face_recognition.face_encodings(image, face_locations, model=model)
            if len(encodings) > 0:
                return encodings[0]
    except Exception as e:
        pass
    
    return None

def build_encodings():
    all_encodings = []
    all_names = []

    # Each folder = one person
    if not os.path.exists(DATASET_DIR):
        print(f"[ERROR] Dataset directory not found: {DATASET_DIR}")
        print("[INFO] Please ensure the dataset directory exists or update DATASET_DIR in this script")
        return

    for person_name in os.listdir(DATASET_DIR):
        person_dir = os.path.join(DATASET_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue

        image_paths = glob.glob(os.path.join(person_dir, "*.*"))
        print(f"[INFO] Processing {person_name} with {len(image_paths)} images")

        person_encodings_count = 0
        
        for img_path in image_paths:
            try:
                # Load and check image
                if not os.path.exists(img_path):
                    print(f"[WARN] File not found: {img_path}")
                    continue
                
                # Try to load image
                try:
                    image = face_recognition.load_image_file(img_path)
                except Exception as e:
                    print(f"[ERROR] Failed to load image {img_path}: {e}")
                    continue
                
                # Get image info
                try:
                    img = Image.open(img_path)
                    img_width, img_height = img.size
                    print(f"[DEBUG] {os.path.basename(img_path)}: {img_width}x{img_height} pixels")
                except:
                    pass
                
                # Try HOG model first (faster)
                encoding = try_detect_face(image, model='hog')
                
                # If HOG fails, try CNN model (more accurate but slower)
                if encoding is None:
                    print(f"[DEBUG] HOG failed for {os.path.basename(img_path)}, trying CNN...")
                    encoding = try_detect_face(image, model='cnn')
                
                if encoding is None:
                    print(f"[WARN] No face found in {img_path} (tried both HOG and CNN), skipping.")
                    continue

                # Success!
                all_encodings.append(encoding)
                all_names.append(person_name)
                person_encodings_count += 1
                print(f"[OK] Found face in {os.path.basename(img_path)}")
                
            except Exception as e:
                print(f"[ERROR] Failed on {img_path}: {e}")
                import traceback
                traceback.print_exc()

        print(f"[INFO] Generated {person_encodings_count} encodings for {person_name}")
        print("")

    if len(all_encodings) == 0:
        print("\n[ERROR] No encodings generated!")
        print("[TROUBLESHOOTING]")
        print("  - Check that images contain clear, front-facing faces")
        print("  - Ensure images are valid (JPEG, PNG, etc.)")
        print("  - Try images with better lighting and higher resolution")
        print("  - Make sure faces are clearly visible and not too small")
        raise RuntimeError("No encodings generated. Check dataset / images.")

    all_encodings = np.array(all_encodings)
    all_names = np.array(all_names)

    np.savez(OUTPUT_PATH, encodings=all_encodings, names=all_names)
    print(f"[SUCCESS] Saved {len(all_encodings)} encodings to {OUTPUT_PATH}")
    print(f"[INFO] Encodings per person:")
    unique_names, counts = np.unique(all_names, return_counts=True)
    for name, count in zip(unique_names, counts):
        print(f"  - {name}: {count} encodings")

if __name__ == "__main__":
    build_encodings()

