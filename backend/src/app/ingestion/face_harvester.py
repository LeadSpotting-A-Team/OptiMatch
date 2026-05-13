"""
Ingestion pipeline — bridges the core harvesting services with persistence.

This module is the only place in the codebase that orchestrates:
    1. Downloading / loading media (app/io)
    2. Detecting and cropping faces (core/services)
    3. Saving face chips to disk
    4. Persisting metadata to the repository (via IMetadataRepository)

The IMetadataRepository dependency is injected at call time so the pipeline
can be used with any repository implementation (SQLite, in-memory for tests …).
"""
from __future__ import annotations

import os

from src.core.io import url_loader, files_loader
from src.core.entities.post_metadata import PostMetadata
from src.core.interfaces.i_face_detector import IFaceDetector
from src.core.interfaces.i_metadata_repository import IMetadataRepository
import src.core.services.face_id_service as face_id_service
import src.core.services.harvesting_service as harvesting_service
from src.app.config import *
# Raised when media processing fails for a recoverable reason (bad URL,
# unsupported format, etc.) so callers can log and continue.
class IngestionException(Exception):
    def __init__(self, cause: Exception | str = "") -> None:
        self.cause = cause

    def __str__(self) -> str:
        return f"IngestionException: {self.cause}"

    # Returns the error message formatted with ANSI colour codes for terminal output.
    def colored_str(self, color_code: str = "91") -> str:
        return f"\033[{color_code}m{self}\033[0m"


# Raised when the media type at the URL is not an image or a video.
class UnsupportedMediaTypeException(IngestionException):
    def __init__(self) -> None:
        super().__init__("Media type is not supported (expected image or video)")


# Downloads the media at post.media_url, detects all faces in every frame,
# saves each face chip to faces_output_dir, persists the post and face
# associations to the repository, and returns a list of dicts with keys
# "face_id" and "face_image" (CroppedFace) for downstream embedding.
# Raises IngestionException on recoverable errors so callers can continue
# processing the next post without crashing.
def ingest_post(
    post: PostMetadata,
    detector: IFaceDetector,
    repository: IMetadataRepository,
    faces_output_dir: str = FACES_DIR,
    download_dir: str = DOWNLOAD_DIR,
    min_confidence: float = FACE_CONFIDENCE_THRESHOLD,
    min_face_size: int = MIN_FACE_SIZE,
) -> list[dict]:
    local_file: str | None = None
    try:
        os.makedirs(faces_output_dir, exist_ok=True)

        # Step 1 — download media to a temporary local file.
        local_file = url_loader.download_to_temp_file(
            post.get_media_url(), download_dir
        )

        # Step 2 — determine media type and load all frames.
        if url_loader.is_image_file(local_file):
            image = files_loader.load_image_as_rgb(local_file)
            frames = [image]
        elif url_loader.is_video_file(local_file):
            frames = files_loader.load_video_frames_as_rgb(local_file)
        else:
            raise UnsupportedMediaTypeException()

        # Step 3 — save the post record before linking any faces.
        repository.save_post(post)

        # Step 4 — harvest faces from every frame, save chips, link to post.
        harvested: list[dict] = []
        for frame_index, frame in enumerate(frames):
            if frame is None:
                continue
            cropped_faces = harvesting_service.harvest_faces_from_frame(
                frame, detector, min_confidence, min_face_size
            )
            for face_index, cropped_face in enumerate(cropped_faces):
                face_id = face_id_service.generate_face_id(
                    post.get_media_url(), face_index, frame_index
                )
                chip_path = os.path.join(faces_output_dir, f"{face_id}.jpg")
                files_loader.save_image(cropped_face.get_image(), chip_path)
                repository.link_face_to_post(face_id, post.get_post_id(), cropped_face)
                harvested.append({"face_id": face_id, "face_image": cropped_face})

        return harvested

    except IngestionException:
        raise
    except Exception as exc:
        raise IngestionException(exc) from exc
    finally:
        # Always remove the temporary download file.
        if local_file and os.path.exists(local_file):
            os.remove(local_file)
