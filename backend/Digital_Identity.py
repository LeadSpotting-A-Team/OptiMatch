import cv2
import numpy as np
import onnxruntime as ort
import os
import pandas as pd
import config

# model settings
MODEL_PATH = config.ARCFACE_MODEL_PATH
session = ort.InferenceSession(MODEL_PATH)


#get the embedding of a face image (face_image_rgb)
#return the embedding as a single dimensional array of size 512
def get_face_embedding(face_image_rgb : np.ndarray) -> np.ndarray:
    # 1.Pre-processing
    face_resized = cv2.resize(face_image_rgb, config.ARCFACE_INPUT_SIZE)
    
    # 2.Normalization to the range [-1, 1]
    #RGB [0,255] -> [-1,1]
    face_data = face_resized.astype(np.float32)
    face_data = (face_data - 127.5) / 128.0
    
    # 3. matrix of R , G , B channels
    #making the matrix separate for each channel
    face_data = np.transpose(face_data, (2, 0, 1)) 

    #expand the dimensions of the matrix.
    input_blob = np.expand_dims(face_data, axis=0)

    #4. Inference
    #get the input name from the model
    inputs = {session.get_inputs()[0].name: input_blob}
    #run the model
    embedding = session.run(None, inputs)[0][0]

    #5. Normalization
    #normalize the embedding to the unit vector
    norm = np.linalg.norm(embedding)
    if norm > 1e-6:
        embedding = embedding / norm
        
    return embedding

#get the similarity between two embeddings
#return the similarity as a float between 0 and 1
def get_embeddings_similarity(embedding1 : np.ndarray, embedding2 : np.ndarray):
    sim = np.dot(embedding1, embedding2)
    return np.clip(float(sim), 0.0, 1.0)
    #return 0 if the similarity is negative

#O(N * 512) where N is the number of embeddings in the database
def find_matches(query_embedding : np.ndarray , threshold : float , database_matrix : np.ndarray):

    #make the query embedding a 1D array
    query_vec = np.array(query_embedding).astype('float32').flatten()
    
    #calculate the similarity between the query embedding and the database matrix
    similarities = np.dot(database_matrix, query_vec)
    
    #find the indices that are greater than the threshold
    matched_indices = np.where(similarities > threshold)[0]
    
    #create a list of (index, score)
    matches = []
    for idx in matched_indices:
        matches.append((idx, similarities[idx]))
    
    #sort the matches by the score (from high to low)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches

