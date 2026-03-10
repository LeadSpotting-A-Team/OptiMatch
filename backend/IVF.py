import json
import os
from pathlib import Path
from typing import List, Optional
import faiss
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

# ArcFace produces 512-dimensional embeddings
DIM = 512

# Number of Voronoi clusters (cells) the index is divided into.
# FAISS recommendation: nlist ≈ sqrt(N) for N vectors.
# 4000 is optimized for datasets of 1M+ vectors.
NLIST = 100

# Default paths for the index file and its ID-mapping sidecar
INDEX_PATH = "face_vault.index"
MAP_PATH   = "face_vault.map.json"


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
    dummy = rng.standard_normal((NLIST * 40, DIM)).astype(np.float32)
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
    ID support : IndexIDMap    (sequential integer person_ids — hidden from the caller)
    Persistence: index + ID-mapping JSON are saved to disk after every write

    ID design
    ─────────
    The caller supplies a string `face_id`.  Internally we assign a sequential
    integer `person_id` (0, 1, 2 …) which FAISS stores via add_with_ids.

    The mapping is a plain list:

        _id_map[person_id] = face_id   # None for deleted slots

    This makes the "FAISS int → face_id" lookup a pure list index — O(1) with
    zero hashing overhead.  A companion dict provides the reverse direction:

        _face_index[face_id] = person_id   # O(1) reverse lookup

    Both structures are persisted to a JSON sidecar (face_vault.map.json) so
    they reload in sync with the FAISS index on every restart.
    """

    # What  : Loads the index and the ID-mapping sidecar from disk if they exist;
    #         otherwise initialises fresh empty structures.
    # Gets  : index_path — path to the .index file (default: face_vault.index)
    #         map_path   — path to the .map.json sidecar (default: face_vault.map.json)
    # Returns: nothing
    def __init__(
        self,
        index_path: str = INDEX_PATH,
        map_path: str = MAP_PATH,
    ) -> None:
        self._path     = Path(index_path)
        self._map_path = Path(map_path)
        self._index: faiss.Index = _load_or_create_index(str(self._path))
        self._load_map()

    # ── ID-mapping helpers ────────────────────────────────────────────────────

    # What  : Populates _id_map and _face_index from the JSON sidecar.
    #         If the file does not exist yet, starts with empty structures.
    # Gets  : nothing (reads self._map_path)
    # Returns: nothing
    def _load_map(self) -> None:
        if self._map_path.is_file():
            data: dict = json.loads(self._map_path.read_text(encoding="utf-8"))
            # _id_map is a list; JSON "null" becomes Python None for deleted slots.
            self._id_map: list[Optional[str]] = data["id_map"]
        else:
            self._id_map = []

        # Rebuild the reverse dict at startup — never persisted separately.
        # Skips None slots so deleted entries are excluded automatically.
        self._face_index: dict[str, int] = {
            face_id: person_id
            for person_id, face_id in enumerate(self._id_map)
            if face_id is not None
        }

    # What  : Writes _id_map to the JSON sidecar atomically (temp + rename).
    #         Called immediately after every faiss.write_index so both files
    #         always stay in sync.
    # Gets  : nothing
    # Returns: nothing
    def _save_map(self) -> None:
        tmp = str(self._map_path) + ".tmp"
        Path(tmp).write_text(
            json.dumps({"id_map": self._id_map}), encoding="utf-8"
        )
        os.replace(tmp, str(self._map_path))

    # What  : Appends a new face_id to _id_map and updates the reverse dict.
    #         The new person_id is simply len(_id_map) before the append —
    #         equivalent to the next available array index.
    # Gets  : face_id — caller-supplied string identifier; must be unique
    # Returns: the newly assigned person_id (int)
    def _register(self, face_id: str) -> int:
        if face_id in self._face_index:
            raise ValueError(f"face_id '{face_id}' already exists in the index.")
        person_id = len(self._id_map)
        self._id_map.append(face_id)
        self._face_index[face_id] = person_id
        return person_id

    # What  : Marks a slot in _id_map as deleted (sets it to None) and removes
    #         the face_id from the reverse dict.
    # Gets  : face_id — caller-supplied identifier to remove
    # Returns: the person_id (int) that was freed (needed for FAISS removal)
    def _unregister(self, face_id: str) -> int:
        if face_id not in self._face_index:
            raise KeyError(f"face_id '{face_id}' not found in the index.")
        person_id = self._face_index.pop(face_id)
        self._id_map[person_id] = None      # keep list length stable; slot is dead
        return person_id

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
    # Gets  : embedding — 1-D numpy array of shape (512,), already L2-normalised
    #         face_id   — unique string identifier for this face
    # Returns: nothing
    def add_face(self, embedding: np.ndarray, face_id: str) -> None:
        vec = np.asarray(embedding, dtype=np.float32).flatten()

        if vec.shape[0] != DIM:
            raise ValueError(f"Embedding must have dimension {DIM}, got {vec.shape[0]}")
        if not self._index.is_trained:
            raise RuntimeError("Index is not trained; cannot add vectors.")

        # person_id is assigned here — it equals the current length of _id_map,
        # i.e. the next free sequential slot.
        person_id = self._register(face_id)
        self._index.add_with_ids(
            vec.reshape(1, -1),
            np.array([person_id], dtype=np.int64),
        )
        faiss.write_index(self._index, str(self._path))
        self._save_map()

    # What  : Adds many face embeddings to the index in a single FAISS call,
    #         then saves to disk once.  Preferred over calling add_face in a loop
    #         because the write_index cost is paid only once.
    # Gets  : embeddings — 2-D numpy array of shape (N, 512), L2-normalised rows
    #         face_ids   — list of N unique string identifiers (one per embedding)
    # Returns: nothing
    def add_faces_batch(self, embeddings: np.ndarray, face_ids: List[str]) -> None:
        # ascontiguousarray ensures the memory layout is C-contiguous,
        # which FAISS requires — slices of larger arrays can be non-contiguous.
        vecs = np.ascontiguousarray(
            np.asarray(embeddings, dtype=np.float32).reshape(-1, DIM)
        )

        if vecs.shape[0] != len(face_ids):
            raise ValueError(
                f"Number of embeddings ({vecs.shape[0]}) must match "
                f"number of face_ids ({len(face_ids)})"
            )
        if vecs.shape[1] != DIM:
            raise ValueError(
                f"Each embedding must have dimension {DIM}, got {vecs.shape[1]}"
            )
        if not self._index.is_trained:
            raise RuntimeError("Index is not trained; cannot add vectors.")

        # Register all face_ids before touching FAISS so a duplicate raises
        # immediately and leaves the index in a consistent state.
        person_ids = np.array(
            [self._register(fid) for fid in face_ids], dtype=np.int64
        )
        self._index.add_with_ids(vecs, person_ids)
        faiss.write_index(self._index, str(self._path))
        self._save_map()

    # What  : Removes a single face from the index by its face_id, then saves.
    # Gets  : face_id — the string identifier that was used when adding the face
    # Returns: nothing
    def delete_face(self, face_id: str) -> None:
        person_id = self._unregister(face_id)

        # IndexIDMap.remove_ids accepts a numpy int64 array directly;
        # internally FAISS wraps it in an IDSelectorBatch.
        self._index.remove_ids(np.array([person_id], dtype=np.int64))
        faiss.write_index(self._index, str(self._path))
        self._save_map()

    # ── Read operations ───────────────────────────────────────────────────────

    # What  : Searches the index for the K nearest neighbours of a query embedding.
    #         nprobe controls the accuracy/speed trade-off: higher = more accurate
    #         but slower (scans more clusters).
    # Gets  : query_embedding — 1-D numpy array of shape (512,), L2-normalised
    #         k              — number of top results to return (default 5)
    #         nprobe         — how many IVF clusters to scan per query (default 20)
    # Returns: list of dicts sorted by score descending, e.g.
    #          [{"face_id": "abc123", "score": 0.97}, ...]
    #          An empty list is returned when the index contains no vectors.
    def search_face(
        self, query_embedding: np.ndarray, k: int = 5, nprobe: int = 20
    ) -> List[dict]:
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

        # labels[0, j] == -1 means FAISS found no match for that slot (sparse index).
        # person_id is the direct index into _id_map — O(1) list lookup.
        return [
            {
                "face_id": self._id_map[int(labels[0, j])],
                "score": float(scores[0, j]),
            }
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
    #         is rebuilt with the new centroids, and they are re-inserted with
    #         the same person_ids so _id_map stays valid without any changes.
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

        # Step 1 — snapshot all vectors and their person_ids before touching the index.
        # The returned person_ids are the original sequential integers, which are the
        # direct indices into _id_map — no mapping update is required after rebuild.
        existing_vecs, existing_person_ids = self._extract_all_vectors()

        # Step 2 — build a fresh IVF and train it on the real data distribution
        quantizer = faiss.IndexFlatIP(DIM)
        ivf = faiss.IndexIVFFlat(quantizer, DIM, NLIST, faiss.METRIC_INNER_PRODUCT)
        ivf.train(train)
        new_index = faiss.IndexIDMap(ivf)

        # Step 3 — re-insert all previously stored faces with their original person_ids.
        # Because person_ids are unchanged, _id_map remains correct with no edits.
        if existing_vecs.shape[0] > 0:
            new_index.add_with_ids(existing_vecs, existing_person_ids)

        # Step 4 — atomic save: write to a temp file first, then rename.
        # os.replace is atomic at the OS level; if the process dies before rename,
        # the original face_vault.index file remains untouched.
        tmp_path = str(self._path) + ".tmp"
        faiss.write_index(new_index, tmp_path)
        os.replace(tmp_path, str(self._path))

        self._index = new_index
        # _id_map is unchanged — no _save_map() call needed here.

    # What  : Internal helper used by rebuild_and_train.
    #         Walks every inverted list (cluster) of the IVF index and collects
    #         all stored vectors together with their person_ids (the sequential
    #         integers used as FAISS IDs).
    #         IndexIVFFlat does NOT store vectors in a single flat array — they are
    #         scattered across nlist separate inverted lists, one per cluster.
    # Gets  : nothing (reads from self._index and self._ivf)
    # Returns: tuple (vecs, person_ids)
    #          vecs       — float32 array of shape (N, 512)
    #          person_ids — int64 array of shape (N,) with the sequential IDs
    def _extract_all_vectors(self) -> tuple[np.ndarray, np.ndarray]:
        # id_map[internal_idx] = person_id
        # IndexIDMap maintains its own internal sequential positions; id_map
        # translates those back to the person_ids we stored via add_with_ids.
        id_map = faiss.vector_to_array(self._index.id_map)

        invlists = self._ivf.invlists
        # code_size for IVFFlat = DIM * 4 bytes (raw float32, no compression)
        code_size = self._ivf.code_size

        all_vecs: list[np.ndarray] = []
        all_person_ids: list[np.ndarray] = []

        for list_no in range(self._ivf.nlist):
            size = invlists.list_size(list_no)
            if size == 0:
                continue

            # rev_swig_ptr converts a raw C++ pointer into a numpy array.
            # get_ids   → int64 pointer → array of internal sequential positions
            # get_codes → uint8 pointer → raw bytes of the stored float32 vectors
            internal_ids = faiss.rev_swig_ptr(invlists.get_ids(list_no), size).copy()
            raw_codes = faiss.rev_swig_ptr(
                invlists.get_codes(list_no), size * code_size
            ).copy()

            # Reinterpret the raw bytes as float32 and reshape to (size, DIM)
            vecs = raw_codes.view(np.float32).reshape(size, DIM)

            all_vecs.append(vecs)
            all_person_ids.append(id_map[internal_ids])

        if not all_vecs:
            return np.empty((0, DIM), dtype=np.float32), np.empty(0, dtype=np.int64)

        return (
            np.ascontiguousarray(np.vstack(all_vecs), dtype=np.float32),
            np.concatenate(all_person_ids).astype(np.int64),
        )
