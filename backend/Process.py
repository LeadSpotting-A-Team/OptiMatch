import os

from mtcnn import MTCNN
import url_loader
import config
import metadata as metadata_module
import faces as faces_module
import files_loader
class ProcessException(Exception):
    def __init__(self, post_id: str = "", cause: Exception | None = None):
        self.post_id = post_id
        self.cause = cause
    def __str__(self):
        return f"ProcessException: post_id: {self.post_id} , cause: {self.cause}"


class NotSupportedException(ProcessException):
    def __init__(self, post_id: str = ""):
        super().__init__(post_id , ValueError("Media is not supported"))




#process the post
#post_metadata: the metadata of the post
#detector: the detector to use for face detection
#(detector can be a MTCNN object or a string (detector_backend))
#return: the list of face ids
def process_post(post_metadata: metadata_module.Post_Metadata, detector: MTCNN | str):
    file = None
    try:
        file = url_loader.download_url_to_file(post_metadata.get_media_url(), config.DOWNLOAD_PATH)
        if url_loader.is_an_image_file(file):
            return _process_image(post_metadata, file, detector)
        elif url_loader.is_a_video_file(file):
            return _process_video(post_metadata, file, detector)
        else:
            raise NotSupportedException(post_id=post_metadata.get_post_id())
    except ProcessException:
        #if the exception is a ProcessException, raise it
        raise
    except Exception as e:
        #raise a ProcessException with the post id and the exception
        raise ProcessException(post_id=post_metadata.get_post_id(), cause=e)
    finally:
        #remove the file if it exists
        if file is not None and os.path.exists(file):
            os.remove(file)



#process the image
def _process_image(post_metadata, file_path, detector: MTCNN | str):
    image = files_loader.load_as_rgb(file_path)
    faces_coords = []
    if isinstance(detector, MTCNN):
        faces_coords = faces_module.get_faces_coordinates_from_image_by_detector(image, detector)
    elif isinstance(detector, str):
        faces_coords = faces_module.get_faces_coordinates_from_image(image, detector)
    else:
        raise ValueError("Detector is not a MTCNN or a string (detector_backend)")
    if faces_coords is None or len(faces_coords) == 0:
        return []
    face_ids = faces_module.save_face_images(faces_coords, image, config.FACES_OUTPUT_PATH, post_metadata)
    post_metadata.set_max_faces_per_frame(len(faces_coords))
    post_metadata.add_frame_count(1)
    metadata_module.save_post_metadata(post_metadata)
    return face_ids


#process the video
def _process_video(post_metadata, file_path, detector: MTCNN | str):
    video_frames = files_loader.load_video_as_rgb(file_path)
    face_ids = []
    frame_index = 0
    for frame in video_frames:
        post_metadata.add_frame_count(1)
        if frame is not None and files_loader.is_valid_image(frame):
            faces_coords = []
            if isinstance(detector, MTCNN):
                faces_coords = faces_module.get_faces_coordinates_from_image_by_detector(frame, detector)
            elif isinstance(detector, str):
                faces_coords = faces_module.get_faces_coordinates_from_image(frame, detector)
            else:
                raise ValueError("Detector is not a MTCNN or a string (detector_backend)")
            if faces_coords is None or len(faces_coords) == 0:
                continue  # frame_index לא מתקדם - כמו בקוד המקורי
            post_metadata.set_max_faces_per_frame(len(faces_coords))
            faces_id_of_frame = faces_module.save_face_images(
                faces_coords, frame, config.FACES_OUTPUT_PATH, post_metadata, frame_index
            )
            face_ids.extend(faces_id_of_frame)
        frame_index += 1
    metadata_module.save_post_metadata(post_metadata)
    return face_ids