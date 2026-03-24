from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class IVectorStore(ABC):
    """
    Contract for a face-embedding vector store.
    The core layer describes *what* operations are available; the FAISS
    implementation in src/app/vector_store/ handles the underlying index.
    """

    @abstractmethod
    def add_face(self, embedding: np.ndarray, face_id: str) -> None:
        # Adds a single embedding vector associated with face_id to the store.
        # Raises ValueError if face_id already exists in the index.
        ...

    @abstractmethod
    def add_faces_batch(
        self,
        embeddings: np.ndarray,
        face_ids: list[str],
    ) -> None:
        # Adds multiple embeddings in one atomic operation.
        # embeddings must have shape (N, 512); face_ids must have length N.
        # Raises ValueError if lengths do not match or any face_id is a duplicate.
        ...

    @abstractmethod
    def search_nearest_faces(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
    ) -> list[dict]:
        # Searches the index for the k most similar faces to query_embedding.
        # Returns a list of dicts with keys "face_id" (str) and "score" (float).
        # Returns an empty list when the index contains no vectors.
        ...

    @abstractmethod
    def delete_face(self, face_id: str) -> None:
        # Removes the vector associated with face_id from the index.
        # Raises KeyError if face_id does not exist.
        ...

    @abstractmethod
    def get_face_count(self) -> int:
        # Returns the total number of face vectors currently stored in the index.
        ...

    @abstractmethod
    def get_all_embeddings(self) -> np.ndarray:
        # Returns all stored embedding vectors as a float32 array of shape (N, 512).
        # Returns an empty array when the index is empty.
        ...

    @abstractmethod
    def rebuild_index(
        self,
        training_data: np.ndarray,
        new_nlist: Optional[int] = None,
    ) -> None:
        # Retrains the index on training_data, optionally changing the cluster count.
        # All existing vectors are preserved and re-inserted after training.
        # Raises ValueError if training_data contains fewer than 39 * nlist vectors.
        ...
