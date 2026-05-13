from __future__ import annotations

import numpy as np

import src.core.io.url_loader as url_loader
from src.core.entities.cropped_face import CroppedFace
from src.core.interfaces.i_face_detector import IFaceDetector
from src.core.services.face_detection_service import detect_and_crop_faces
from src.app.config import MIN_FACE_SIZE



# ── Single-frame harvesting ───────────────────────────────────────────────────

# Detects and crops all valid faces from one RGB image frame.
# Returns a list of CroppedFace objects; returns an empty list when no faces
# pass the confidence and size thresholds.
def harvest_faces_from_frame(
    frame: np.ndarray,
    detector: IFaceDetector,
    min_confidence: float,
    min_face_size: int,
) -> list[CroppedFace]:
    return detect_and_crop_faces(frame, detector, min_confidence, min_face_size)


# ── Image file harvesting ─────────────────────────────────────────────────────

# Detects and crops all valid faces from a pre-loaded RGB image.
# Returns a list of CroppedFace objects; returns an empty list if the image
# is None or no faces are found.
def harvest_faces_from_image(
    image: np.ndarray | None,
    detector: IFaceDetector,
    min_confidence: float,
    min_face_size: int,
) -> list[CroppedFace]:
    if image is None:
        return []
    return harvest_faces_from_frame(image, detector, min_confidence, min_face_size)


# ── Video harvesting ──────────────────────────────────────────────────────────

# Detects and crops faces from every frame of a video (supplied as a list of
# RGB numpy arrays).  Frames that are None (e.g. corrupted) are represented as
# empty lists so the frame index alignment is preserved.
# Returns a list-of-lists: result[i] contains the CroppedFace objects for frame i.
def harvest_faces_from_video(
    frames: list[np.ndarray | None],
    detector: IFaceDetector,
    min_confidence: float,
    min_face_size: int,
) -> list[list[CroppedFace]]:
    return [
        harvest_faces_from_frame(frame, detector, min_confidence, min_face_size)
        if frame is not None
        else []
        for frame in frames
    ]

# Detects and crops all valid faces from a file (image or video).
# Returns a list of CroppedFace objects; returns an empty list if the file
# is None or no faces are found.
def harvest_faces_from_frames(image_or_video_frames: np.ndarray | list[np.ndarray], detector: IFaceDetector, min_face_size: int = MIN_FACE_SIZE) -> list[CroppedFace]:
    min_confidence = 0.0
    if type(image_or_video_frames) == np.ndarray:
        return harvest_faces_from_image(image_or_video_frames, detector, min_confidence, min_face_size)
    elif type(image_or_video_frames) == list[np.ndarray]:
        return harvest_faces_from_video(image_or_video_frames, detector, min_confidence, min_face_size)
    else:
        raise ValueError(f"Unsupported file type: {type(image_or_video_frames)}")



# ── Count helper ──────────────────────────────────────────────────────────────

# Counts the total number of cropped faces across all frames in a video result.
# Accepts the list-of-lists format returned by harvest_faces_from_video.
# Returns an integer count.
def count_harvested_faces(frames_result: list[list[CroppedFace]]) -> int:
    return sum(len(frame) for frame in frames_result if frame is not None)
