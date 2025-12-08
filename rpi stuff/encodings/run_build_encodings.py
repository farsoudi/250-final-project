import os
import glob
import numpy as np
import face_recognition

DATASET_DIR = "dataset"
OUTPUT_PATH = "encodings/face_encodings.npz"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def build_encodings():
    all_encodings = []
    all_names = []

    # Each folder = one person
    for person_name in os.listdir(DATASET_DIR):
        person_dir = os.path.join(DATASET_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue

        image_paths = glob.glob(os.path.join(person_dir, "*.*"))
        print(f"[INFO] Processing {person_name} with {len(image_paths)} images")

        for img_path in image_paths:
            try:
                image = face_recognition.load_image_file(img_path)
                # Detect + encode face(s) in the image
                encodings = face_recognition.face_encodings(image)

                if len(encodings) == 0:
                    print(f"[WARN] No face found in {img_path}, skipping.")
                    continue

                # If multiple faces, just use the first
                all_encodings.append(encodings[0])
                all_names.append(person_name)
            except Exception as e:
                print(f"[ERROR] Failed on {img_path}: {e}")

    if len(all_encodings) == 0:
        raise RuntimeError("No encodings generated. Check dataset / images.")

    all_encodings = np.array(all_encodings)
    all_names = np.array(all_names)

    np.savez(OUTPUT_PATH, encodings=all_encodings, names=all_names)
    print(f"[INFO] Saved {len(all_encodings)} encodings to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_encodings()
