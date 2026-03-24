"""
FastAPI web server — entry point for the face-search HTTP API.

Start with:
    uvicorn src.app.web.server:app --reload --host 0.0.0.0
"""
from __future__ import annotations

import base64
import logging
import os
import tempfile

import cv2
import numpy as np
import requests as http_requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from src.app import config
from src.app.db.metadata_repository import SqliteMetadataRepository
from src.app.ml.arcface_embedding import ArcFaceEmbedding
from src.app.ml.mtcnn_detector import MtcnnDetector
from src.app.vector_store.faiss_vector_store import FaissVectorStore
from src.core.services import embedding_service, harvesting_service

logging.getLogger("tensorflow").setLevel(logging.ERROR)

# ── Application setup ─────────────────────────────────────────────────────────

app = FastAPI(title="OptiMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve cropped face chip images as static files under /faces.
if config.FACES_DIR.exists():
    app.mount("/faces", StaticFiles(directory=str(config.FACES_DIR)), name="faces")

# ── Shared singletons (loaded once at startup) ────────────────────────────────

# Detector instance reuses the MTCNN loaded in config to avoid reloading weights.
_detector   = MtcnnDetector(config.DETECTOR)
_embedder   = ArcFaceEmbedding()
_vector_store = FaissVectorStore(config.INDEX_PATH, config.MAP_PATH)
_metadata_repo = SqliteMetadataRepository(config.DB_PATH)

# ── Helper functions ──────────────────────────────────────────────────────────

# Encodes a CroppedFace image to a base64 JPEG string for JSON transport.
# Returns the encoded string without the data-URI prefix.
def _encode_face_as_base64(cropped_face) -> str:
    img_bgr = cv2.cvtColor(cropped_face.get_image(), cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode(".jpg", img_bgr)
    return base64.b64encode(buffer).decode("utf-8")


# Enriches a search result dict with post metadata from the repository.
# Returns the result dict extended with platform, username, link, etc.
def _enrich_result_with_metadata(face_id: str, score: float) -> dict:
    post = _metadata_repo.get_post_by_face_id(face_id)
    result = {
        "face_id":      face_id,
        "score":        round(float(score), 4),
        "link_to_post": None,
        "platform":     None,
        "timestamp":    None,
        "media_url":    None,
        "username":     None,
    }
    if post:
        result["link_to_post"] = post.get_link_to_post()
        result["platform"]     = post.get_platform()
        result["timestamp"]    = post.get_timestamp()
        result["media_url"]    = post.get_media_url()
        result["username"]     = post.get_username()
    return result


# Core search pipeline: detects faces in the image at tmp_path, computes
# embeddings, searches the vector store, de-duplicates by best score, and
# returns the enriched result payload.
def _run_search_pipeline(tmp_path: str) -> dict:
    image = cv2.cvtColor(cv2.imread(tmp_path), cv2.COLOR_BGR2RGB)

    cropped_faces = harvesting_service.harvest_faces_from_image(
        image,
        _detector,
        config.FACE_CONFIDENCE_THRESHOLD,
        config.MIN_FACE_SIZE,
    )
    if not cropped_faces:
        return {
            "query_faces": [],
            "results": [],
            "message": "No faces detected in the image",
        }

    query_faces_b64 = [_encode_face_as_base64(cf) for cf in cropped_faces]

    # Merge results from all query faces, keeping the highest score per face_id.
    best_scores: dict[str, float] = {}
    for cropped_face in cropped_faces:
        embedding = embedding_service.compute_embedding(cropped_face, _embedder)
        if embedding is None:
            continue
        for result in _vector_store.search_nearest_faces(embedding, k=50):
            fid = result["face_id"]
            best_scores[fid] = max(best_scores.get(fid, 0.0), result["score"])

    sorted_ids = sorted(best_scores, key=lambda x: best_scores[x], reverse=True)
    enriched   = [_enrich_result_with_metadata(fid, best_scores[fid]) for fid in sorted_ids]

    return {"query_faces": query_faces_b64, "results": enriched}

# ── Routes ────────────────────────────────────────────────────────────────────

# Returns server health status and the total number of indexed faces.
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "faces": _vector_store.get_face_count()}


# Accepts a direct URL to an image, downloads it, and runs the face search pipeline.
# Returns query face thumbnails (base64) and enriched match results.
@app.post("/search/url")
async def search_by_url(url: str = Form(...)) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/*,*/*;q=0.8",
    }
    try:
        resp = http_requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        resp.raise_for_status()
        contents = resp.content
    except http_requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {exc}") from exc

    nparr = np.frombuffer(contents, np.uint8)
    if cv2.imdecode(nparr, cv2.IMREAD_COLOR) is None:
        raise HTTPException(
            status_code=400,
            detail="Could not decode image from URL. Make sure the URL points directly to an image file.",
        )

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return _run_search_pipeline(tmp_path)
    finally:
        os.unlink(tmp_path)


# Accepts a multipart image upload, validates it, and runs the face search pipeline.
# Returns query face thumbnails (base64) and enriched match results.
@app.post("/search")
async def search_by_upload(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    suffix = (file.filename or "upload").rsplit(".", 1)[-1].lower()
    suffix = f".{suffix}" if suffix in ("jpg", "jpeg", "png", "webp") else ".jpg"

    try:
        contents = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc

    nparr = np.frombuffer(contents, np.uint8)
    if cv2.imdecode(nparr, cv2.IMREAD_COLOR) is None:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return _run_search_pipeline(tmp_path)
    finally:
        os.unlink(tmp_path)
