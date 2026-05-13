# OptiMatch — Face Search Engine

Detect, index, and search faces from images and videos in milliseconds.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**

---

## Installation

```bash
# 1. Clone
git clone https://github.com/ShlomiGanon/Face-Search-Engine.git
cd Face-Search-Engine

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..
```

---

## ArcFace Model

The model weights are not included in the repository. Download `w600k_r50.onnx` from the [InsightFace model zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo), rename it to `arcface_w600k_r50.onnx`, and place it at:

```
backend/src/app/ml/models/arcface_w600k_r50.onnx
```

---

## Building the Face Index

Run once from `backend/` to ingest a dataset before searching.

```bash
cd backend

# From a folder structure (backend/sandbox/datasets/<source>/<person>/)
python -m scripts.build_index --source folders

# From a CSV file
python -m scripts.build_index --source csv --csv-path sandbox/dataset.csv
```

---

## Running

```bash
python run.py
```

Starts both servers. Open **http://localhost:5173** in your browser.

> The backend loads ML models on startup — wait 10–30 seconds for the "System Initializing" banner to disappear before searching.

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |

Press **Ctrl+C** to stop.

---

## Configuration

All settings can be overridden with environment variables:

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `backend/data/` | Root directory for runtime data |
| `FACE_CONFIDENCE_THRESHOLD` | `0.5` | Minimum detection confidence |
| `MIN_FACE_SIZE` | `64` | Minimum face size in pixels |

Full configuration: `backend/src/app/config.py`
