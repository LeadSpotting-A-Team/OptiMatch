from src.core.entities.SocialProfile import SocialProfile
from src.core.io.files_loader import load_image_or_video
from src.core.io.leedspoting_api import get_profiles_from_api, get_profiles_count_from_api
from src.core.io.url_loader import download_to_temp_file
from src.core.services.harvesting_service import harvest_faces_from_frames
import numpy as np
from src.core.services.embedding_service import compute_similarity
from src.app.config import FACE_CONFIDENCE_THRESHOLD
from src.core.services.face_detection_service import IFaceDetector
from src.core.services.embedding_service import IEmbeddingModel
from src.app.config import DOWNLOAD_DIR
from concurrent.futures import ThreadPoolExecutor, as_completed


def search_api(
    target_first_name: str,
    target_last_name: str,
    target_frames_rgb: np.ndarray,
    detector: IFaceDetector,
    embedding_model: IEmbeddingModel,
    similarity_threshold: float = FACE_CONFIDENCE_THRESHOLD,
) -> list[tuple[SocialProfile, float]]:

    if get_profiles_count_from_api(target_first_name, target_last_name) == 0:
        return []

    profiles = get_profiles_from_api(target_first_name, target_last_name)

    embedding_profile_pairs: list[tuple[np.ndarray, SocialProfile]] = []

    def _download_and_load(profile: SocialProfile):
        file_path = download_to_temp_file(profile.get_all_images_links()[0], DOWNLOAD_DIR)
        frames = load_image_or_video(file_path)
        return profile, frames

    # Download and load images in parallel using threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_download_and_load, p) for p in profiles]
        loaded: list[tuple[SocialProfile, np.ndarray]] = []
        for future in as_completed(futures):
            try:
                loaded.append(future.result())
            except Exception:
                pass

    # Process sequentially: face detection and embedding computation
    for profile, frames in loaded:
        try:
            cropped_faces = harvest_faces_from_frames(frames, detector)
            for cf in cropped_faces:
                emb = embedding_model.compute_embedding(embedding_model.preprocess(cf))
                embedding_profile_pairs.append((emb, profile))
        except Exception:
            pass

    # Compute embeddings for the target query image.
    target_embeddings = []
    for frame in target_frames_rgb:
        cropped_faces = harvest_faces_from_frames(frame, detector)
        if len(cropped_faces) == 0:
            continue
        for cf in cropped_faces:
            embedding = embedding_model.compute_embedding(embedding_model.preprocess(cf))
            target_embeddings.append(embedding)

    # Keep the best similarity score per profile (by object identity).
    best_scores: dict[int, tuple[SocialProfile, float]] = {}
    for target_emb in target_embeddings:
        for profile_emb, profile in embedding_profile_pairs:
            similarity_score = compute_similarity(target_emb, profile_emb)
            if similarity_score >= similarity_threshold:
                pid = id(profile)
                if pid not in best_scores or similarity_score > best_scores[pid][1]:
                    best_scores[pid] = (profile, similarity_score)

    sorted_results = sorted(best_scores.values(), key=lambda x: x[1], reverse=True)
    return sorted_results
