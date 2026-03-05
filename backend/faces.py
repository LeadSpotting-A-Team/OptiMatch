import hashlib
import os
import time
from mtcnn import MTCNN
from deepface import DeepFace
import cv2
import files_loader
import metadata as metadata_module
import config
#### WE NEED TO MOVE TO [ DeepFace ]                   library for face detection and embedding
#                                     : more fast but less accurate than InsightFace


#### OR WE MOVE TO      [ insightface (FaceAnalysis) ] library for face detection and embedding
#                                     : more accurate but slower than DeepFace



class Face_Coordinates:

    def __init__(self, x,y,width,height):
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height

    def __init__(self, face_object : dict):
        if 'box' in face_object:
            self.face_x = face_object['box'][0]
            self.face_y = face_object['box'][1]
            self.face_width = face_object['box'][2]
            self.face_height = face_object['box'][3]
        elif 'facial_area' in face_object:
            self.face_x = face_object['facial_area']['x']
            self.face_y = face_object['facial_area']['y']
            self.face_width = face_object['facial_area']['w']
            self.face_height = face_object['facial_area']['h']
        else:
            raise ValueError("Not a valid face object") 



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


def is_valie_face(face_object : dict , confidence_threshold : float = config.FACE_CONFIDENCE_THRESHOLD):
    #'facial_area' -> {'x': x, 'y': y, 'w': width, 'h': height}
    if 'facial_area' in face_object and (face_object['facial_area']['w'] < config.MIN_FACE_SIZE or face_object['facial_area']['h'] < config.MIN_FACE_SIZE):
        return False
    if 'box' in face_object and (face_object['box'][2] < config.MIN_FACE_SIZE or face_object['box'][3] < config.MIN_FACE_SIZE):
        return False
    #'confidence' -> confidence value of the face detection
    if face_object.get('confidence', 0) < confidence_threshold:#get the confidence value from the face object, if not found, return 0
        return False
    if not is_face_lock_forword(face_object):
        return False
    return True

def get_faces_coordinates_from_image(image , detector_backend : str):

    try:
        results = DeepFace.extract_faces(img_path=image, detector_backend=detector_backend, enforce_detection=False)
        faces = []
        for face in results:
            if not is_valie_face(face): continue
            fc = Face_Coordinates(face)
            faces.append(fc)
        return faces
    except ValueError as e:
            return None

def get_faces_coordinates_from_image_by_detector(image , detector : MTCNN):

    try:
        results = detector.detect_faces(image)
        faces = []
        for face in results:
            if not is_valie_face(face): continue
            fc = Face_Coordinates(face)
            faces.append(fc)
        return faces
    except ValueError as e:
            return None

def get_face_id(media_url : str , face_index : int , frame_index : int):
    #generate a unique face id using the media url, face index and frame index
    return hashlib.sha256(media_url.encode()).hexdigest() + "_" + str(face_index) + "_" + str(frame_index)

    
def save_faces_to_file(faces_coordinates : list[Face_Coordinates] , image , path : str , post_metadata : metadata_module.Post_Metadata, frame_index : int = 0):
    face_index = 0
    face_ids = []
    if faces_coordinates is None or len(faces_coordinates) == 0:
        return []#if no faces are found, return an empty list of face ids
    metadata_module.save_post_metadata(post_metadata)
    os.makedirs(path, exist_ok=True)
    for face in faces_coordinates:

        face_id = get_face_id(post_metadata.get_media_url() , face_index , frame_index) #generate a unique face id using the media url, face index and frame index
        face_img = image[face.get_left_upper_y():face.get_right_lower_y(), 
                        face.get_left_upper_x():face.get_right_lower_x()]
        files_loader.save_as_image(face_img , f"{path}/{face_id}.jpg")#save the face image
        #link the face to the post
        metadata_module.link_face_to_post(f"{path}/{face_id}.jpg", post_metadata.get_post_id())
        face_ids.append(face_id)
        face_index += 1
    return face_ids



