from __future__ import annotations

import numpy as np

from src.core.entities.cropped_face import CroppedFace
from src.core.interfaces.i_embedding_model import IEmbeddingModel


# Generates a 512-dimensional embedding vector for the given face crop using
# the provided embedding model.
# Returns None when the crop is invalid (missing image data) so callers can
# skip bad inputs without catching exceptions.
def compute_embedding(
    cropped_face: CroppedFace,
    model: IEmbeddingModel,
) -> np.ndarray | None:
    if cropped_face is None or cropped_face.get_image() is None:
        return None

    aligned_image = model.preprocess(cropped_face)
    return model.compute_embedding(aligned_image)


# Computes the cosine similarity between two L2-normalised embedding vectors.
# Both embeddings must have dimension 512.
# Returns a float in [0.0, 1.0] where 1.0 means identical faces.
def compute_similarity(
    embedding_a: np.ndarray,
    embedding_b: np.ndarray,
) -> float:
    similarity = np.dot(embedding_a, embedding_b)
    return float(np.clip(similarity, 0.0, 1.0))


# Finds all embeddings in database_matrix whose similarity to query_embedding
# exceeds the given threshold.
# Returns a list of (index, score) tuples sorted by score descending.
def find_matches_above_threshold(
    query_embedding: np.ndarray,
    database_matrix: np.ndarray,
    threshold: float,
) -> list[tuple[int, float]]:
    query_vec = np.array(query_embedding, dtype="float32").flatten()
    similarities = np.dot(database_matrix, query_vec)
    matched_indices = np.where(similarities > threshold)[0]
    matches = [(int(idx), float(similarities[idx])) for idx in matched_indices]
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches
