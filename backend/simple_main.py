import os

from mtcnn import MTCNN
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

import logging
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import config
import metadata as metadata_module
from metadata import Post_Metadata
from Process import process_post , ProcessException, NotSupportedException

logging.getLogger('tensorflow').setLevel(logging.ERROR)

metadata_module.clear_tables()

# DeepFace detector_backend: "opencv", "ssd", "mtcnn", "retinaface", "mediapipe", etc.
detector = MTCNN()
while True:
    #get the face confidence threshold
    face_confidence_threshold = float(input("Enter the \033[93mface confidence threshold\033[0m: "))
    config.FACE_CONFIDENCE_THRESHOLD = face_confidence_threshold

    #get the minimum face size
    min_face_size = int(input("Enter the \033[93mminimum face size\033[0m: "))
    config.MIN_FACE_SIZE = min_face_size

    #get the URL of the image or video
    url = input("Enter the \033[93mURL\033[0m of the image or video: ")
    if url == "exit":
        break
    post_metadata = Post_Metadata(post_id="1", media_url=url, link_to_post=None, timestamp=None, platform=None)

    try:
        face_ids = process_post(post_metadata, detector)
        if len(face_ids) == 0:
            print("No faces found.")
        else:
            print(f"Found {len(face_ids)} face(s).")
    except ProcessException as e:
        print(f"\033[91m{e}\033[0m")