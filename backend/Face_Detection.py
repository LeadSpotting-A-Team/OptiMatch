
import os
from deepface import DeepFace
import mtcnn
import files_loader
import config
import numpy as np

#class to store the face coordinates
#detector is a global variable that is used to detect the faces
#detector is a MTCNN object or a string (detector_backend)


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
        
        #MTCNN detection result
        if 'box' in face_object:
            return Detected_Face(face_object['box'][0], face_object['box'][1], face_object['box'][2], face_object['box'][3], face_object['confidence'])
        #DeepFace detection result
        elif 'facial_area' in face_object:
            return Detected_Face(face_object['facial_area']['x'], face_object['facial_area']['y'], face_object['facial_area']['w'], face_object['facial_area']['h'], face_object['confidence'])
        #(SUPPORTED DETECTORS: MTCNN, DeepFace)
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
def is_face_looking_forward(face_object : dict) -> bool:
    return True #TODO: implement the function

#check if the face is valid
def is_big_enough_AND_looking_forward(face_object : dict):


    #'facial_area' -> {'x': x, 'y': y, 'w': width, 'h': height}
    if 'facial_area' in face_object and (face_object['facial_area']['w'] < config.MIN_FACE_SIZE or face_object['facial_area']['h'] < config.MIN_FACE_SIZE):
        return False
    #'box' -> [x, y, width, height]
    if 'box' in face_object and (face_object['box'][2] < config.MIN_FACE_SIZE or face_object['box'][3] < config.MIN_FACE_SIZE):
        return False

    if not is_face_looking_forward(face_object):
        return False
    return True





#define function to extract faces_coordinates from an image by the detector [mtcnn or deepface]
def detect_faces_in_image(image , detector : mtcnn.MTCNN | str = config.DETECTOR) -> list[Detected_Face]:
    faces = []
    detected_faces = []
    try:
        if isinstance(detector, mtcnn.MTCNN):
            detected_faces = detector.detect_faces(image)

        elif isinstance(detector, str):
            detected_faces = DeepFace.extract_faces(img_path=image, detector_backend=detector, enforce_detection=False)
        else:
            raise TypeError("Detector is not a MTCNN or a string (detector_backend)")
        
        for face in detected_faces:
                if not is_big_enough_AND_looking_forward(face): continue
                faces.append(Detected_Face.from_detection_result(face))
        return faces
    except ValueError as e:
        #return empty list if the detection failed!
        return []

#define function to extract faces from an image by face coordinates
#return the list of face images [None if the confidence is less than the minimum confidence]
def crop_faces_from_image(image : np.ndarray , detected_faces : list[Detected_Face] , index_alignment : bool = True , min_confidence : float = 0) -> list[np.ndarray | None]:
    if detected_faces is None or len(detected_faces) == 0:
        return []
    
    faces = []
    for detected_face in detected_faces:
        if detected_face.get_confidence() < min_confidence:
            #skip the face if the confidence is less than the minimum confidence
            if not index_alignment:
                # when not preserving index alignment, skip instead of appending None
                continue 
            face_img = None
        else:
            face_img = image[detected_face.get_left_upper_y():detected_face.get_right_lower_y(), 
                        detected_face.get_left_upper_x():detected_face.get_right_lower_x()]
        faces.append(face_img)
    return faces

#define function to save the extracted faces to the custom path
def save_cropped_faces_to_path(cropped_faces : list[np.ndarray | None], file_names : list[str], path : str = config.FACES_OUTPUT_PATH):
    if len(cropped_faces) != len(file_names):
        raise ValueError("The number of cropped faces and file names must be the same")
    os.makedirs(path, exist_ok=True) #create the path if it does not exist
    for face_index in range(len(cropped_faces)):
        if cropped_faces[face_index] is None:
            continue #skip the face if the image is None [it means the confidence is less than the minimum confidence]
        #join the path (as path/file_name.jpg) and save the image
        file_path = os.path.join(path, f"{file_names[face_index]}.jpg")
        files_loader.save_as_image(cropped_faces[face_index], file_path)
    return True #return True if the faces are saved successfully

