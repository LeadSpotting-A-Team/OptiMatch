import os
import Face_Harvester
import Digital_Identity
import Face_Detection
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

import logging
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import config
import metadata as metadata_module
from metadata import Post_Metadata

logging.getLogger('tensorflow').setLevel(logging.ERROR)

metadata_module.clear_tables()

# DeepFace detector_backend: "opencv", "ssd", "mtcnn", "retinaface", "mediapipe", etc.
#detector = MTCNN()
while True:
    #get the detector
    detector = input("Enter the \033[93mdetector\033[0m: ")

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
        #crop the faces from the URL [cropped_faces : list[np.ndarray | None]]
        post_metadata = Post_Metadata(post_id="1", media_url=url, link_to_post=None, timestamp=None, platform=None)
        face_ids = Face_Harvester.Store_Harvested_Post(post_metadata)

        images = Face_Harvester.get_images_from_faces_ids(face_ids)

        embeddings = []
        for image in images:
            embedding = Digital_Identity.get_face_embedding(image)
            embeddings.append(embedding)

        for index1 in range(len(embeddings)):
            for index2 in range(len(embeddings)):
                embedding1 = embeddings[index1]
                embedding2 = embeddings[index2]
                print(f"similarity [{index1}][{index2}]: {Digital_Identity.get_embeddings_similarity(embedding1, embedding2)}")

        #crop_face = face_ids[0]

        #embedding = Digital_Identity.get_face_embedding(crop_face)

        #print(f"similarity: {Digital_Identity.get_embeddings_similarity(embedding, Digital_Identity.get_face_embedding(crop_face))}")

    except Face_Harvester.ProcessException as e:
        print(e.colored_str())