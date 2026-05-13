from __future__ import annotations
import threading
import logging
import numpy as np
from insightface.app import FaceAnalysis


from src.core.entities.detected_face import DetectedFace, FaceDetectionException
from src.core.interfaces.i_face_detector import IFaceDetector


class RetinaFaceDetector(IFaceDetector):
    """
    RetinaFace-based implementation of IFaceDetector using InsightFace.
    Standardized to work exactly like the MTCNN implementation.
    """

    def __init__(
        self, 
        face_analysis_app: FaceAnalysis | None = None,
        model_pack_name: str = 'buffalo_l',
        image_size_after_warp: int = 640
    ) -> None:
        """
        Initializes the RetinaFace detector.
        :param face_analysis_app: Existing FaceAnalysis instance to avoid re-loading weights.
        """
        if face_analysis_app is not None:
            self._detector = face_analysis_app
        else:
            # Initialize a new app with RetinaFace (detection) and ArcFace (recognition)
            self._detector = FaceAnalysis(
                name=model_pack_name, 
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self._detector.prepare(
                ctx_id=0, 
                det_size=(image_size_after_warp, image_size_after_warp)
            )
            #mutex to avoid race conditions
        self._mutex = threading.RLock()

    def detect_faces(
        self,
        image_bgr: np.ndarray,
        min_confidence: float,
    ) -> list[DetectedFace]:
        """
        Runs RetinaFace detection on a BGR image.
        Returns a list of DetectedFace objects.
        """
        if image_bgr is None or image_bgr.size == 0:
            return []
        with self._mutex: #acquire the lock
            result = self.try_detect_faces(image_bgr, min_confidence)
            return result


    def try_detect_faces(
    self,
    image_bgr: np.ndarray,
    min_confidence: float,
    ) -> list[DetectedFace] | None:
        if image_bgr is None or image_bgr.size == 0:
            return []

        if self._mutex.acquire(blocking=False):#try to acquire the lock
            try:
                    # InsightFace .get() returns a list of Face objects
                    raw_detections = self._detector.get(image_bgr)
            except Exception:
                return []

            finally:
                self._mutex.release()#release the lock
        else:
            return None

        detected_faces: list[DetectedFace] = []
        for face_obj in raw_detections:
            # Filter by detection confidence (det_score)
            if face_obj.det_score < min_confidence:
                continue
            
            try:
                # Using the factory method we built earlier
                detected_faces.append(DetectedFace.from_insightface_result(face_obj))
            except FaceDetectionException:
                continue

        return detected_faces