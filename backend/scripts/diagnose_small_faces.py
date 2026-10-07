"""Compare the same downloaded pictures at several face-size limits without changing server settings."""
import argparse
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
import requests
from src.app.ml.mtcnn_detector import MtcnnDetector
from src.app.ml.arcface_embedding import ArcFaceEmbedding
from src.core.services.candidate_comparison import compare_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--picture', required=True)
    parser.add_argument('--candidates', required=True, help='JSON array of link/picture_urls objects')
    parser.add_argument('--sizes', nargs='+', type=int, default=[64, 32, 20])
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if any(size <= 0 for size in args.sizes):
        parser.error('Face sizes must be positive')
    reference = cv2.imdecode(np.frombuffer(Path(args.picture).read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    if reference is None:
        parser.error('Reference image could not be decoded')
    reference = cv2.cvtColor(reference, cv2.COLOR_BGR2RGB)
    candidates = json.loads(Path(args.candidates).read_text(encoding='utf-8-sig'))
    detector, embedder = MtcnnDetector(), ArcFaceEmbedding()
    print('Reference face sizes:', [(f.face_width, f.face_height) for f in detector.detect_faces(reference, .5)], flush=True)
    cache = {}
    for candidate in candidates:
        for url in candidate.get('picture_urls', [])[:4]:
            if url in cache:
                continue
            try:
                response = requests.get(url, headers={'User-Agent': 'Face-Search-Engine/1.0 (educational project)'}, timeout=(10, 20))
                cache[url] = response
                response.raise_for_status()
                pixels = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR)
                faces = detector.detect_faces(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB), .5) if pixels is not None else []
                print(candidate['link'], 'image=', pixels.shape[:2] if pixels is not None else None,
                      'faces=', [(f.face_width, f.face_height) for f in faces], flush=True)
            except requests.RequestException as failure:
                cache[url] = failure
                print(candidate['link'], 'download failed:', type(failure).__name__, flush=True)

    def cached_get(url, **kwargs):
        response = cache[url]
        if isinstance(response, Exception):
            raise response
        return response

    runs = {}
    with patch('src.core.services.candidate_comparison.requests.get', side_effect=cached_get):
        for size in args.sizes:
            result = compare_candidates(reference, candidates, detector, embedder, .5, size)
            runs[str(size)] = result
            scores = {row['link_to_post']: row['score'] for row in result['results']}
            for outcome in result['diagnostics']['candidate_outcomes']:
                print('Minimum', size, outcome['link'], outcome['status'], outcome.get('quality', ''),
                      'similarity=', scores.get(outcome['link']), flush=True)
    Path(args.output).write_text(json.dumps(runs, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
