from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from src.core.entities.cropped_face import CroppedFace


class IEmbeddingModel(ABC):
    """
    Contract for any face-embedding model (ArcFace, FaceNet, …).
    Separates the two-step inference pipeline (alignment + embedding) so
    each step can be tested or replaced independently.
    The core layer depends only on this interface; ONNX / framework-specific
    implementations live in src/app/ml/.
    """

    @abstractmethod
    def preprocess(self, cropped_face: CroppedFace) -> np.ndarray:
        # Aligns the face chip using its landmark coordinates and resizes it
        # to the model's expected input resolution.
        # Returns a float32 numpy array ready for inference.
        ...

    @abstractmethod
    def compute_embedding(self, aligned_image: np.ndarray) -> np.ndarray:
        # Runs model inference on the aligned image produced by preprocess().
        # Returns a normalised 512-dimensional float32 embedding vector.
        ...
