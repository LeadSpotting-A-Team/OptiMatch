from abc import ABC, abstractmethod
import numpy as np
from Cropped_Face import CroppedFace 

class FaceEmbeddingModel(ABC):
    """
    Abstract Base Class for face embedding models.
    Provides a unified interface for alignment and inference.
    """
    @abstractmethod
    def preprocess(self, cropped_face: CroppedFace) -> np.ndarray:
        # 1. Get image and landmarks from cropped_face
        # 2. Perform Affine Transform (Alignment)
        # 3. Return aligned image
        pass

    @abstractmethod
    def get_embedding(self, aligned_img: np.ndarray) -> np.ndarray:
        # Run inference on the aligned image
        pass