import os
from deepface import DeepFace
import mtcnn
import files_loader
import config
import numpy as np

#class to store the face coordinates
#detector is a global variable that is used to detect the faces
#detector is a MTCNN object or a string (detector_backend)
class FaceDetectionException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Detected_Face:

    def __init__(self, x,y,width,height,confidence,keypoints):
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height
        self.confidence = confidence
        self.keypoints = keypoints
    @staticmethod
    #form the face coordinates from the face detection result
    def from_detection_result(face_object : dict) -> 'Detected_Face':
        try:    
            #MTCNN detection result
            if 'box' in face_object:
                keypoints = {
                            "nose": [face_object['keypoints']['nose'][0], face_object['keypoints']['nose'][1]],
                            "mouth_right": [face_object['keypoints']['mouth_right'][0], face_object['keypoints']['mouth_right'][1]],
                            "right_eye": [face_object['keypoints']['right_eye'][0], face_object['keypoints']['right_eye'][1]],
                            "left_eye": [face_object['keypoints']['left_eye'][0], face_object['keypoints']['left_eye'][1]],
                            "mouth_left": [face_object['keypoints']['mouth_left'][0], face_object['keypoints']['mouth_left'][1]]
                }
                return Detected_Face(face_object['box'][0], face_object['box'][1], face_object['box'][2], face_object['box'][3], face_object['confidence'], keypoints)
            #DeepFace detection result
            elif 'facial_area' in face_object:
                area = face_object['facial_area']
                #all the keypoints are inside the area
                keypoints = {
                    "nose": [area['nose'][0], area['nose'][1]],
                    "mouth_right": [area['mouth_right'][0], area['mouth_right'][1]],
                    "right_eye": [area['right_eye'][0], area['right_eye'][1]],
                    "left_eye": [area['left_eye'][0], area['left_eye'][1]],
                    "mouth_left": [area['mouth_left'][0], area['mouth_left'][1]]
                }
                #return the detected face
                return Detected_Face(area['x'], area['y'], area['w'], area['h'], face_object['confidence'], keypoints)
            #unsupported detector
            else:
                raise ValueError("Not a valid face detection result")
        except KeyError as e:
            raise FaceDetectionException(f"KeyError: {e} , please check the face detection result")

    #get the left upper x coordinate of the face
    def get_left_upper_x(self):
        return self.face_x
    #get the left upper y coordinate of the face
    def get_left_upper_y(self):
        return self.face_y
    #get the right lower x coordinate of the face
    def get_right_lower_x(self):
        return self.face_x + self.face_width
    #get the right lower y coordinate of the face
    def get_right_lower_y(self):
        return self.face_y + self.face_height
    def get_confidence(self):
        return self.confidence

#check if the face is looking forward
def is_face_looking_forward(face_object : dict) -> bool:
    return True #TODO: implement the function

#check if the face is valid
def is_big_enough_AND_looking_forward(face: Detected_Face):
    #check if the face is big enough
    if face.face_width < config.MIN_FACE_SIZE or face.face_height < config.MIN_FACE_SIZE:
        return False

    #check if the face is looking forward
    if not is_face_looking_forward(face):
        return False
        
    return True





#define function to extract faces_coordinates from an image by the detector [mtcnn or deepface]
def detect_faces_in_image(image , detector : mtcnn.MTCNN | str = config.DETECTOR) -> list[Detected_Face]:
    faces = []
    raw_detections = []
    
    try:
        # 1. Execute detection based on the detector type
        if isinstance(detector, mtcnn.MTCNN):
            raw_detections = detector.detect_faces(image)
        elif isinstance(detector, str):
            # DeepFace.extract_faces returns a list of dicts: [{'face':..., 'facial_area':..., 'confidence':...}]
            raw_detections = DeepFace.extract_faces(img_path=image, detector_backend=detector, enforce_detection=True)
        else:
            raise TypeError("Detector must be an MTCNN instance or a string (e.g., 'retinaface')")
        # 2. Process and normalize each detected face
        for face_data in raw_detections:
            try:
                # Normalize the raw dictionary into our unified Detected_Face object
                new_face = Detected_Face.from_detection_result(face_data)
                
                
                # Now we pass the CLEAN object to our validation function
                if not is_big_enough_AND_looking_forward(new_face):
                    continue 

                faces.append(new_face)
                
            except FaceDetectionException:
                # Skip faces that are missing critical landmarks (nose/eyes)
                continue

        return faces

    except (ValueError):
        #return an empty list on critical failure
        return []

