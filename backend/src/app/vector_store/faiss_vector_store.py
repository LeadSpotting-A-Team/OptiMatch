from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from src.core.interfaces.i_vector_store import IVectorStore

# ArcFace produces 512-dimensional embedding vectors.
_EMBEDDING_DIM = 512


class FaissVectorStore(IVectorStore):
    """
    FAISS IndexIVFFlat implementation of IVectorStore.

    Stores 512-dimensional ArcFace embeddings in a FAISS IVF index using inner
    product as the similarity metric (equivalent to cosine similarity for
    L2-normalised vectors).

    ID mapping:
        FAISS uses sequential integer IDs internally (called person_id here).
        A sidecar JSON file (map_path) stores the mapping:
            id_map[person_id] = face_id  (list; None for deleted slots)
        A reverse dict (_face_index) is rebuilt in memory at startup for O(1)
        lookups in the opposite direction.

    Both the index file and the JSON sidecar are written to disk after every
    mutation so the store survives process restarts.
    """

    def __init__(
        self,
        index_path: str | Path,
        map_path: str | Path,
        nlist: Optional[int] = None,
    ) -> None:
        self._index_path = Path(index_path)
        self._map_path   = Path(map_path)

        # Ensure parent directories exist before any disk operation.
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._map_path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve which nlist to use (priority: stored JSON → arg → default 100).
        stored_nlist = self._read_nlist_from_map()
        if stored_nlist is not None:
            self._nlist = stored_nlist
        elif nlist is not None:
            self._nlist = nlist
        else:
            self._nlist = 100

        self._index: faiss.Index = self._load_or_create_index()
        self._load_id_map()

    # ── Index lifecycle ───────────────────────────────────────────────────────

    # Reads the nlist value stored in the JSON sidecar.
    # Returns None when the sidecar does not yet exist (fresh store).
    # Returns the default 100 when the sidecar exists but has no "nlist" key
    # (legacy compatibility).
    def _read_nlist_from_map(self) -> Optional[int]:
        if not self._map_path.is_file():
            return None
        try:
            data = json.loads(self._map_path.read_text(encoding="utf-8"))
            value = data.get("nlist")
            return int(value) if value is not None else 100
        except (json.JSONDecodeError, ValueError):
            return 100

    # Loads the FAISS index from disk if it exists, otherwise creates a new
    # trained IndexIVFFlat wrapped in an IndexIDMap and writes it to disk.
    def _load_or_create_index(self) -> faiss.Index:
        if self._index_path.is_file():
            return faiss.read_index(str(self._index_path))
        index = self._build_trained_ivf(self._nlist)
        faiss.write_index(index, str(self._index_path))
        return index

    # Creates a new IndexIVFFlat trained on random unit vectors so FAISS can
    # initialise its Voronoi centroids without requiring real data up front.
    def _build_trained_ivf(self, nlist: int) -> faiss.IndexIDMap:
        quantizer = faiss.IndexFlatIP(_EMBEDDING_DIM)
        ivf = faiss.IndexIVFFlat(
            quantizer, _EMBEDDING_DIM, nlist, faiss.METRIC_INNER_PRODUCT
        )
        rng = np.random.default_rng(42)
        dummy = rng.standard_normal((nlist * 40, _EMBEDDING_DIM)).astype(np.float32)
        norms = np.linalg.norm(dummy, axis=1, keepdims=True)
        norms[norms < 1e-9] = 1.0
        dummy /= norms
        ivf.train(dummy)
        return faiss.IndexIDMap(ivf)

    # ── ID map helpers ────────────────────────────────────────────────────────

    # Loads the id_map list from the JSON sidecar and rebuilds the in-memory
    # reverse lookup dict (_face_index).
    def _load_id_map(self) -> None:
        if self._map_path.is_file():
            data = json.loads(self._map_path.read_text(encoding="utf-8"))
            self._id_map: list[Optional[str]] = data["id_map"]
        else:
            self._id_map = []
        self._face_index: dict[str, int] = {
            face_id: person_id
            for person_id, face_id in enumerate(self._id_map)
            if face_id is not None
        }

    # Atomically writes the nlist and id_map to the JSON sidecar using a
    # temp-file-then-rename strategy to avoid partial writes.
    def _save_id_map(self) -> None:
        tmp = str(self._map_path) + ".tmp"
        Path(tmp).write_text(
            json.dumps({"nlist": self._nlist, "id_map": self._id_map}),
            encoding="utf-8",
        )
        os.replace(tmp, str(self._map_path))

    # Registers a new face_id by appending it to id_map and recording its
    # sequential person_id in the reverse lookup dict.
    # Raises ValueError if the face_id already exists.
    def _register_face(self, face_id: str) -> int:
        if face_id in self._face_index:
            raise ValueError(f"face_id '{face_id}' already exists in the index.")
        person_id = len(self._id_map)
        self._id_map.append(face_id)
        self._face_index[face_id] = person_id
        return person_id

    # Removes face_id from the reverse lookup dict and nullifies its slot in
    # id_map (slot stays to keep sequential person_ids stable).
    # Raises KeyError if face_id does not exist.
    def _unregister_face(self, face_id: str) -> int:
        if face_id not in self._face_index:
            raise KeyError(f"face_id '{face_id}' not found in the index.")
        person_id = self._face_index.pop(face_id)
        self._id_map[person_id] = None
        return person_id

    # Returns the inner IndexIVFFlat unwrapped from the IndexIDMap wrapper.
    @property
    def _ivf(self) -> faiss.IndexIVFFlat:
        return faiss.downcast_index(self._index.index)

    # ── IVectorStore implementation ───────────────────────────────────────────

    # Adds a single 512-d embedding to the FAISS index and persists both
    # the index file and the JSON sidecar to disk.
    # Raises ValueError if face_id is already registered.
    def add_face(self, embedding: np.ndarray, face_id: str) -> None:
        vec = np.asarray(embedding, dtype=np.float32).flatten()
        if vec.shape[0] != _EMBEDDING_DIM:
            raise ValueError(f"Expected dimension {_EMBEDDING_DIM}, got {vec.shape[0]}")

        person_id = self._register_face(face_id)
        self._index.add_with_ids(
            vec.reshape(1, -1),
            np.array([person_id], dtype=np.int64),
        )
        faiss.write_index(self._index, str(self._index_path))
        self._save_id_map()

    # Adds N embeddings in a single FAISS call and persists both files once.
    # Retries _save_id_map up to save_retries times on Windows PermissionError.
    def add_faces_batch(
        self,
        embeddings: np.ndarray,
        face_ids: list[str],
        save_retries: int = 3,
    ) -> None:
        vecs = np.ascontiguousarray(
            np.asarray(embeddings, dtype=np.float32).reshape(-1, _EMBEDDING_DIM)
        )
        if vecs.shape[0] != len(face_ids):
            raise ValueError("embeddings count does not match face_ids count")

        person_ids = np.array(
            [self._register_face(fid) for fid in face_ids], dtype=np.int64
        )
        self._index.add_with_ids(vecs, person_ids)
        faiss.write_index(self._index, str(self._index_path))

        for attempt in range(save_retries):
            try:
                self._save_id_map()
                break
            except PermissionError:
                if attempt == save_retries - 1:
                    raise
                time.sleep(0.25)

    # Searches the index for the k most similar vectors to query_embedding.
    # nprobe controls how many IVF clusters are scanned (higher = more accurate,
    # slower).  Returns an empty list when the index contains no vectors.
    def search_nearest_faces(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        nprobe: int = 5,
    ) -> list[dict]:
        if self._index.ntotal == 0:
            return []

        vec = np.asarray(query_embedding, dtype=np.float32).flatten().reshape(1, -1)
        self._ivf.nprobe = nprobe
        k = min(k, self._index.ntotal)
        scores, labels = self._index.search(vec, k)

        return [
            {"face_id": self._id_map[int(labels[0, j])], "score": float(scores[0, j])}
            for j in range(k)
            if labels[0, j] >= 0
        ]

    # Removes the vector for face_id from the FAISS index and persists changes.
    # Raises KeyError if face_id does not exist.
    def delete_face(self, face_id: str) -> None:
        person_id = self._unregister_face(face_id)
        self._index.remove_ids(np.array([person_id], dtype=np.int64))
        faiss.write_index(self._index, str(self._index_path))
        self._save_id_map()

    # Returns the total number of face vectors currently held in the index.
    def get_face_count(self) -> int:
        return int(self._index.ntotal)

    # Extracts and returns all stored embedding vectors as a contiguous float32
    # array of shape (N, 512) by walking all IVF inverted lists.
    def get_all_embeddings(self) -> np.ndarray:
        vecs, _ = self._extract_all_vectors()
        return vecs

    # Retrains the IVF index on training_data, optionally changing nlist.
    # All existing vectors are preserved and re-inserted after retraining.
    # Uses an atomic rename to avoid corrupting the index file on failure.
    def rebuild_index(
        self,
        training_data: np.ndarray,
        new_nlist: Optional[int] = None,
    ) -> None:
        effective_nlist = new_nlist if new_nlist is not None else self._nlist
        train = np.ascontiguousarray(
            np.asarray(training_data, dtype=np.float32).reshape(-1, _EMBEDDING_DIM)
        )
        min_required = effective_nlist * 39
        if train.shape[0] < min_required:
            raise ValueError(
                f"Training data needs at least {min_required} vectors "
                f"(39 × nlist={effective_nlist}); got {train.shape[0]}"
            )

        existing_vecs, existing_person_ids = self._extract_all_vectors()

        quantizer = faiss.IndexFlatIP(_EMBEDDING_DIM)
        ivf = faiss.IndexIVFFlat(
            quantizer, _EMBEDDING_DIM, effective_nlist, faiss.METRIC_INNER_PRODUCT
        )
        ivf.train(train)
        new_index = faiss.IndexIDMap(ivf)

        if existing_vecs.shape[0] > 0:
            new_index.add_with_ids(existing_vecs, existing_person_ids)

        tmp_path = str(self._index_path) + ".tmp"
        faiss.write_index(new_index, tmp_path)
        os.replace(tmp_path, str(self._index_path))

        self._index = new_index
        self._nlist = effective_nlist
        self._save_id_map()

    # ── Internal extraction ───────────────────────────────────────────────────

    # Walks all IVF inverted lists and collects every stored vector together
    # with its original person_id (sequential integer).
    # Returns a tuple (vectors, person_ids) both as contiguous numpy arrays.
    def _extract_all_vectors(self) -> tuple[np.ndarray, np.ndarray]:
        id_map_arr = faiss.vector_to_array(self._index.id_map)
        invlists   = self._ivf.invlists
        code_size  = self._ivf.code_size

        all_vecs:       list[np.ndarray] = []
        all_person_ids: list[np.ndarray] = []

        for list_no in range(self._ivf.nlist):
            size = invlists.list_size(list_no)
            if size == 0:
                continue
            internal_ids = faiss.rev_swig_ptr(invlists.get_ids(list_no),   size).copy()
            raw_codes    = faiss.rev_swig_ptr(invlists.get_codes(list_no),  size * code_size).copy()
            vecs         = raw_codes.view(np.float32).reshape(size, _EMBEDDING_DIM)
            all_vecs.append(vecs)
            all_person_ids.append(id_map_arr[internal_ids])

        if not all_vecs:
            return (
                np.empty((0, _EMBEDDING_DIM), dtype=np.float32),
                np.empty(0, dtype=np.int64),
            )

        return (
            np.ascontiguousarray(np.vstack(all_vecs), dtype=np.float32),
            np.concatenate(all_person_ids).astype(np.int64),
        )
