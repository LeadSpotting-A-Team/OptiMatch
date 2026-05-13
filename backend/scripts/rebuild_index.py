"""
Index rebuild script — retrains an existing FAISS IVF index with a new nlist.

All stored vectors are preserved; only the clustering structure is updated.
This is useful when the index was originally built with too few clusters for
the amount of data it now contains.

Usage:
    python -m scripts.rebuild_index

Run from the backend/ directory.
"""
from __future__ import annotations

import sys

from src.app import config
from src.app.vector_store.faiss_vector_store import FaissVectorStore


def main() -> None:
    # Prompt for the index file path (defaults to the configured path).
    index_path = input(
        f"Index file path [{config.INDEX_PATH}]: "
    ).strip() or str(config.INDEX_PATH)

    if not __import__("pathlib").Path(index_path).exists():
        print(f"Error: index file not found: {index_path}")
        sys.exit(1)

    # Derive the map sidecar path from the index path.
    map_path = index_path.replace(".index", ".map.json")

    # Load the existing index.
    vector_store = FaissVectorStore(index_path, map_path)
    current_count = vector_store.get_face_count()
    print(f"Loaded index with {current_count} stored vectors (current nlist={vector_store._nlist}).")

    # Prompt for the desired new nlist value.
    raw_nlist = input("New nlist value: ").strip()
    try:
        new_nlist = int(raw_nlist)
    except ValueError:
        print("Error: nlist must be an integer.")
        sys.exit(1)

    min_required = new_nlist * 39
    if current_count < min_required:
        print(
            f"Error: not enough vectors to train with nlist={new_nlist}. "
            f"Need {min_required}, have {current_count}."
        )
        sys.exit(1)

    # Retrieve all stored embeddings and retrain the index.
    print("Extracting all embeddings…")
    training_data = vector_store.get_all_embeddings()

    print(f"Rebuilding index with nlist={new_nlist}…")
    vector_store.rebuild_index(training_data, new_nlist=new_nlist)
    print(f"Done. Index rebuilt successfully with nlist={new_nlist}.")


if __name__ == "__main__":
    main()
