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

# Check for GPU/CUDA support in dlib
def check_gpu_support():
    """Check if dlib was compiled with CUDA support."""
    try:
        import dlib
        # Try to get dlib version info
        dlib_version = dlib.DLIB_VERSION
        print(f"[INFO] dlib version: {dlib_version}")
        
        # Check if CUDA is available (dlib will use it automatically for CNN if compiled with CUDA)
        try:
            # This is a simple check - dlib doesn't expose CUDA directly in Python
            # But CNN model will use GPU automatically if dlib was compiled with CUDA
            print("[INFO] GPU support: CNN model will use GPU automatically if dlib was compiled with CUDA")
            print("[INFO] Note: HOG model is always CPU-only")
            return True
        except:
            print("[INFO] GPU support: Unknown (CNN will try to use GPU if available)")
            return False
    except ImportError:
        print("[WARN] Could not import dlib directly")
        return False

# Paths - adjust these as needed
DATASET_DIR = "dataset"  # Dataset is now in gpu stuff directory
OUTPUT_PATH = "encodings/face_encodings.npz"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def resize_image_if_large(image, max_dimension=1200):
    """
    Resize image if it's too large to speed up processing.
    Face recognition works fine on smaller images.
    """
    height, width = image.shape[:2]
    max_size = max(height, width)
    
    if max_size > max_dimension:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        # Resize using PIL for better quality
        pil_image = Image.fromarray(image)
        resized = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return np.array(resized)
    
    return image

def try_detect_face(image, model='hog'):
    """
    Try to detect and encode a face using different methods.
    
    Args:
        image: numpy array image
        model: 'hog' (faster) or 'cnn' (more accurate)
    
    Returns:
        encoding or None
    """
    # For CNN, resize large images first to speed things up
    if model == 'cnn':
        image = resize_image_if_large(image, max_dimension=1200)
    
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
    print("==========================================")
    print("Face Encodings Builder")
    print("==========================================")
    check_gpu_support()
    print("")
    
    all_encodings = []
    all_names = []

    # Each folder = one person
    if not os.path.exists(DATASET_DIR):
        print(f"[ERROR] Dataset directory not found: {DATASET_DIR}")
        print("[INFO] Please ensure the dataset directory exists or update DATASET_DIR in this script")
        return

    # Sort folder names for consistent ordering
    person_folders = sorted([d for d in os.listdir(DATASET_DIR) 
                            if os.path.isdir(os.path.join(DATASET_DIR, d))])
    
    for person_name in person_folders:
        person_dir = os.path.join(DATASET_DIR, person_name)
        
        image_paths = sorted(glob.glob(os.path.join(person_dir, "*.*")))
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
                    print(f"[INFO] {os.path.basename(img_path)}: {img_width}x{img_height} pixels", end="")
                except:
                    pass
                
                # Try HOG model first (faster)
                print(" [Trying HOG...]", end="", flush=True)
                encoding = try_detect_face(image, model='hog')
                
                # If HOG fails, try CNN model (more accurate, uses GPU if available)
                if encoding is None:
                    print(" [HOG failed, trying CNN (GPU-accelerated if available, 10-30 seconds)...]", end="", flush=True)
                    encoding = try_detect_face(image, model='cnn')
                
                if encoding is None:
                    print(f" [FAILED - No face found]")
                    continue

                # Success!
                all_encodings.append(encoding)
                all_names.append(person_name)
                person_encodings_count += 1
                print(f" [SUCCESS - encoding for '{person_name}']")
                
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
    
    # Debug: Show first few name-encoding pairs
    print(f"\n[DEBUG] First 5 encodings:")
    for i in range(min(5, len(all_names))):
        print(f"  Encoding {i}: {all_names[i]}")

if __name__ == "__main__":
    build_encodings()

