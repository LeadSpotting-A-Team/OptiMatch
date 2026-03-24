"""
Central configuration for the application layer.

All paths are resolved relative to the backend/ root directory so the server
can be started from any working directory.  Every value can be overridden by
setting the corresponding environment variable before launching the process.

Usage example:
    DATA_DIR=/mnt/storage/face-engine python -m uvicorn src.app.web.server:app
"""
from __future__ import annotations

import os
from pathlib import Path

from mtcnn import MTCNN

# ── Directory roots ───────────────────────────────────────────────────────────

# Absolute path to the backend/ directory (two levels above this file).
BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]

# Root directory for all runtime-generated data files.
# Override with the DATA_DIR environment variable for production deployments.
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", str(BACKEND_ROOT / "data")))

# ── Persistent data paths ─────────────────────────────────────────────────────

# Path to the SQLite database file that stores post and face metadata.
DB_PATH: Path = DATA_DIR / "db" / "metadata.db"

# Path to the FAISS IVF index file on disk.
INDEX_PATH: Path = DATA_DIR / "index" / "face_vault.index"

# Path to the JSON sidecar that maps internal FAISS IDs to face_id strings.
MAP_PATH: Path = DATA_DIR / "index" / "face_vault.map.json"

# Directory where cropped face image chips are saved (served as static files).
FACES_DIR: Path = DATA_DIR / "faces"

# Directory used for temporary media downloads before face extraction.
DOWNLOAD_DIR: Path = DATA_DIR / "downloads"

# ── Face detection settings ───────────────────────────────────────────────────

# Minimum detection confidence score (0.0–1.0) to accept a detected face.
FACE_CONFIDENCE_THRESHOLD: float = float(
    os.environ.get("FACE_CONFIDENCE_THRESHOLD", "0.5")
)

# Minimum side length in pixels for a face bounding box to be considered valid.
MIN_FACE_SIZE: int = int(os.environ.get("MIN_FACE_SIZE", "64"))

# Shared MTCNN detector instance — initialised once at import time to avoid
# reloading the model weights on every request.
DETECTOR: MTCNN = MTCNN()

# ── Embedding model settings ──────────────────────────────────────────────────

# Name of the active face embedding model.  Currently only "ArcFace" is supported.
EMBEDDING_MODEL_NAME: str = os.environ.get("EMBEDDING_MODEL", "ArcFace")

# ── FAISS / IVF settings ──────────────────────────────────────────────────────

# Default number of Voronoi clusters for a new IVF index.
IVF_DEFAULT_NLIST: int = 100

# Active nlist used at runtime.  Override with IVF_NLIST env var.
IVF_NLIST: int = int(os.environ.get("IVF_NLIST", str(IVF_DEFAULT_NLIST)))
