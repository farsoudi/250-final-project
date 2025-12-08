# GPU Server Face Recognition Service

This service handles face recognition on the GPU server, receiving face images from Raspberry Pi devices and returning recognized names.

## Setup

### 1. Run the setup script (Fedora)
```bash
./setup.sh
```

This will:
- Install system dependencies
- Create a Python virtual environment
- Install Python packages (much faster on x86_64 - ~10-15 minutes vs 40-75 on RPi)

### 2. Build face encodings
```bash
source venv/bin/activate
python build_encodings.py
```

**Note:** Make sure the dataset is accessible. The script looks for `../rpi stuff/dataset` by default. You can modify `DATASET_DIR` in `build_encodings.py` if needed.

### 3. Run the service
```bash
source venv/bin/activate
python face_recognition_service.py
```

The service will run on `0.0.0.0:3005` (accessible from RPi at `76.175.119.31:3005`)

## API Endpoints

### GET /health
Health check endpoint. Returns:
```json
{
  "status": "ok",
  "encodings_loaded": true
}
```

### POST /recognize
Recognize a face from an uploaded image.

**Request (multipart/form-data):**
- `image`: Image file (JPEG/PNG)

**Request (JSON):**
```json
{
  "image": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "name": "kasra",
  "distance": 0.35,
  "confidence": 0.3
}
```

## Configuration

- `ENCODINGS_PATH`: Path to face encodings file (default: `encodings/face_encodings.npz`)
- `THRESHOLD`: Distance threshold for recognition (default: 0.5)
- Port: 3005 (hardcoded in `face_recognition_service.py`)

## Dependencies

- Flask (web server)
- OpenCV (image processing)
- face_recognition (face encoding/recognition)
- numpy (numerical operations)

All dependencies install quickly on x86_64 systems with pre-built wheels.

