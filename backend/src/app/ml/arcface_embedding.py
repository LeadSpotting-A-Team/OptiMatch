from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from src.core.entities.cropped_face import CroppedFace
from src.core.interfaces.i_embedding_model import IEmbeddingModel

# Path to the ONNX model weights, relative to this file's directory.
_MODEL_PATH: Path = Path(__file__).parent / "models" / "arcface_w600k_r50.onnx"


class ArcFaceEmbedding(IEmbeddingModel):
    """
    ArcFace R50 implementation of IEmbeddingModel using ONNX Runtime.

    Performs landmark-based affine alignment to a canonical 112 × 112 face,
    then runs the ArcFace model to produce a 512-dimensional L2-normalised
    embedding vector.
    """

    # Standard ArcFace reference landmark positions for a 112 × 112 image.
    _REFERENCE_LANDMARKS = np.array(
        [
            [38.2946, 51.6963],  # left eye
            [73.5318, 51.5014],  # right eye
            [56.0252, 71.7366],  # nose
            [41.5493, 92.3655],  # mouth left
            [70.7299, 92.2041],  # mouth right
        ],
        dtype=np.float32,
    )

    def __init__(self, model_path: str | Path = _MODEL_PATH) -> None:
        # Load the ONNX session once; inference calls are thread-safe.
        self._session = ort.InferenceSession(str(model_path))
        self._input_size = (112, 112)

    # Aligns the face chip to the canonical 112 × 112 ArcFace coordinate space
    # using an affine transform estimated from the five facial landmarks.
    # Falls back to a plain resize when landmark-based alignment fails.
    # Returns the aligned float32 RGB image array of shape (112, 112, 3).
    def preprocess(self, cropped_face: CroppedFace) -> np.ndarray:
        image = cropped_face.get_image()
        landmarks = cropped_face.get_landmarks()

        src_landmarks = np.array(
            [
                landmarks["left_eye"],
                landmarks["right_eye"],
                landmarks["nose"],
                landmarks["mouth_left"],
                landmarks["mouth_right"],
            ],
            dtype=np.float32,
        )

        transform, _ = cv2.estimateAffinePartial2D(
            src_landmarks, self._REFERENCE_LANDMARKS, method=cv2.RANSAC
        )

        if transform is None or not np.isfinite(transform).all():
            # Alignment failed — fall back to simple resize
            return cv2.resize(image, self._input_size)

        return cv2.warpAffine(image, transform, self._input_size, borderValue=0.0)

    # Runs the ArcFace ONNX model on an aligned 112 × 112 image.
    # Normalises pixel values from [0, 255] to [-1, 1] before inference.
    # Returns an L2-normalised float32 vector of dimension 512.
    def compute_embedding(self, aligned_image: np.ndarray) -> np.ndarray:
        # Normalise: RGB [0, 255] → [-1, 1]
        face_data = aligned_image.astype(np.float32)
        face_data = (face_data - 127.5) / 128.0

        # Reshape from (H, W, C) → (1, C, H, W) for ONNX input
        input_blob = np.expand_dims(np.transpose(face_data, (2, 0, 1)), axis=0)

        input_name = self._session.get_inputs()[0].name
        embedding: np.ndarray = self._session.run(None, {input_name: input_blob})[0][0]

        # L2 normalise to unit vector so inner product equals cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 1e-6:
            embedding = embedding / norm

        return embedding
