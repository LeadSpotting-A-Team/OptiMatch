import os
import logging
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

import Face_Harvester
import Digital_Identity
import IVF

warnings.filterwarnings('ignore', category=DeprecationWarning)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

face_vector_store = IVF.FaceVectorStore("sandbox/face_vector_store.index")

while True:
    url = input("Enter the URL of the image to search for: ")
    if url == "exit":
        break
    if not url:
        print("Please enter a valid URL.")
        continue

    frames = Face_Harvester.Harveste_URL(url)
    
    min_confidence = float(input("Enter the minimum confidence: "))
    
    frame_count = 0
    face_count = 0

    for frame in frames:
        frame_count += 1
        for cropped_face in frame:
            face_count += 1
            embedding = Digital_Identity.get_face_embedding(cropped_face)
            if embedding is None:
                continue
            results = face_vector_store.search_face(embedding)
            for result in results:
                if result["score"] > min_confidence:
                    print(f"Found {result['face_id']} with score {result['score']}")

    print(f"Found {face_count} faces in {frame_count} frames")