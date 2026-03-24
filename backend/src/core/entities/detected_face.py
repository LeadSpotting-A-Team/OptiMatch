from __future__ import annotations


# Raised when a raw detection result is malformed or missing required keys.
class FaceDetectionException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class DetectedFace:
    """
    Represents a single face detected in an image.
    Stores bounding-box coordinates, detection confidence, and facial keypoints.
    Framework-agnostic: produced by any IFaceDetector implementation.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        confidence: float,
        keypoints: dict[str, list[int]],
    ) -> None:
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height
        self.confidence = confidence
        self.keypoints = keypoints

    # ── Coordinate helpers ────────────────────────────────────────────────────

    # Returns the left-most x coordinate of the bounding box.
    def get_left_upper_x(self) -> int:
        return self.face_x

    # Returns the top-most y coordinate of the bounding box.
    def get_left_upper_y(self) -> int:
        return self.face_y

    # Returns the right-most x coordinate of the bounding box.
    def get_right_lower_x(self) -> int:
        return self.face_x + self.face_width

    # Returns the bottom-most y coordinate of the bounding box.
    def get_right_lower_y(self) -> int:
        return self.face_y + self.face_height

    # Returns the detection confidence score (0.0 – 1.0).
    def get_confidence(self) -> float:
        return self.confidence

    # ── Factory ───────────────────────────────────────────────────────────────

    @staticmethod
    def from_mtcnn_result(face_object: dict) -> "DetectedFace":
        # Parses a raw MTCNN detection dict into a DetectedFace instance.
        # Raises FaceDetectionException if required keys are missing.
        try:
            keypoints = {
                "nose":        [face_object["keypoints"]["nose"][0],        face_object["keypoints"]["nose"][1]],
                "mouth_right": [face_object["keypoints"]["mouth_right"][0], face_object["keypoints"]["mouth_right"][1]],
                "right_eye":   [face_object["keypoints"]["right_eye"][0],   face_object["keypoints"]["right_eye"][1]],
                "left_eye":    [face_object["keypoints"]["left_eye"][0],    face_object["keypoints"]["left_eye"][1]],
                "mouth_left":  [face_object["keypoints"]["mouth_left"][0],  face_object["keypoints"]["mouth_left"][1]],
            }
            box = face_object["box"]
            return DetectedFace(box[0], box[1], box[2], box[3], face_object["confidence"], keypoints)
        except KeyError as e:
            raise FaceDetectionException(f"Missing key in MTCNN result: {e}")

    @staticmethod
    def from_deepface_result(face_object: dict) -> "DetectedFace":
        # Parses a raw DeepFace detection dict into a DetectedFace instance.
        # Raises FaceDetectionException if required keys are missing.
        try:
            area = face_object["facial_area"]
            keypoints = {
                "nose":        [area["nose"][0],        area["nose"][1]],
                "mouth_right": [area["mouth_right"][0], area["mouth_right"][1]],
                "right_eye":   [area["right_eye"][0],   area["right_eye"][1]],
                "left_eye":    [area["left_eye"][0],    area["left_eye"][1]],
                "mouth_left":  [area["mouth_left"][0],  area["mouth_left"][1]],
            }
            return DetectedFace(area["x"], area["y"], area["w"], area["h"], face_object["confidence"], keypoints)
        except KeyError as e:
            raise FaceDetectionException(f"Missing key in DeepFace result: {e}")
