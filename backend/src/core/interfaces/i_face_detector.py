from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from src.core.entities.detected_face import DetectedFace


class IFaceDetector(ABC):
    """
    Contract for any face-detection backend (MTCNN, RetinaFace, DeepFace, …).
    The core layer depends only on this interface; concrete implementations
    live in src/app/ml/ and are injected at runtime.
    """

    @abstractmethod
    def detect_faces(
        self,
        image: np.ndarray,
        min_confidence: float,
    ) -> list[DetectedFace]:
        # Runs face detection on the given RGB image.
        # Filters out any detection whose confidence is below min_confidence.
        # Returns a list of DetectedFace objects; returns an empty list when
        # no faces are found rather than raising an exception.
        ...
