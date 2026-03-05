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


#process a post by downloading the media, detecting faces and saving the faces to the file
#return a list of face ids
def process_post(post_metadata: metadata_module.Post_Metadata , detector: MTCNN):
    file = None
    try:
        file = url_loader.download_url_to_file(post_metadata.get_media_url(), config.DOWNLOAD_PATH)
        if url_loader.is_an_image_file(file):
            image = files_loader.load_as_rgb(file)
            face_ids = []
            faces_coords = faces_module.get_faces_coordinates_from_image_by_detector(image, detector)
            if faces_coords is None or len(faces_coords) == 0:
                return []#if no faces are found, return an empty list of face ids
            face_ids = faces_module.save_faces_to_file(faces_coords, image, config.FACES_OUTPUT_PATH, post_metadata)
            post_metadata.set_max_faces_per_frame(len(faces_coords))
            post_metadata.add_frame_count(1)#add 1 to the frame count because we processed one frame
            metadata_module.save_post_metadata(post_metadata)
            return face_ids
        elif url_loader.is_a_video_file(file):
            video_frames = files_loader.load_video_as_rgb(file)
            face_ids = []
            frame_index = 0
            for frame in video_frames:
                post_metadata.add_frame_count(1)#add 1 to the frame count
                if frame is not None and files_loader.is_valid_image(frame):
                    faces_coords = faces_module.get_faces_coordinates_from_image_by_detector(frame, detector)
                    if faces_coords is None or len(faces_coords) == 0:
                        continue #if no faces are found, continue to the next frame
                    post_metadata.set_max_faces_per_frame(len(faces_coords))
                    faces_id_of_frame = faces_module.save_faces_to_file(faces_coords, frame, config.FACES_OUTPUT_PATH, post_metadata, frame_index)
                    face_ids.extend(faces_id_of_frame)#add the face ids of the frame to the list of face ids
                frame_index += 1
            metadata_module.save_post_metadata(post_metadata)
            return face_ids
        else:
            raise NotSupportedException(post_id = post_metadata.get_post_id())
    except ProcessException:
        raise
    except Exception as e:
        raise ProcessException(post_id = post_metadata.get_post_id(), cause = e)
    finally:
        if file is not None and os.path.exists(file):
            os.remove(file)



def process_post_by_deepface(post_metadata: metadata_module.Post_Metadata , detector_backend: str):
    file = None
    try:
        file = url_loader.download_url_to_file(post_metadata.get_media_url(), config.DOWNLOAD_PATH)
        if url_loader.is_an_image_file(file):
            image = files_loader.load_as_rgb(file)
            face_ids = []
            faces_coords = faces_module.get_faces_coordinates_from_image(image, detector_backend)
            if faces_coords is None or len(faces_coords) == 0:
                return []#if no faces are found, return an empty list of face ids
            face_ids = faces_module.save_faces_to_file(faces_coords, image, config.FACES_OUTPUT_PATH, post_metadata)
            post_metadata.set_max_faces_per_frame(len(faces_coords))
            post_metadata.add_frame_count(1)#add 1 to the frame count because we processed one frame
            metadata_module.save_post_metadata(post_metadata)
            return face_ids
        elif url_loader.is_a_video_file(file):
            video_frames = files_loader.load_video_as_rgb(file)
            face_ids = []
            frame_index = 0
            for frame in video_frames:
                post_metadata.add_frame_count(1)#add 1 to the frame count
                if frame is not None and files_loader.is_valid_image(frame):
                    faces_coords = faces_module.get_faces_coordinates_from_image(frame, detector_backend)
                    if faces_coords is None or len(faces_coords) == 0:
                        continue #if no faces are found, continue to the next frame
                    post_metadata.set_max_faces_per_frame(len(faces_coords))
                    faces_id_of_frame = faces_module.save_faces_to_file(faces_coords, frame, config.FACES_OUTPUT_PATH, post_metadata, frame_index)
                    face_ids.extend(faces_id_of_frame)#add the face ids of the frame to the list of face ids
                frame_index += 1
            metadata_module.save_post_metadata(post_metadata)
            return face_ids
        else:
            raise NotSupportedException(post_id = post_metadata.get_post_id())
    except ProcessException:
        raise
    except Exception as e:
        raise ProcessException(post_id = post_metadata.get_post_id(), cause = e)
    finally:
        if file is not None and os.path.exists(file):
            os.remove(file)
