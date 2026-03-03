
from mtcnn import MTCNN
import cv2
import files_loader


class Face_Coordinates:

    def __init__(self, x,y,width,height):
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height

    def __init__(self, face_object : dict):
        if 'box' not in face_object:
            raise ValueError("Not a valid MTCNN face object")

        if face_object['box'][0] < 0 or face_object['box'][1] < 0:
            raise ValueError("Face coordinates are negative")

        self.face_x = face_object['box'][0]
        self.face_y = face_object['box'][1]
        self.face_width = face_object['box'][2]
        self.face_height = face_object['box'][3]

    def get_left_upper_x(self):
        return self.face_x
    def get_left_upper_y(self):
        return self.face_y
    def get_right_lower_x(self):
        return self.face_x + self.face_width
    def get_right_lower_y(self):
        return self.face_y + self.face_height

def is_face_lock_forword(face_object : dict):
    return True #TODO: implement the function


def is_valie_face(face_object : dict , confidence_threshold : float = 0.9):
    #'box' -> [x,y,width,height]
    if face_object['box'][2] < 64 or face_object['box'][3] < 64:
        return False
    #'confidence' -> confidence value of the face detection
    if face_object['confidence'] < confidence_threshold: #confidence is the confidence of the face detection
        return False
    if not is_face_lock_forword(face_object):
        return False
    return True

def get_faces_coordinates_from_image(image , detector):

    results = detector.detect_faces(image)
    faces = []
    for face in results:
        if not is_valie_face(face): continue
        fc = Face_Coordinates(face)
        faces.append(fc)
    return faces

def save_faces_to_file(faces_coordinates : list[Face_Coordinates] , image , path):
    i = 0
    for face in faces_coordinates:
        face_img = image[face.get_left_upper_y():face.get_right_lower_y(), 
                        face.get_left_upper_x():face.get_right_lower_x()]
        files_loader.save_as_image(face_img , f"{path}/face_{i}.jpg")#save the face image
        i += 1



