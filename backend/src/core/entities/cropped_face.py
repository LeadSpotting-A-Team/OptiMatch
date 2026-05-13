from __future__ import annotations

import numpy as np


class CroppedFace:
    """
    Holds the cropped image chip of a single detected face together with its
    facial landmark coordinates (relative to the crop, not the original image).

    Used as the unit of data passed between the detection, alignment, and
    embedding stages of the pipeline.
    """

    def __init__(
        self,
        image: np.ndarray,
        landmarks: dict[str, tuple[int, int]],
    ) -> None:
        self._image = image
        self._landmarks = landmarks

    # Returns the RGB numpy array of the cropped face chip.
    def get_image(self) -> np.ndarray:
        return self._image

    # Returns the facial landmark dict with keys: left_eye, right_eye,
    # nose, mouth_left, mouth_right — all relative to the crop origin.
    def get_landmarks(self) -> dict[str, tuple[int, int]]:
        return self._landmarks
