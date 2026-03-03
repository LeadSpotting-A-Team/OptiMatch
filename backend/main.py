import os
from mtcnn import MTCNN
import files_loader
from faces import *

#main function

detector = MTCNN()

frames = files_loader.load_video_as_rgb("sandbox/video.mp4")
frame_index = 0
video_faces_directory = os.path.join("sandbox", f"video_faces_directory")
os.makedirs(video_faces_directory, exist_ok=True)
for frame in frames:
    if frame is None: continue
    faces = get_faces_coordinates_from_image(frame , detector)
    frame_faces_directory = os.path.join("sandbox", "video_faces_directory", f"frame_{frame_index}")
    os.makedirs(frame_faces_directory, exist_ok=True)
    save_faces_to_file(faces , frame , frame_faces_directory)
    frame_index += 1