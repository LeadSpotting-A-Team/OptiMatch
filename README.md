# Face Search Engine: End-to-End Facial Recognition Pipeline

A high-performance facial recognition and retrieval system designed to detect, index, and search millions of faces from raw image and video datasets in milliseconds.

---

## Project Overview

This project is an automated pipeline that transforms raw scraped data into a searchable "Digital Identity" database. It utilizes state-of-the-art computer vision models for detection and embedding, coupled with high-speed vector indexing for real-time forensic analysis.

---

## System Architecture

### Phase 1: The "Face Harvester" (Detection & Extraction)
The entry point of the pipeline, responsible for isolating facial data from noise.
- **Input:** Raw images and video frames
- **Technology:** MTCNN / MediaPipe
- **Key Features:**
  - Automatic cropping of "Face Chips"
  - Minimum quality filter: hard-coded threshold (e.g., 64×64 pixels) to discard low-resolution faces

### Phase 2: The "Digital Identity" (Embedding Generation)
Converting visual pixels into numerical biological signatures.
- **Input:** Cropped Face Chips
- **Technology:** FaceNet / ArcFace
- **Optimization:** L2 Normalization

### Phase 3: The "Brain" (Vector Indexing & Retrieval)
The core search engine designed for extreme scalability.
- **Input:** Face Embeddings
- **Technology:** FAISS (Facebook AI Similarity Search)

### Phase 4: The "Visual Investigator" (Search UI)
A specialized dashboard for analysts to perform visual queries.
- **Input:** User-uploaded query image
- **Frontend:** React.js / Tailwind CSS

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Face Detection | MTCNN, MediaPipe |
| Embeddings | FaceNet, ArcFace, DeepFace |
| CV Utilities | OpenCV |
| Vector Search | FAISS |
| Frontend | React.js, Tailwind CSS |

---

## Project Structure

```
Face-Search-Engine/
├── backend/
│   └── faces_detection.py     # Face detection logic
├── mtcnn/                     # MTCNN library (cloned separately, see setup below)
│   ├── mtcnn/                 # The actual importable package
│   ├── requirements.txt       # All Python dependencies
│   └── setup.py
├── sandbox/                   # Local scratch space (gitignored)
├── .venv/                     # Virtual environment (gitignored)
├── .gitignore
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git
- pip

---

### Step 1 — Clone the main project

```bash
git clone https://github.com/ShlomiGanon/Face-Search-Engine.git
cd Face-Search-Engine
```

---

### Step 2 — Clone the MTCNN library into the project

MTCNN is used as a local embedded dependency. Clone it into the `mtcnn/` subfolder **inside** the project root:

```bash
git clone https://github.com/ipazc/mtcnn mtcnn
```

After this step your folder should match the structure shown above.

---

### Step 3 — Create and activate a virtual environment

**Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 4 — Install all dependencies

All required packages are listed in `mtcnn/requirements.txt`:

```bash
pip install -r mtcnn/requirements.txt
```

This installs:

| Package | Version | Purpose |
|---|---|---|
| `tensorflow` | 2.20.0 | MTCNN inference backend |
| `mtcnn` | 1.0.0 | Face detection library |
| `numpy` | ≥ 1.26.0 | Numerical operations |
| `opencv-python` | latest | Image loading and processing |
| `joblib` | ≥ 1.4.2 | MTCNN internal dependency |
| `lz4` | ≥ 4.3.3 | MTCNN weight decompression |

> **Note:** TensorFlow is a large package (~330 MB). Installation may take several minutes.

---

### Step 5 — Verify the installation

```bash
python -c "from mtcnn.mtcnn import MTCNN; d = MTCNN(); print('MTCNN loaded successfully')"
```

Expected output:
```
MTCNN loaded successfully
```

---

## Usage Example

```python
import cv2
from mtcnn.mtcnn import MTCNN

detector = MTCNN()

image = cv2.imread("path/to/image.jpg")
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

faces = detector.detect_faces(image_rgb)
for face in faces:
    print(face)
    # {'box': [x, y, w, h], 'confidence': 0.99, 'keypoints': {'left_eye': ..., ...}}
```

---

## Project Status

> Work in progress. Phases 1–2 are under active development.
