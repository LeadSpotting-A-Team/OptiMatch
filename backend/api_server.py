"""
Visual Investigator - FastAPI server for face search.
Run: uvicorn api_server:app --reload --host 0.0.0.0
"""
import base64
import logging
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import requests as http_requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import Face_Harvester
import Digital_Identity
import IVF
import config
import metadata as metadata_module

logging.getLogger("tensorflow").setLevel(logging.ERROR)

# Resolve paths relative to project root; ensure cwd so config paths work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
INDEX_PATH = str(PROJECT_ROOT / "sandbox" / "face_vector_store.index")
MAP_PATH = str(PROJECT_ROOT / "face_vault.map.json")
FACES_DIR = PROJECT_ROOT / config.FACES_OUTPUT_PATH

app = FastAPI(title="OptiMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for face images
if FACES_DIR.exists():
    app.mount("/faces", StaticFiles(directory=str(FACES_DIR)), name="faces")

face_vector_store = IVF.FaceVectorStore(INDEX_PATH, MAP_PATH)


@app.get("/health")
def health():
    return {"status": "ok", "faces": face_vector_store.get_total_count()}


def _cropped_face_to_base64(cropped_face) -> str:
    """Encode CroppedFace image to base64 JPEG string."""
    img_rgb = cropped_face.get_image()
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode(".jpg", img_bgr)
    return base64.b64encode(buffer).decode("utf-8")


def _enrich_result(face_id: str, score: float) -> dict:
    """Add post metadata to a search result."""
    post = metadata_module.get_post_by_face_id(face_id)
    result = {
        "face_id": face_id,
        "score": round(float(score), 4),
        "link_to_post": None,
        "platform": None,
        "timestamp": None,
        "media_url": None,
    }
    if post:
        result["link_to_post"] = post.get_link_to_post()
        result["platform"] = post.get_platform()
        result["timestamp"] = post.get_timestamp()
        result["media_url"] = post.get_media_url()
    return result


def _run_pipeline(tmp_path: str, suffix: str) -> dict:
    """Shared logic: detect faces, embed, search, return enriched results."""
    cropped_faces = Face_Harvester.Harveste_Image(
        tmp_path,
        index_alignment=True,
        min_confidence=config.FACE_CONFIDENCE_THRESHOLD,
    )
    if not cropped_faces:
        return {"query_faces": [], "results": [], "message": "No faces detected in the image"}

    query_faces_b64 = [_cropped_face_to_base64(cf) for cf in cropped_faces]
    merged: dict[str, float] = {}
    for cropped_face in cropped_faces:
        embedding = Digital_Identity.get_face_embedding(cropped_face)
        if embedding is None:
            continue
        for r in face_vector_store.search_face(embedding, k=50):
            fid = r["face_id"]
            merged[fid] = max(merged.get(fid, 0), r["score"])

    sorted_ids = sorted(merged.keys(), key=lambda x: merged[x], reverse=True)
    enriched = [_enrich_result(fid, merged[fid]) for fid in sorted_ids]
    return {"query_faces": query_faces_b64, "results": enriched}


@app.post("/search/url")
async def search_by_url(url: str = Form(...)):
    """Download image from URL, run face search pipeline."""
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
    except http_requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {e}") from e

    # Try to decode — if OpenCV can't read it, it's not a valid image
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image from URL. Make sure the URL points directly to an image file.")

    suffix = ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return _run_pipeline(tmp_path, suffix)
    finally:
        os.unlink(tmp_path)


@app.post("/search")
async def search(file: UploadFile = File(...)):
    """
    Upload an image, run face detection + embedding, search the vector store.
    Returns query faces (base64) and enriched match results.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    suffix = Path(file.filename or "upload").suffix or ".jpg"
    if suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        suffix = ".jpg"

    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}") from e

    # Decode image preserving RGB
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image")
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        return _run_pipeline(tmp_path, suffix)
    finally:
        os.unlink(tmp_path)
