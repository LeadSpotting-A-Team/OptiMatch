"""
Index builder script — ingests a dataset of images into the face vector store.

Supports two dataset layouts:
    --source csv     Read posts from a CSV file (Basic_dataset_sample.csv format).
    --source folders Read posts from sandbox/datasets/<source>/<folder>/ structure.

Usage:
    python -m scripts.build_index --source folders
    python -m scripts.build_index --source csv --csv-path sandbox/Basic_dataset_sample.csv

Run from the backend/ directory so that src.app.config resolves paths correctly.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import numpy as np

from src.app import config
from src.app.db.metadata_repository import SqliteMetadataRepository
from src.app.ingestion.face_harvester import IngestionException, ingest_post
from src.app.io.dataset_reader import read_posts_from_csv
from src.app.ml.arcface_embedding import ArcFaceEmbedding
from src.app.ml.mtcnn_detector import MtcnnDetector
from src.app.vector_store.faiss_vector_store import FaissVectorStore
from src.core.entities.post_metadata import PostMetadata
from src.core.services import embedding_service

MAX_BATCH_RETRIES = 8


# Removes existing index and map files so a fresh build starts clean.
def clear_existing_index() -> None:
    for path in (config.INDEX_PATH, config.MAP_PATH):
        if path.exists():
            path.unlink()
            print(f"Removed {path}")


# Processes a list of posts: ingests each one, computes embeddings, and adds
# them to the vector store in batches.  Returns the total number of faces added.
def process_posts(
    posts: list[PostMetadata],
    detector: MtcnnDetector,
    embedder: ArcFaceEmbedding,
    vector_store: FaissVectorStore,
    repository: SqliteMetadataRepository,
) -> int:
    total_faces = 0

    for post in posts:
        try:
            harvested = ingest_post(
                post=post,
                detector=detector,
                repository=repository,
                faces_output_dir=str(config.FACES_DIR),
                download_dir=str(config.DOWNLOAD_DIR),
                min_confidence=config.FACE_CONFIDENCE_THRESHOLD,
                min_face_size=config.MIN_FACE_SIZE,
            )
        except IngestionException as exc:
            print(exc.colored_str())
            continue
        except Exception as exc:
            print(f"Unexpected error for post {post.get_post_id()}: {exc}")
            continue

        # Compute embeddings for all harvested faces in this post.
        embeddings_list: list[np.ndarray] = []
        face_ids_list:   list[str]        = []
        for entry in harvested:
            emb = embedding_service.compute_embedding(entry["face_image"], embedder)
            if emb is None:
                continue
            embeddings_list.append(emb)
            face_ids_list.append(entry["face_id"])

        if not embeddings_list:
            continue

        # Batch-add with retries to handle Windows file-lock races.
        for attempt in range(MAX_BATCH_RETRIES):
            try:
                vector_store.add_faces_batch(
                    np.vstack(embeddings_list), face_ids_list
                )
                break
            except PermissionError:
                if attempt == MAX_BATCH_RETRIES - 1:
                    raise
                print(f"  PermissionError retry {attempt + 1}/{MAX_BATCH_RETRIES}…")
                time.sleep(0.3)

        total_faces += len(face_ids_list)
        print(f"  Post {post.get_post_id()}: added {len(face_ids_list)} face(s)")

    return total_faces


# Builds the post list from the folder-based dataset layout:
#   sandbox/datasets/<source>/<folder>/  (each folder = one post)
def load_posts_from_folders(datasets_root: str) -> list[PostMetadata]:
    posts: list[PostMetadata] = []
    post_id = 0
    for source in os.listdir(datasets_root):
        source_path = os.path.join(datasets_root, source)
        if not os.path.isdir(source_path):
            continue
        for folder_name in os.listdir(source_path):
            folder_path = os.path.join(source_path, folder_name)
            if not os.path.isdir(folder_path):
                continue
            posts.append(PostMetadata(post_id=str(post_id), media_url=folder_path))
            post_id += 1
    return posts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the face vector-store index.")
    parser.add_argument(
        "--source",
        choices=["csv", "folders"],
        default="folders",
        help="Dataset source: 'csv' for a CSV file, 'folders' for the sandbox layout.",
    )
    parser.add_argument(
        "--csv-path",
        default="sandbox/Basic_dataset_sample.csv",
        help="Path to the CSV file (only used when --source csv).",
    )
    parser.add_argument(
        "--datasets-root",
        default="sandbox/datasets",
        help="Root folder for the folder-based dataset (only used when --source folders).",
    )
    args = parser.parse_args()

    # Initialise shared components.
    detector   = MtcnnDetector(config.DETECTOR)
    embedder   = ArcFaceEmbedding()
    repository = SqliteMetadataRepository(config.DB_PATH)
    repository.clear_all()

    clear_existing_index()
    vector_store = FaissVectorStore(config.INDEX_PATH, config.MAP_PATH)

    # Load the post list from the chosen source.
    if args.source == "csv":
        posts = read_posts_from_csv(args.csv_path)
        print(f"Loaded {len(posts)} posts from CSV: {args.csv_path}")
    else:
        posts = load_posts_from_folders(args.datasets_root)
        print(f"Loaded {len(posts)} posts from folders: {args.datasets_root}")

    print(f"Starting ingestion of {len(posts)} posts…")
    total = process_posts(posts, detector, embedder, vector_store, repository)
    print(f"\nDone. Total faces indexed: {total}")

    # Retrain the IVF index with real data if enough vectors were collected.
    min_required = vector_store._nlist * 39
    if vector_store.get_face_count() >= min_required:
        print("Retraining IVF index on real embeddings…")
        vector_store.rebuild_index(vector_store.get_all_embeddings())
        print("IVF index retrained successfully.")
    else:
        print(
            f"Skipping IVF retraining: only {vector_store.get_face_count()} faces "
            f"(need {min_required})."
        )


if __name__ == "__main__":
    main()
