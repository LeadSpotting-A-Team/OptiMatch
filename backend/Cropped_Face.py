import numpy as np
from Face_Detection import Detected_Face


class CroppedFace:
    def __init__(self, rough_crop: np.ndarray, landmarks: dict[str, tuple[int, int]]):
        self.rough_crop = rough_crop
        self.landmarks = landmarks

    def get_image(self) -> np.ndarray:
        return self.rough_crop

    def get_landmarks(self) -> dict:
        return self.landmarks



#extract the rough crop from the image
#return the rough crop and the relative landmarks
def extract_rough_crop(image: np.ndarray, detected_face : Detected_Face, margin_percentage : float = 0.4) -> CroppedFace:
    img_h, img_w = image.shape[:2]

    # 1. calculate the margins (40% of the face size)
    margin_x = int(detected_face.face_width * margin_percentage)
    margin_y = int(detected_face.face_height * margin_percentage)
    
    # 2. calculate the crop coordinates with margin
    x1 = max(0, detected_face.face_x - margin_x)
    y1 = max(0, detected_face.face_y - margin_y)
    x2 = min(img_w, detected_face.face_x + detected_face.face_width + margin_x)
    y2 = min(img_h, detected_face.face_y + detected_face.face_height + margin_y)
    
    # 3. perform the crop (using copy to avoid holding the entire image in memory)
    rough_crop = image[y1:y2, x1:x2].copy()
    
    # 4. correct the landmarks (relative to the new crop)
    # every point (x, y) becomes: (x - x1, y - y1)
    relative_landmarks = {}
    if detected_face.keypoints:
        for point_name, coords in detected_face.keypoints.items():
            # coords are the original (x, y) in the large image
            rel_x = coords[0] - x1
            rel_y = coords[1] - y1
            relative_landmarks[point_name] = (rel_x, rel_y)
            
    return CroppedFace(rough_crop, relative_landmarks)