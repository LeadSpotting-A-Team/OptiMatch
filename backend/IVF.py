import json
import os
from pathlib import Path
from typing import List, Optional
import faiss
import numpy as np
import time
import config as _cfg  # private alias — avoids polluting the public module namespace

# ── Constants ─────────────────────────────────────────────────────────────────

# ArcFace produces 512-dimensional embeddings
DIM = 512

# Single source of truth for the default cluster count (points to config).
_DEFAULT_NLIST: int = _cfg.IVF_DEFAULT_NLIST

# Default file paths
INDEX_PATH = "face_vault.index"
MAP_PATH   = "face_vault.map.json"

# Kept for backward compatibility: simple_main.py references IVF.MINIMUM_TRAINING_DATA_SIZE.
MINIMUM_TRAINING_DATA_SIZE = _DEFAULT_NLIST * 39

# ── Module-level helpers (private) ────────────────────────────────────────────


# Create a new trained IndexIVFFlat wrapped in an IndexIDMap.
# Uses nlist*40 random unit vectors as dummy training data so FAISS can initialise centroids.
def _make_trained_ivf(nlist: int) -> faiss.IndexIDMap:
    quantizer = faiss.IndexFlatIP(DIM)
    ivf = faiss.IndexIVFFlat(quantizer, DIM, nlist, faiss.METRIC_INNER_PRODUCT)

    # IVF must be trained before any vectors can be added.
    # We generate nlist*40 random unit vectors as a stand-in for real embeddings.
    rng = np.random.default_rng(42)
    dummy = rng.standard_normal((nlist * 40, DIM)).astype(np.float32)
    norms = np.linalg.norm(dummy, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0   # guard against zero-norm edge case
    dummy /= norms
    ivf.train(dummy)

    # Wrap the IVF inside IndexIDMap so we can use custom integer IDs
    # instead of FAISS's default sequential 0-based IDs.
    return faiss.IndexIDMap(ivf)


# Load the index from disk if it exists; otherwise create, train, and save a new one.
# nlist is only used when creating — an existing index already has its nlist baked in.
def _load_or_create_index(index_path: str, nlist: int) -> faiss.Index:
    if os.path.isfile(index_path):
        return faiss.read_index(index_path)

    index = _make_trained_ivf(nlist)
    faiss.write_index(index, index_path)
    return index


# ── Main class ────────────────────────────────────────────────────────────────

# FAISS wrapper for ArcFace embeddings (IndexIVFFlat + IndexIDMap).
# Metric : Inner Product (cosine similarity on unit vectors)
# IDs    : caller supplies a string face_id; internally a sequential int person_id is used.
#          _id_map[person_id] = face_id   (list, None for deleted slots)
#          _face_index[face_id] = person_id  (dict, reverse lookup)
# Both structures are saved to face_vault.map.json after every write.
class FaceVectorStore:

    # Load (or create) the index and map sidecar.
    # nlist priority: stored JSON → constructor arg → config.IVF_NLIST → _DEFAULT_NLIST.
    def __init__(
        self,
        index_path: str = INDEX_PATH,
        map_path: str = MAP_PATH,
        nlist: Optional[int] = None,
    ) -> None:
        self._path     = Path(index_path)
        self._map_path = Path(map_path)

        # Resolve nlist using the 4-step fallback chain before loading the index.
        # Priority 1: value persisted in the JSON sidecar (the index was already
        #             built with this nlist — loading a different value would
        #             cause subtle mismatches between nlist and the actual structure).
        stored_nlist = self._read_nlist_from_map()
        if stored_nlist is not None:
            self._nlist: int = stored_nlist
        elif nlist is not None:
            # Priority 2: caller-supplied constructor argument
            self._nlist = nlist
        elif _cfg.IVF_NLIST != _DEFAULT_NLIST:
            # Priority 3: config.IVF_NLIST only when it was explicitly overridden
            # (i.e. differs from the default), so a vanilla config doesn't shadow
            # an already-stored value when we still fall through to priority 4.
            self._nlist = _cfg.IVF_NLIST
        else:
            # Priority 4: hardcoded default — final fallback
            self._nlist = _DEFAULT_NLIST

        self._index: faiss.Index = _load_or_create_index(str(self._path), self._nlist)
        self._load_map()

    # ── ID-mapping helpers ────────────────────────────────────────────────────

    # Read only the "nlist" key from the JSON sidecar.
    # Returns None if the file is missing (fresh store), _DEFAULT_NLIST if the key
    # is absent (legacy index — backward compat), or the stored int if present.
    def _read_nlist_from_map(self) -> Optional[int]:
        if not self._map_path.is_file():
            # No sidecar at all — this is a fresh store, not a legacy one.
            return None
        try:
            data: dict = json.loads(self._map_path.read_text(encoding="utf-8"))
            value = data.get("nlist")
            if value is not None:
                return int(value)
            # File exists but key is absent → legacy index; pin to default.
            return _DEFAULT_NLIST
        except (json.JSONDecodeError, ValueError):
            # Corrupt or unreadable JSON — fall back to default for safety.
            return _DEFAULT_NLIST

    # Load id_map list from JSON and rebuild the reverse face_index dict.
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

    # Atomically write nlist + id_map to JSON (temp file → rename).
    def _save_map(self) -> None:
        tmp = str(self._map_path) + ".tmp"
        # Persist nlist alongside id_map so that the next load always uses the
        # same nlist the index was built with, regardless of config changes.
        Path(tmp).write_text(
            json.dumps({"nlist": self._nlist, "id_map": self._id_map}),
            encoding="utf-8",
        )
        os.replace(tmp, str(self._map_path))

    # Append face_id to _id_map and return its new sequential person_id.
    def _register(self, face_id: str) -> int:
        if face_id in self._face_index:
            raise ValueError(f"face_id '{face_id}' already exists in the index.")
        person_id = len(self._id_map)
        self._id_map.append(face_id)
        self._face_index[face_id] = person_id
        return person_id

    # Mark face_id slot as None in _id_map and remove it from the reverse dict.
    def _unregister(self, face_id: str) -> int:
        if face_id not in self._face_index:
            raise KeyError(f"face_id '{face_id}' not found in the index.")
        person_id = self._face_index.pop(face_id)
        self._id_map[person_id] = None      # keep list length stable; slot is dead
        return person_id

    # Unwrap IndexIDMap to reach the inner IndexIVFFlat (needed for nprobe and invlists).
    @property
    def _ivf(self) -> faiss.IndexIVFFlat:
        return faiss.downcast_index(self._index.index)

    # ── Public configuration properties ───────────────────────────────────────

    # Number of Voronoi clusters this index was built with.
    @property
    def nlist(self) -> int:
        return self._nlist

    # Minimum vectors needed to train: FAISS requires at least 39 × nlist.
    @property
    def min_training_size(self) -> int:
        return self._nlist * 39

    # ── Write operations ──────────────────────────────────────────────────────

    # Add one embedding + face_id and save both index and map to disk.
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

    # Add N embeddings in one FAISS call and save once.
    # Retries _save_map on PermissionError (Windows file-lock protection).
    def add_faces_batch(
        self,
        embeddings: np.ndarray,
        face_ids: List[str],
        save_retries: int = 3,
    ) -> None:
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

        for attempt in range(save_retries):
            try:
                self._save_map()
                break
            except PermissionError:
                if attempt == save_retries - 1:
                    raise
                time.sleep(0.25)

    # Remove a face by face_id and save both index and map to disk.
    def delete_face(self, face_id: str) -> None:
        person_id = self._unregister(face_id)

        # IndexIDMap.remove_ids accepts a numpy int64 array directly;
        # internally FAISS wraps it in an IDSelectorBatch.
        self._index.remove_ids(np.array([person_id], dtype=np.int64))
        faiss.write_index(self._index, str(self._path))
        self._save_map()

    # ── Read operations ───────────────────────────────────────────────────────

    # Return top-k nearest faces for a query embedding.
    # nprobe controls accuracy vs. speed: higher = more clusters scanned.
    def search_face(
        self, query_embedding: np.ndarray, k: int = 5, nprobe: int = 5
    ) -> List[dict]:

        start_time = time.time() * 1000  # milliseconds

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
        end_time = time.time() * 1000  # milliseconds
        debug_file = os.path.join("sandbox", "debug", "search_time.txt")
        os.makedirs(os.path.dirname(debug_file), exist_ok=True)
        with open(debug_file, "a") as f:
            f.write(f"Search time: {end_time - start_time} milliseconds , nprobe: {nprobe} , k: {k}\n")

        return [
            {
                "face_id": self._id_map[int(labels[0, j])],
                "score": float(scores[0, j]),
            }
            for j in range(k)
            if labels[0, j] >= 0
        ]

    # Return total number of stored vectors.
    def get_total_count(self) -> int:
        return int(self._index.ntotal)

    # Return all stored vectors as a float32 array of shape (N, 512).
    def get_all_embeddings(self) -> np.ndarray:
        vecs, _ = self._extract_all_vectors()
        return vecs

    # ── Maintenance ───────────────────────────────────────────────────────────

    # Retrain the index on real data. Optionally change nlist at the same time.
    # All existing vectors are preserved and re-inserted with their original person_ids.
    def rebuild_and_train(
        self,
        new_training_data: np.ndarray,
        new_nlist: Optional[int] = None,
    ) -> None:
        # Decide which nlist to use for the rebuilt index.
        # Keeping new_nlist separate from self._nlist until after a successful
        # rebuild ensures the instance stays consistent if anything goes wrong.
        effective_nlist = new_nlist if new_nlist is not None else self._nlist

        train = np.ascontiguousarray(
            np.asarray(new_training_data, dtype=np.float32).reshape(-1, DIM)
        )

        min_required = effective_nlist * 39
        if train.shape[0] < min_required:
            raise ValueError(
                f"Training data needs at least {min_required} vectors "
                f"(39 × nlist={effective_nlist}); got {train.shape[0]}"
            )

        # Step 1 — snapshot all vectors and their person_ids before touching the index.
        # The returned person_ids are the original sequential integers, which are the
        # direct indices into _id_map — no mapping update is required after rebuild.
        existing_vecs, existing_person_ids = self._extract_all_vectors()

        # Step 2 — build a fresh IVF and train it on the real data distribution
        quantizer = faiss.IndexFlatIP(DIM)
        ivf = faiss.IndexIVFFlat(quantizer, DIM, effective_nlist, faiss.METRIC_INNER_PRODUCT)
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

        # Commit the (possibly new) nlist and persist both files in sync.
        # This must happen after the successful write above so that if write_index
        # raises, _nlist and the JSON sidecar remain unchanged.
        self._nlist = effective_nlist
        self._save_map()

    # Walk all IVF inverted lists and collect every stored vector + its person_id.
    # IndexIVFFlat scatters vectors across nlist separate lists, not a flat array.
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
