import cv2
import numpy as np
import onnxruntime as ort
from embeddings_models.FaceEmbeddingModel import FaceEmbeddingModel
from Cropped_Face import CroppedFace

import os

ARCFACE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "arcface_w600k_r50.onnx")

class ArcFaceEmbedding(FaceEmbeddingModel):
    def __init__(self):
        # Load the ONNX model session once
        self.session = ort.InferenceSession(ARCFACE_MODEL_PATH)
        self.input_size = (112, 112)
        
        # Standard ArcFace reference points for a 112x112 image
        self.reference_landmarks = np.array([
            [38.2946, 51.6963],  # Left eye
            [73.5318, 51.5014],  # Right eye
            [56.0252, 71.7366],  # Nose
            [41.5493, 92.3655],  # Mouth left
            [70.7299, 92.2041]   # Mouth right
        ], dtype=np.float32)

    def preprocess(self, cropped_face: CroppedFace) -> np.ndarray:
        # 1. Get image and landmarks from cropped_face
        rough_crop = cropped_face.get_image()
        relative_kp = cropped_face.get_landmarks()

        # Landmarks guaranteed by Face_Detection.from_detection_result → extract_rough_crop flow
        # 2. Convert dictionary landmarks to numpy array in specific order
        src_landmarks = np.array([
            relative_kp['left_eye'],
            relative_kp['right_eye'],
            relative_kp['nose'],
            relative_kp['mouth_left'],
            relative_kp['mouth_right']
        ], dtype=np.float32)

        # 3. Calculate Affine Transform matrix
        tform = cv2.estimateAffinePartial2D(src_landmarks, self.reference_landmarks, method=cv2.LMEDS)[0]
        
        # 4. Fallback if alignment fails
        if tform is None or not np.isfinite(tform).all():
            return cv2.resize(rough_crop, self.input_size)

        # 5. Perform the actual Warp Affine (Alignment)
        aligned_img = cv2.warpAffine(rough_crop, tform, self.input_size, borderMode=cv2.BORDER_REPLICATE)
        return aligned_img

    def get_embedding(self, aligned_img: np.ndarray) -> np.ndarray:
        # 1. Data normalization: RGB [0,255] -> [-1,1]
        face_data = aligned_img.astype(np.float32)
        face_data = (face_data - 127.5) / 127.5
        
        # 2. Transpose from (H, W, C) to (C, H, W) and expand to batch (1, C, H, W)
        face_data = np.transpose(face_data, (2, 0, 1)) 
        input_blob = np.expand_dims(face_data, axis=0)

        # 3. Model Inference
        input_name = self.session.get_inputs()[0].name
        embedding = self.session.run(None, {input_name: input_blob})[0][0]

        # 4. L2 Normalization to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 1e-6:
            embedding = embedding / norm
            
        return embedding