"""
Interactive CLI face-search tool.

Downloads an image from a user-supplied URL, detects faces, computes embeddings,
and prints the top matches from the vector store together with their scores.

Usage:
    python -m scripts.search_cli

Run from the backend/ directory.  Type "exit" to quit the loop.
"""
from __future__ import annotations

import logging
import os
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("tensorflow").setLevel(logging.ERROR)

from src.app import config
from src.app.io import files_loader, url_loader
from src.app.ml.arcface_embedding import ArcFaceEmbedding
from src.app.ml.mtcnn_detector import MtcnnDetector
from src.app.vector_store.faiss_vector_store import FaissVectorStore
from src.core.services import embedding_service, harvesting_service


def main() -> None:
    # Initialise components.
    detector      = MtcnnDetector(config.DETECTOR)
    embedder      = ArcFaceEmbedding()
    vector_store  = FaissVectorStore(config.INDEX_PATH, config.MAP_PATH)

    print(f"Vector store loaded: {vector_store.get_face_count()} faces indexed.")
    print("Enter a URL to search. Type 'exit' to quit.\n")

    while True:
        url = input("Image URL: ").strip()
        if url.lower() == "exit":
            break
        if not url:
            print("Please enter a valid URL.")
            continue

        # Download the image and harvest faces from it.
        local_file: str | None = None
        try:
            local_file = url_loader.download_to_temp_file(url, str(config.DOWNLOAD_DIR))
            image = files_loader.load_image_as_rgb(local_file)
        except Exception as exc:
            print(f"Failed to load image: {exc}\n")
            continue
        finally:
            if local_file and os.path.exists(local_file):
                os.remove(local_file)

        cropped_faces = harvesting_service.harvest_faces_from_image(
            image,
            detector,
            config.FACE_CONFIDENCE_THRESHOLD,
            config.MIN_FACE_SIZE,
        )
        if not cropped_faces:
            print("No faces detected.\n")
            continue

        # Ask for a minimum score threshold to filter output.
        raw_threshold = input("Minimum confidence score (0.0–1.0): ").strip()
        try:
            min_score = float(raw_threshold)
        except ValueError:
            min_score = 0.0

        # Search for each detected face and print matches above the threshold.
        total_matches = 0
        for face_index, cropped_face in enumerate(cropped_faces):
            embedding = embedding_service.compute_embedding(cropped_face, embedder)
            if embedding is None:
                continue
            results = vector_store.search_nearest_faces(embedding)
            for result in results:
                if result["score"] >= min_score:
                    print(
                        f"  Face {face_index} → {result['face_id']}  "
                        f"score={result['score']:.4f}"
                    )
                    total_matches += 1

        print(f"Detected {len(cropped_faces)} face(s). {total_matches} match(es) found.\n")


if __name__ == "__main__":
    main()
