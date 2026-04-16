from typing import IO
from src.core.io.dataset_reader import read_posts_from_csv
from src.core.interfaces.i_vector_store import IVectorStore
from src.core.interfaces.i_face_detector import IFaceDetector
from src.core.interfaces.i_embedding_model import IEmbeddingModel
from src.core.interfaces.i_metadata_repository import IMetadataRepository
from src.app.ingestion.face_harvester import ingest_post
import numpy as np
#LEARN : (csv_file) -> add a faces to the database and ivf 
#SEARCH : (media_file) -> search for a face in the database and return the most similar faces
#* SEARCH_API : (first_name, last_name , media_file) -> search for a face in the database and return the most similar faces

#we need to redesign the all backend 

#link the frontend to the backend (to use the api)



#this function is used to learn the faces from the csv file and add them to the database and ivf
#this function returns the number of valid faces that were learned.
def learn_service(csv_file: IO[str] , detector: IFaceDetector , embedding_model: IEmbeddingModel , vector_store: IVectorStore , metadata_repository: IMetadataRepository) -> int:
    
    valid_face_count = 0
    
    posts = read_posts_from_csv(csv_file)
    for post in posts:
        try:
            #ingest_post -> [{"face_id": face_id, "face_image": face_image} , {"face_id": face_id2, "face_image": face_image2}  , ....]
            list_of_faces_dicts = ingest_post(post, detector, metadata_repository);
            for d in list_of_faces_dicts:
                try:
                    face_id, face_image = d["face_id"], d["face_image"]
                    emb = embedding_model.compute_embedding(embedding_model.preprocess(face_image))
                    if emb is not None:
                        vector_store.add_face(emb, face_id)
                        valid_face_count += 1
                except Exception as e:
                    pass # Ignore errors
        except Exception as e:#to skip the post if there is an error
            continue


    return valid_face_count