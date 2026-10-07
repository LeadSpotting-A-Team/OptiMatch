"""Direct comparison, independent of candidate discovery. No persistence."""
import cv2
import numpy as np
import requests
from urllib.parse import urlparse


def compare_candidates(image, candidates, detector, embedder, min_confidence, min_size):
    from src.core.services.harvesting_service import harvest_faces_from_image
    from src.core.services.embedding_service import compute_similarity

    def embeddings(pixels):
        faces = harvest_faces_from_image(pixels, detector, min_confidence, min_size)
        return [embedder.compute_embedding(embedder.preprocess(face)) for face in faces]

    query = embeddings(image)
    query_detections = detector.detect_faces(image, min_confidence)
    usable_query = [face for face in query_detections if face.face_width >= min_size and face.face_height >= min_size]
    query_quality = (len(usable_query) == 1 and usable_query[0].face_width >= 64 and usable_query[0].face_height >= 64)
    results, outcomes = [], []
    for candidate in candidates:
        outcome = {"link": candidate["link"], "status": "MISSING_PICTURE", "attempts": []}
        outcomes.append(outcome)
        if len(query) != 1:
            outcome["status"] = "NO_QUERY_FACE" if not query else "MULTIPLE_QUERY_FACES"
            continue
        best = None
        urls = list(dict.fromkeys(candidate.get("picture_urls", [])))[:4]
        for url in urls:
            attempt = {"status": "PICTURE_LOAD_FAILED"}
            outcome["attempts"].append(attempt)
            try:
                if urlparse(url).scheme not in ("http", "https"):
                    raise ValueError("Invalid picture URL")
                response = requests.get(url, headers={"User-Agent": "Face-Search-Engine/1.0 (educational project)"}, timeout=(10, 20))
                attempt["http_status"] = response.status_code
                response.raise_for_status()
                pixels = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR)
                if pixels is None:
                    raise ValueError("Invalid image")
                rgb = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)
                detected = detector.detect_faces(rgb, min_confidence)
                usable = [face for face in detected if face.face_width >= min_size and face.face_height >= min_size]
                if not usable:
                    attempt["status"] = "FACE_TOO_SMALL" if detected else "NO_CANDIDATE_FACE"
                    continue
                if len(usable) > 1:
                    attempt["status"] = "MULTIPLE_CANDIDATE_FACES"
                    continue
                attempt["status"] = "EMBEDDING_FAILED"
                candidate_vectors = embeddings(rgb)
                if not candidate_vectors:
                    continue
                score = max(compute_similarity(query[0], vector) for vector in candidate_vectors)
                attempt["status"] = "COMPARED"
                if best is None or score > best:
                    best = score
                    outcome["face_width"] = usable[0].face_width
                    outcome["face_height"] = usable[0].face_height
            except (requests.RequestException, ValueError, TypeError):
                pass
            except Exception:
                attempt["status"] = "EMBEDDING_FAILED"
        if best is not None:
            outcome["status"] = "COMPARED"
            outcome["quality"] = "USABLE" if query_quality and min(outcome["face_width"], outcome["face_height"]) >= 64 else "SMALL_FACE"
            results.append({"link_to_post": candidate["link"], "score": float(best)})
        elif outcome["attempts"]:
            outcome["status"] = outcome["attempts"][-1]["status"]
    return {"query_faces": [None] * len(query), "results": results,
            "diagnostics": {"candidate_profiles": len(candidates), "comparisons": len(results),
                            "candidate_outcomes": outcomes}, "message": "CANDIDATES_COMPARED"}
