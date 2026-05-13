from __future__ import annotations

import cv2
import numpy as np

from .url_loader import is_image_file, is_video_file


def load_image_or_video(file_path: str) -> np.ndarray | list[np.ndarray]:
    if is_image_file(file_path):
        return load_image_as_rgb(file_path)
    elif is_video_file(file_path):
        return load_video_frames_as_rgb(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

# Loads an image from disk and returns it as an RGB numpy array.
# Raises an exception if the file cannot be read (e.g. wrong path or corrupt file).
def load_image_as_rgb(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"Failed to load image from: {image_path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# Saves an RGB numpy array to disk as a JPEG/PNG image at the given path.
# Raises an exception if the write operation fails.
def save_image(image_rgb: np.ndarray, destination_path: str) -> None:
    result = cv2.imwrite(destination_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    if not result:
        raise IOError(f"Failed to save image to: {destination_path}")


# Returns True when both dimensions of the image meet the minimum size requirement.
# Returns False when the image is too small to contain a usable face.
def is_image_large_enough(image: np.ndarray, min_size: int) -> bool:
    return image.shape[0] >= min_size and image.shape[1] >= min_size


# Reads a video file frame by frame and returns every frame as an RGB numpy array.
# Frames that cannot be decoded are represented as None to preserve frame-index alignment.
# Returns a list of (np.ndarray | None) in presentation order.
def load_video_frames_as_rgb(video_path: str) -> list[np.ndarray | None]:
    frames: list[np.ndarray | None] = []
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Failed to open video: {video_path}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                current = cap.get(cv2.CAP_PROP_POS_FRAMES)
                total   = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if current >= total:
                    break
                # Corrupted frame — keep None as a placeholder and advance.
                next_frame = int(current) + 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
                frames.append(None)
            else:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        if cap is not None:
            cap.release()
    return frames

def convert_rgb_to_bgr(image_rgb: np.ndarray) -> np.ndarray:
    """
    Efficiently converts an RGB image to BGR format.
    Ensures compatibility between RGB loaders and BGR-based detectors.
    """
    if image_rgb is None or image_rgb.size == 0:
        return image_rgb
        
    return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)