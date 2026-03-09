import os
from pathlib import Path
from typing import List

import faiss
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

# ArcFace produces 512-dimensional embeddings
DIM = 512

# Number of Voronoi clusters (cells) the index is divided into.
# FAISS recommendation: nlist ≈ sqrt(N) for N vectors.
# 4000 is optimized for datasets of 1M+ vectors.
NLIST = 4000

# Default path where the index file is persisted on disk
INDEX_PATH = "face_vault.index"


# ── Module-level helpers (private) ────────────────────────────────────────────

# What  : Creates a brand-new IndexIVFFlat wrapped in an IndexIDMap.
#         Performs a dummy training pass with random unit-normalized vectors
#         so that FAISS initializes its cluster centroids before any real data
#         is added.  The dummy data does NOT stay in the index after training.
# Gets  : nothing
# Returns: a trained faiss.IndexIDMap wrapping a faiss.IndexIVFFlat
def _make_trained_ivf() -> faiss.IndexIDMap:
    quantizer = faiss.IndexFlatIP(DIM)
    ivf = faiss.IndexIVFFlat(quantizer, DIM, NLIST, faiss.METRIC_INNER_PRODUCT)

    # IVF must be trained before any vectors can be added.
    # We generate NLIST*2 random unit vectors as a stand-in for real embeddings.
    rng = np.random.default_rng(42)
    dummy = rng.standard_normal((NLIST * 2, DIM)).astype(np.float32)
    norms = np.linalg.norm(dummy, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0   # guard against zero-norm edge case
    dummy /= norms
    ivf.train(dummy)

    # Wrap the IVF inside IndexIDMap so we can use custom integer IDs
    # instead of FAISS's default sequential 0-based IDs.
    return faiss.IndexIDMap(ivf)


# What  : Loads the index from disk if the file already exists.
#         If the file is missing, creates a new trained index and saves it.
# Gets  : index_path — absolute or relative path to the .index file
# Returns: a faiss.Index (IndexIDMap wrapping IndexIVFFlat) ready for use
def _load_or_create_index(index_path: str) -> faiss.Index:
    if os.path.isfile(index_path):
        return faiss.read_index(index_path)

    index = _make_trained_ivf()
    faiss.write_index(index, index_path)
    return index


# ── Main class ────────────────────────────────────────────────────────────────

class FaceVectorStore:
    """
    Production-ready FAISS wrapper for storing and searching ArcFace embeddings.

    Index type : IndexIVFFlat  (exact distances inside each cluster)
    Metric     : Inner Product (equivalent to cosine similarity on unit vectors)
    ID support : IndexIDMap    (custom integer person IDs instead of sequential ones)
    Persistence: index is saved to disk after every write operation
    """

    # What  : Loads the index from disk if it exists; otherwise initialises a
    #         new trained index and saves it.
    # Gets  : index_path — path to the .index file (default: face_vault.index)
    # Returns: nothing (sets self._index and self._path)
    def __init__(self, index_path: str = INDEX_PATH) -> None:
        self._path = Path(index_path)
        self._index: faiss.Index = _load_or_create_index(str(self._path))

    # What  : Convenience property that drills through the IndexIDMap wrapper
    #         to reach the underlying IndexIVFFlat.  
    # Needed to set nprobe and iterate the inverted lists during extraction.
    # Gets  : nothing
    # Returns: faiss.IndexIVFFlat
    @property
    def _ivf(self) -> faiss.IndexIVFFlat:
        # self._index is IndexIDMap; .index is its wrapped sub-index
        return faiss.downcast_index(self._index.index)

    # ── Write operations ──────────────────────────────────────────────────────

    # What  : Adds a single face embedding to the index and saves to disk.
    #         Use add_faces_batch for bulk inserts (much faster for many faces).
    # Gets  : embedding  — 1-D numpy array of shape (512,), already L2-normalised
    #         person_id  — unique integer ID for this face (must not already exist)
    # Returns: nothing
    def add_face(self, embedding: np.ndarray, person_id: int) -> None:
        vec = np.asarray(embedding, dtype=np.float32).flatten()

        if vec.shape[0] != DIM:
            raise ValueError(f"Embedding must have dimension {DIM}, got {vec.shape[0]}")
        if not self._index.is_trained:
            raise RuntimeError("Index is not trained; cannot add vectors.")

        ids = np.array([person_id], dtype=np.int64)
        self._index.add_with_ids(vec.reshape(1, -1), ids)
        faiss.write_index(self._index, str(self._path))

    # What  : Adds many face embeddings to the index in a single FAISS call,
    #         then saves to disk once.  Preferred over calling add_face in a loop
    #         because the write_index cost is paid only once.
    # Gets  : embeddings  — 2-D numpy array of shape (N, 512), L2-normalised rows
    #         person_ids  — list of N unique integer IDs (one per embedding)
    # Returns: nothing
    def add_faces_batch(self, embeddings: np.ndarray, person_ids: List[int]) -> None:
        # ascontiguousarray ensures the memory layout is C-contiguous,
        # which FAISS requires — slices of larger arrays can be non-contiguous.
        vecs = np.ascontiguousarray(
            np.asarray(embeddings, dtype=np.float32).reshape(-1, DIM)
        )
        ids = np.asarray(person_ids, dtype=np.int64)

        if vecs.shape[0] != ids.shape[0]:
            raise ValueError(
                f"Number of embeddings ({vecs.shape[0]}) must match "
                f"number of IDs ({ids.shape[0]})"
            )
        if vecs.shape[1] != DIM:
            raise ValueError(
                f"Each embedding must have dimension {DIM}, got {vecs.shape[1]}"
            )
        if not self._index.is_trained:
            raise RuntimeError("Index is not trained; cannot add vectors.")

        self._index.add_with_ids(vecs, ids)
        faiss.write_index(self._index, str(self._path))

    # What  : Removes a single person from the index by their integer ID,
    #         then saves to disk.
    # Gets  : person_id — the integer ID that was used when adding the face
    # Returns: nothing
    def delete_face(self, person_id: int) -> None:
        ids = np.array([person_id], dtype=np.int64)

        # IndexIDMap.remove_ids accepts a numpy int64 array directly;
        # internally FAISS wraps it in an IDSelectorBatch.
        self._index.remove_ids(ids)
        faiss.write_index(self._index, str(self._path))

    # ── Read operations ───────────────────────────────────────────────────────

    # What  : Searches the index for the K nearest neighbours of a query embedding.
    #         nprobe controls the accuracy/speed trade-off: higher = more accurate
    #         but slower (scans more clusters).
    # Gets  : query_embedding — 1-D numpy array of shape (512,), L2-normalised
    #         k              — number of top results to return (default 5)
    #         nprobe         — how many IVF clusters to scan per query (default 20)
    # Returns: list of dicts sorted by score descending, e.g.
    #          [{"id": 42, "score": 0.97}, {"id": 7, "score": 0.91}, ...]
    #          An empty list is returned when the index contains no vectors.
    def search_face(self, query_embedding: np.ndarray,k: int = 5,nprobe: int = 20) -> List[dict]:
        vec = np.asarray(query_embedding, dtype=np.float32).flatten().reshape(1, -1)

        if vec.shape[1] != DIM:
            raise ValueError(f"Query must have dimension {DIM}, got {vec.shape[1]}")
        if not self._index.is_trained:
            raise RuntimeError("Index is not trained; cannot search.")
        if self._index.ntotal == 0:
            return []

        # nprobe must be set on the inner IndexIVFFlat, not on the IndexIDMap wrapper.
        self._ivf.nprobe = nprobe

        # k cannot exceed the total number of indexed vectors
        k = min(k, self._index.ntotal)
        scores, labels = self._index.search(vec, k)

        # labels[0, j] == -1 means FAISS found no match for that slot (sparse index)
        return [
            {"id": int(labels[0, j]), "score": float(scores[0, j])}
            for j in range(k)
            if labels[0, j] >= 0
        ]

    # What  : Returns the total number of face vectors currently stored in the index.
    # Gets  : nothing
    # Returns: int
    def get_total_count(self) -> int:
        return int(self._index.ntotal)

    # ── Maintenance ───────────────────────────────────────────────────────────

    # What  : Re-trains the IVF index using real face embeddings instead of the
    #         initial dummy data.  Better centroids improve search accuracy.
    #         All existing vectors are preserved — they are extracted, the index
    #         is rebuilt with the new centroids, and they are re-inserted.
    #         Recommended once the database exceeds ~50k faces.
    #         Uses a temp-file + atomic rename so the original index is never
    #         left in a corrupt state if the process crashes mid-way.
    # Gets  : new_training_data — 2-D numpy array of shape (N, 512), L2-normalised.
    #         N must be at least NLIST * 39 (≈156k for nlist=4000) for stable centroids.
    # Returns: nothing (updates self._index in place and overwrites the index file)
    def rebuild_and_train(self, new_training_data: np.ndarray) -> None:
        train = np.ascontiguousarray(
            np.asarray(new_training_data, dtype=np.float32).reshape(-1, DIM)
        )

        min_required = NLIST * 39
        if train.shape[0] < min_required:
            raise ValueError(
                f"Training data needs at least {min_required} vectors "
                f"(39 × nlist={NLIST}); got {train.shape[0]}"
            )

        # Step 1 — snapshot all vectors and their external IDs before touching the index
        existing_vecs, existing_ext_ids = self._extract_all_vectors()

        # Step 2 — build a fresh IVF and train it on the real data distribution
        quantizer = faiss.IndexFlatIP(DIM)
        ivf = faiss.IndexIVFFlat(quantizer, DIM, NLIST, faiss.METRIC_INNER_PRODUCT)
        ivf.train(train)
        new_index = faiss.IndexIDMap(ivf)

        # Step 3 — re-insert all previously stored faces with their original IDs
        if existing_vecs.shape[0] > 0:
            new_index.add_with_ids(existing_vecs, existing_ext_ids)

        # Step 4 — atomic save: write to a temp file first, then rename.
        # os.replace is atomic at the OS level; if the process dies before rename,
        # the original face_vault.index file remains untouched.
        tmp_path = str(self._path) + ".tmp"
        faiss.write_index(new_index, tmp_path)
        os.replace(tmp_path, str(self._path))

        self._index = new_index

    # What  : Internal helper used by rebuild_and_train.
    #         Walks every inverted list (cluster) of the IVF index and collects
    #         all stored vectors together with their external (user-assigned) IDs.
    #         IndexIVFFlat does NOT store vectors in a single flat array — they are
    #         scattered across nlist separate inverted lists, one per cluster.
    # Gets  : nothing (reads from self._index and self._ivf)
    # Returns: tuple (vecs, ext_ids)
    #          vecs    — float32 array of shape (N, 512)
    #          ext_ids — int64 array of shape (N,) with the original person IDs
    def _extract_all_vectors(self) -> tuple[np.ndarray, np.ndarray]:
        # id_map[internal_id] = external_id
        # IndexIDMap assigns internal sequential IDs (0, 1, 2 …) when add_with_ids
        # is called; id_map lets us translate them back to user-provided IDs.
        id_map = faiss.vector_to_array(self._index.id_map)

        invlists = self._ivf.invlists
        # code_size for IVFFlat = DIM * 4 bytes (raw float32, no compression)
        code_size = self._ivf.code_size

        all_vecs: list[np.ndarray] = []
        all_ext_ids: list[np.ndarray] = []

        for list_no in range(self._ivf.nlist):
            size = invlists.list_size(list_no)
            if size == 0:
                continue

            # rev_swig_ptr converts a raw C++ pointer into a numpy array.
            # get_ids  → int64 pointer  → array of internal sequential IDs
            # get_codes → uint8 pointer → raw bytes of the stored float32 vectors
            internal_ids = faiss.rev_swig_ptr(invlists.get_ids(list_no), size).copy()
            raw_codes = faiss.rev_swig_ptr(
                invlists.get_codes(list_no), size * code_size
            ).copy()

            # Reinterpret the raw bytes as float32 and reshape to (size, DIM)
            vecs = raw_codes.view(np.float32).reshape(size, DIM)

            all_vecs.append(vecs)
            all_ext_ids.append(id_map[internal_ids])

        if not all_vecs:
            return np.empty((0, DIM), dtype=np.float32), np.empty(0, dtype=np.int64)

        return (
            np.ascontiguousarray(np.vstack(all_vecs), dtype=np.float32),
            np.concatenate(all_ext_ids).astype(np.int64),
        )
