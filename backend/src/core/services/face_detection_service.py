from __future__ import annotations

import numpy as np

from src.core.entities.cropped_face import CroppedFace
from src.core.entities.detected_face import DetectedFace
from src.core.interfaces.i_face_detector import IFaceDetector


# ── Validation ────────────────────────────────────────────────────────────────

# Checks whether a detected face meets the minimum size requirement.
# Returns True only when both the width and height of the bounding box are
# at least min_size pixels; returns False otherwise.
def is_face_valid(face: DetectedFace, min_size: int) -> bool:
    return face.face_width >= min_size and face.face_height >= min_size


# ── Crop extraction ───────────────────────────────────────────────────────────

# Extracts a padded crop of a face from the full image and adjusts the
# landmark coordinates so they are relative to the top-left corner of the crop.
# margin_percentage controls how much padding (as a fraction of face size) is
# added on each side.
# Returns a CroppedFace with the chip image and adjusted landmarks.
def extract_face_crop(
    image: np.ndarray,
    detected_face: DetectedFace,
    margin_percentage: float = 0.4,
) -> CroppedFace:
    img_h, img_w = image.shape[:2]

    margin_x = int(detected_face.face_width  * margin_percentage)
    margin_y = int(detected_face.face_height * margin_percentage)

    x1 = max(0,     detected_face.face_x - margin_x)
    y1 = max(0,     detected_face.face_y - margin_y)
    x2 = min(img_w, detected_face.face_x + detected_face.face_width  + margin_x)
    y2 = min(img_h, detected_face.face_y + detected_face.face_height + margin_y)

    # copy() prevents the crop from holding a reference to the full image in memory
    chip = image[y1:y2, x1:x2].copy()

    relative_landmarks: dict[str, tuple[int, int]] = {}
    if detected_face.keypoints:
        for point_name, coords in detected_face.keypoints.items():
            relative_landmarks[point_name] = (coords[0] - x1, coords[1] - y1)

    return CroppedFace(chip, relative_landmarks)


# ── Main detection pipeline ───────────────────────────────────────────────────

# Runs face detection on an RGB image, filters out small faces, crops each
# valid face with a margin, and returns the list of CroppedFace objects.
# Returns an empty list when no valid faces are found.
def detect_and_crop_faces(
    image: np.ndarray,
    detector: IFaceDetector,
    min_confidence: float,
    min_face_size: int,
) -> list[CroppedFace]:
    detected_faces = detector.detect_faces(image, min_confidence)
    cropped_faces: list[CroppedFace] = []

    for face in detected_faces:
        if not is_face_valid(face, min_face_size):
            continue
        crop = extract_face_crop(image, face)
        cropped_faces.append(crop)

    return cropped_faces
