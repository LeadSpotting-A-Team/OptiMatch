from __future__ import annotations

import numpy as np

from src.core.entities.cropped_face import CroppedFace
from src.core.interfaces.i_face_detector import IFaceDetector
from src.core.services.face_detection_service import detect_and_crop_faces


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


# ── Count helper ──────────────────────────────────────────────────────────────

# Counts the total number of cropped faces across all frames in a video result.
# Accepts the list-of-lists format returned by harvest_faces_from_video.
# Returns an integer count.
def count_harvested_faces(frames_result: list[list[CroppedFace]]) -> int:
    return sum(len(frame) for frame in frames_result if frame is not None)
