import os
import time
import Face_Harvester
import Digital_Identity
import Face_Detection
import IVF
import numpy as np
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

import logging
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import config
import metadata as metadata_module
from metadata import Post_Metadata

logging.getLogger('tensorflow').setLevel(logging.ERROR)

#------------ clear ivf ------------
if os.path.exists("face_vault.index"):
    os.remove("face_vault.index")#clear the ivf index
if os.path.exists("face_vault.map.json"):
    os.remove("face_vault.map.json")#clear the face vault map
if os.path.exists("sandbox/face_vector_store.index"):
    os.remove("sandbox/face_vector_store.index")#clear the face vector store index

metadata_module.clear_tables()
MAX_RETRIES = 8 #max retries for adding faces to the ivf index
path = "sandbox/datasets/"
ivf = IVF.FaceVectorStore()
for source in os.listdir(path):
    post_id = 0
    source_path = os.path.join(path, source)
    for folder_name in os.listdir(source_path):
        folder_path = os.path.join(source_path, folder_name)
        if not os.path.isdir(folder_path):
            continue
        post_metadata = Post_Metadata(post_id=post_id, media_url=folder_name)
        metadata_module.save_post_metadata(post_metadata)
        faces_count = 0
        embeddings_list = []
        face_ids_list = []
        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)
            if not os.path.isfile(image_path):
                continue
            cropped_faces = Face_Harvester.Harveste_Image(image_path)
            for cropped_face in cropped_faces:
                faces_count += 1
                face_id = Face_Harvester.get_Harvested_Face_id(image_path, 0, faces_count)
                embedding = Digital_Identity.get_face_embedding(cropped_face)
                metadata_module.link_harvested_faces_to_post(face_id, post_id, cropped_face)
                embeddings_list.append(embedding)
                face_ids_list.append(face_id)
        if embeddings_list:
            for attempt in range(MAX_RETRIES):
                try:
                    ivf.add_faces_batch(np.vstack(embeddings_list), face_ids_list)
                    break
                except PermissionError:
                    if attempt == MAX_RETRIES - 1:
                        raise
                    print(f"PermissionError: {attempt + 1}/8, retrying...")
                    time.sleep(0.3)
        post_id += 1
        print(f"Processed {faces_count} faces for folder {folder_name}")
if ivf.get_total_count() >= IVF.MINIMUM_TRAINING_DATA_SIZE:
    ivf.rebuild_and_train(ivf.get_all_embeddings())  # train the ivf
    print("IVF index rebuilt and trained")