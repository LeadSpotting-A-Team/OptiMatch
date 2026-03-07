import hashlib
import os
from mtcnn import MTCNN
from deepface import DeepFace
import cv2
import files_loader
import metadata as metadata_module
import config
import numpy as np
#### WE NEED TO MOVE TO [ DeepFace ]                   library for face detection and embedding
#                                     : more fast but less accurate than InsightFace


#### OR WE MOVE TO      [ insightface (FaceAnalysis) ] library for face detection and embedding
#                                     : more accurate but slower than DeepFace


#class to store the face coordinates
class Face_Coordinates:

    def __init__(self, x,y,width,height,confidence):
        self.face_x = x
        self.face_y = y
        self.face_width = width
        self.face_height = height
        self.confidence = confidence
    @staticmethod
    #form the face coordinates from the face detection result
    def from_detection_result(face_object : dict) -> 'Face_Coordinates':
        if 'box' in face_object:
            return Face_Coordinates(face_object['box'][0], face_object['box'][1], face_object['box'][2], face_object['box'][3], face_object['confidence'])
        elif 'facial_area' in face_object:
            return Face_Coordinates(face_object['facial_area']['x'], face_object['facial_area']['y'], face_object['facial_area']['w'], face_object['facial_area']['h'], face_object['confidence'])
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

#check if the face is looking forward
def is_face_look_forword(face_object : dict) -> bool:
    return True #TODO: implement the function

#check if the face is valid
def is_valid_face(face_object : dict , confidence_threshold : float = config.FACE_CONFIDENCE_THRESHOLD):


    #'facial_area' -> {'x': x, 'y': y, 'w': width, 'h': height}
    if 'facial_area' in face_object and (face_object['facial_area']['w'] < config.MIN_FACE_SIZE or face_object['facial_area']['h'] < config.MIN_FACE_SIZE):
        return False
    #'box' -> [x, y, width, height]
    if 'box' in face_object and (face_object['box'][2] < config.MIN_FACE_SIZE or face_object['box'][3] < config.MIN_FACE_SIZE):
        return False

    if not is_face_look_forword(face_object):
        return False
    return True

#get the faces coordinates from the image by the detector
#(use only if the detector is DeepFace)
def get_faces_coordinates_from_image(image , detector_backend : str) -> list[Face_Coordinates]:

    try:
        results = DeepFace.extract_faces(img_path=image, detector_backend=detector_backend, enforce_detection=False)
        faces = []
        for face in results:
            if not is_valid_face(face): continue
            fc = Face_Coordinates.from_detection_result(face)
            faces.append(fc)
        return faces
    except ValueError as e:
            return None

#get the faces coordinates from the image by the detector
#(use only if the detector is not DeepFace)
def get_faces_coordinates_from_image_by_detector(image , detector : MTCNN) -> list[Face_Coordinates]:

    try:
        results = detector.detect_faces(image)
        faces = []
        for face in results:
            if not is_valid_face(face): continue
            fc = Face_Coordinates.from_detection_result(face)
            faces.append(fc)
        return faces
    except ValueError as e:
            return None

#generate a unique face id using the media url, face index and frame index
def get_face_id(media_url : str , face_index : int , frame_index : int):
    return hashlib.sha256(media_url.encode()).hexdigest() + "_" + str(face_index) + "_" + str(frame_index)

#extract the faces from the image to list of separate images
def extract_faces_from_image(image , face_coordinates : list[Face_Coordinates]) -> list[np.ndarray]:
    faces = []
    for face_coordinate in face_coordinates:
        face_img = image[face_coordinate.get_left_upper_y():face_coordinate.get_right_lower_y(), 
                        face_coordinate.get_left_upper_x():face_coordinate.get_right_lower_x()]
        faces.append(face_img)
    return faces



#save the face images to the file and return the list of face ids
def save_face_images(faces_coordinates: list[Face_Coordinates], image, path: str, post_metadata: metadata_module.Post_Metadata, frame_index: int = 0):
    # Early return if no faces to process
    if faces_coordinates is None or len(faces_coordinates) == 0:
        return []
    # Persist post metadata to DB before saving face crops
    metadata_module.save_post_metadata(post_metadata)
    # Create output directory if it does not exist
    os.makedirs(path, exist_ok=True)
    # Extract face crops from image (reuses extract_faces_from_image to avoid duplicate slicing logic)
    face_images = extract_faces_from_image(image, faces_coordinates)
    face_ids = []
    face_index = 0
    for face_img in face_images:
        # Unique ID: hash(media_url) + face_index + frame_index
        face_id = get_face_id(post_metadata.get_media_url(), face_index, frame_index)
        file_path = f"{path}/{face_id}.jpg"

        # Save face crop as JPEG
        files_loader.save_as_image(face_img, file_path)
        # Record link between face file and post in metadata DB
        metadata_module.link_face_to_post(file_path, post_metadata.get_post_id())

        face_ids.append(face_id)
        face_index += 1

    return face_ids



