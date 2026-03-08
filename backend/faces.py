
import os
from mtcnn import MTCNN
from deepface import DeepFace
import files_loader
import config
import numpy as np

#class to store the face coordinates

class Detected_Face:

    def __init__(self, x,y,width,height,confidence):
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height
        self.confidence = confidence
    
    @staticmethod
    #form the face coordinates from the face detection result
    def from_detection_result(face_object : dict) -> 'Detected_Face':
        if 'box' in face_object:
            return Detected_Face(face_object['box'][0], face_object['box'][1], face_object['box'][2], face_object['box'][3], face_object['confidence'])
        elif 'facial_area' in face_object:
            return Detected_Face(face_object['facial_area']['x'], face_object['facial_area']['y'], face_object['facial_area']['w'], face_object['facial_area']['h'], face_object['confidence'])
        else:
            raise ValueError("Not a valid face detection result")

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
def is_face_look_forward(face_object : dict) -> bool:
    return True #TODO: implement the function

#check if the face is valid
def is_valid_face(face_object : dict , confidence_threshold : float = config.FACE_CONFIDENCE_THRESHOLD):


    #'facial_area' -> {'x': x, 'y': y, 'w': width, 'h': height}
    if 'facial_area' in face_object and (face_object['facial_area']['w'] < config.MIN_FACE_SIZE or face_object['facial_area']['h'] < config.MIN_FACE_SIZE):
        return False
    #'box' -> [x, y, width, height]
    if 'box' in face_object and (face_object['box'][2] < config.MIN_FACE_SIZE or face_object['box'][3] < config.MIN_FACE_SIZE):
        return False

    if not is_face_look_forward(face_object):
        return False
    return True





#define function to extract faces_coordinates from an image by the detector [mtcnn or deepface]
def extract_faces_coordinates_from_image(image , detector : MTCNN | str) -> list[Detected_Face]:
    faces = []
    detected_faces = []
    try:
        if isinstance(detector, MTCNN):
            detected_faces = detector.detect_faces(image)

        elif isinstance(detector, str):
            detected_faces = DeepFace.extract_faces(img_path=image, detector_backend=detector, enforce_detection=False)
        else:
            raise TypeError("Detector is not a MTCNN or a string (detector_backend)")
        
        for face in detected_faces:
                if not is_valid_face(face): continue
                faces.append(Detected_Face.from_detection_result(face))
        return faces
    except ValueError as e:
        #return empty list if the detection failed!
        return []

#define function to extract faces from an image by face coordinates
#return the list of face images [None if the confidence is less than the minimum confidence]
def extract_faces_from_image(image , faces_coordinates : list[Detected_Face] , index_alignment : bool = True , min_confidence : float = 0) -> list[np.ndarray | None]:
    if faces_coordinates is None or len(faces_coordinates) == 0:
        return []
    
    faces = []
    for face_coordinate in faces_coordinates:
        if face_coordinate.get_confidence() < min_confidence:
            #skip the face if the confidence is less than the minimum confidence
            if not index_alignment:
                # when not preserving index alignment, skip instead of appending None
                continue 
            face_img = None
        else:
            face_img = image[face_coordinate.get_left_upper_y():face_coordinate.get_right_lower_y(), 
                        face_coordinate.get_left_upper_x():face_coordinate.get_right_lower_x()]
        faces.append(face_img)
    return faces

#define function to save the extracted faces to the custom path
def save_faces_to_path(faces_images : list[np.ndarray | None], files_names : list[str], path : str):
    if len(faces_images) != len(files_names):
        raise ValueError("The number of faces images and files names must be the same")
    os.makedirs(path, exist_ok=True) #create the path if it does not exist
    for face_index in range(len(faces_images)):
        if faces_images[face_index] is None:
            continue #skip the face if the image is None [it means the confidence is less than the minimum confidence]
        file_path = f"{path}/{files_names[face_index]}.jpg"
        files_loader.save_as_image(faces_images[face_index], file_path)
    return True #return True if the faces are saved successfully

