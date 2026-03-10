import numpy as np
import config
from Cropped_Face import CroppedFace
from embeddings_models.FaceEmbeddingModel import FaceEmbeddingModel
from embeddings_models.ArcFace_Embedding import ArcFaceEmbedding

#define the embedding model
EMBEDDING_MODEL : FaceEmbeddingModel | None = None
if config.EMBEDDING_MODEL == 'ArcFace':

    EMBEDDING_MODEL = ArcFaceEmbedding()
else:
    raise ValueError(f"Embedding model {config.EMBEDDING_MODEL} not supported")

#get the embedding of a face image (face_image_rgb)
#return the embedding as a single dimensional array of size 512
def get_face_embedding(cropped_face : CroppedFace) -> np.ndarray | None:
    # 1. Validation
    if cropped_face is None or cropped_face.get_image() is None:
        return None
        
    # 2. Pre-processing (Alignment and Resizing)
    # This uses the specific logic of the loaded model (e.g., ArcFace)
    preprocessed_face = EMBEDDING_MODEL.preprocess(cropped_face)
    
    # 3. Inference (Generating the 512-d vector)
    embedding = EMBEDDING_MODEL.get_embedding(preprocessed_face)
    return embedding


#get the similarity between two embeddings
#return the similarity as a float between 0 and 1
def get_embeddings_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    # Perform dot product
    sim = np.dot(embedding1, embedding2)
    
    # Clip results to [0, 1] range to handle potential floating point noise
    return np.clip(float(sim), 0.0, 1.0)

# O(N * 512) where N is the number of embeddings in the database
def find_matches(query_embedding: np.ndarray, threshold: float, database_matrix: np.ndarray):
    # 1. Ensure the query is a flattened float32 array
    query_vec = np.array(query_embedding).astype('float32').flatten()
    
    # 2. Vectorized similarity calculation (Dot product of matrix and vector)
    # This returns an array of shape (N,) containing all similarity scores
    similarities = np.dot(database_matrix, query_vec)
    
    # 3. Filter indices where similarity exceeds the threshold
    matched_indices = np.where(similarities > threshold)[0]
    
    # 4. Create list of (index, score) and sort by score descending
    # Using a list comprehension is generally faster than manual appending
    matches = [(idx, float(similarities[idx])) for idx in matched_indices]
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches
