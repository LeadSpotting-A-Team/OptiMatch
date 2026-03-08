import os

import hashlib
from mtcnn import MTCNN
import url_loader
import config
import metadata as metadata_module
import faces as faces_module
import files_loader
import numpy as np
class ProcessException(Exception):
    def __init__(self, cause: Exception | str = ""):
        self.cause = cause
        
    #return the exception as a string with the no color and no color code
    def __str__(self) -> str:
        return self.colored_str("0")

    #color is a string of the color code, 0 is no color
    def colored_str(self , color: str = "91") -> str:
        color_begin = ""
        if(color != "0"): color_begin = f"\033[{color}m"
        color_end = ""
        if(color != "0"): color_end = f"\033[0m"
        return f"ProcessException: cause -> {color_begin}{self.cause}{color_end}"

class NotSupportedException(ProcessException):
    def __init__(self):
        super().__init__("Media type is not supported")


#generate a unique face id using the media url, face index and frame index
def get_Harvested_Face_id(media_url : str , face_index : int , frame_index : int):
    return hashlib.sha256(media_url.encode()).hexdigest() + "_" + str(face_index) + "_" + str(frame_index)


def Store_Harvested_Post(post_metadata: metadata_module.Post_Metadata, detector: MTCNN | str):
    faces_ids: list[str] = []
    try:
        frames = Harveste_URL(post_metadata.get_media_url(), detector , False)
        frame_index = 0
        for frame in frames:
            face_index = 0
            for face_image in frame:
                if face_image is not None:
                    face_id = get_Harvested_Face_id(post_metadata.get_media_url(), face_index, frame_index)
                    metadata_module.link_harvested_faces_to_post(face_id, post_metadata.get_post_id())
                    faces_ids.append(face_id)
                    face_index += 1
            frame_index += 1
        metadata_module.save_post_metadata(post_metadata)
        return faces_ids

    except ProcessException as e:
        raise e
    except Exception as e:
        raise ProcessException(e)

#Harveste a URL and return a list of frames with the faces images
def Harveste_URL(url: str, detector: MTCNN | str, index_alignment: bool = True, min_confidence: float = config.FACE_CONFIDENCE_THRESHOLD) -> list[list[np.ndarray | None]]:
    file = None
    try:
        file = url_loader.download_url_to_file(url, config.DOWNLOAD_PATH)
        if url_loader.is_an_image_file(file):
            faces_images = Harveste_Image(file, detector, index_alignment, min_confidence)
            return [faces_images]#return a list of one frame with the faces images
        elif url_loader.is_a_video_file(file):
            return Harveste_Video(file, detector, index_alignment, min_confidence)
        else:
            raise NotSupportedException()
    finally:
        if file is not None and os.path.exists(file):
            os.remove(file)


#Harveste a frame and return a list of faces images
def Harveste_Frame(frame: np.ndarray, detector: MTCNN | str, index_alignment: bool = True, min_confidence: float = config.FACE_CONFIDENCE_THRESHOLD) -> list[np.ndarray | None]:
    faces_coordinates = faces_module.extract_faces_coordinates_from_image(frame, detector)
    faces_images = faces_module.extract_faces_from_image(frame, faces_coordinates, index_alignment, min_confidence)
    return faces_images

#Harveste an image and return a list of faces images
def Harveste_Image(image_path: str, detector: MTCNN | str, index_alignment: bool = True, min_confidence: float = config.FACE_CONFIDENCE_THRESHOLD) -> list[np.ndarray | None]:
    image = files_loader.load_as_rgb(image_path)
    if not files_loader.is_valid_image(image):
        return []
    return Harveste_Frame(image, detector, index_alignment, min_confidence)

#Harveste a video and return a list of frames with the faces images
def Harveste_Video(video_path: str, detector: MTCNN | str, index_alignment: bool = True, min_confidence: float = config.FACE_CONFIDENCE_THRESHOLD) -> list[list[np.ndarray | None]]:
    result: list[list[np.ndarray | None]] = [] #list of frames, each frame is a list of faces images inside the frame
    frames = files_loader.load_video_as_rgb(video_path)
    for frame in frames:
        if frame is None or not files_loader.is_valid_image(frame):
            result.append([]) #append empty list if the frame is None
            continue
        faces_images = Harveste_Frame(frame, detector, index_alignment, min_confidence)
        result.append(faces_images)
    return result