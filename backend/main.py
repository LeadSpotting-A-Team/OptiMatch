import os
import Face_Harvester
import Digital_Identity
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'
import dataset_reader
import logging
import warnings
import IVF
import config
import metadata as metadata_module
from metadata import Post_Metadata

warnings.filterwarnings('ignore', category=DeprecationWarning)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
metadata_module.clear_tables()

#need to check difrent way to generate the face id
#we can use the face coordinates to generate a unique id

posts_metadata = dataset_reader.read_dataset_as_csv("sandbox/Basic_dataset_sample.csv")
posts_metadata_count = 0
face_vector_store = IVF.FaceVectorStore("sandbox/face_vector_store.index")
for post_metadata in posts_metadata:
    try:
        post_faces = Face_Harvester.Store_Harvested_Post(post_metadata)
        for face in post_faces:
            face_id = face["face_id"]
            face_image = face["face_image"]
            face_emb = Digital_Identity.get_face_embedding(face_image)
            if face_emb is None:
                continue #skip the face if the embedding is None
            face_vector_store.add_face(face_emb, face_id)
        print(f"Added {len(post_faces)} faces to the vector store")
        posts_metadata_count += 1
    except Face_Harvester.ProcessException as e:
        print(e.colored_str())
    except Exception as e:
        print(f"Error: {e}")