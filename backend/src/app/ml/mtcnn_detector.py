from __future__ import annotations

import numpy as np
from mtcnn import MTCNN

from src.core.entities.detected_face import DetectedFace, FaceDetectionException
from src.core.interfaces.i_face_detector import IFaceDetector


class MtcnnDetector(IFaceDetector):
    """
    MTCNN-based implementation of IFaceDetector.

    Wraps the MTCNN library and normalises its raw output into DetectedFace
    objects understood by the core layer.  An existing MTCNN instance can be
    passed in (e.g. from config.py) so the model weights are loaded only once.
    """

    def __init__(self, detector: MTCNN | None = None) -> None:
        # Accept an externally created MTCNN instance to avoid re-loading
        # the model weights on every API request.
        self._detector = detector if detector is not None else MTCNN()

    # Runs MTCNN detection on the given RGB image and returns a list of
    # DetectedFace objects whose confidence meets or exceeds min_confidence.
    # Silently skips any raw detection result that is malformed.
    # Returns an empty list when no valid faces are found.
    def detect_faces(
        self,
        image: np.ndarray,
        min_confidence: float,
    ) -> list[DetectedFace]:
        try:
            raw_detections = self._detector.detect_faces(image)
        except Exception:
            return []

        detected_faces: list[DetectedFace] = []
        for raw in raw_detections:
            if raw.get("confidence", 0.0) < min_confidence:
                continue
            try:
                detected_faces.append(DetectedFace.from_mtcnn_result(raw))
            except FaceDetectionException:
                continue

        return detected_faces
