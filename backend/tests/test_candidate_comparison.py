import sys
import types
import unittest
from unittest.mock import Mock, patch
import numpy as np
from src.core.services.candidate_comparison import compare_candidates


class CandidateComparisonTest(unittest.TestCase):
    def run_compare(self, rows, harvest, responses, face_size=90):
        detector = Mock()
        detector.detect_faces.return_value = [types.SimpleNamespace(face_width=face_size, face_height=100)]
        model = Mock()
        model.compute_embedding.return_value = np.array([1.0])
        harvesting = types.ModuleType('src.core.services.harvesting_service')
        harvesting.harvest_faces_from_image = Mock(side_effect=harvest)
        similarity = types.ModuleType('src.core.services.embedding_service')
        similarity.compute_similarity = Mock(return_value=.2)
        with patch.dict(sys.modules, {harvesting.__name__: harvesting, similarity.__name__: similarity}), \
             patch('src.core.services.candidate_comparison.requests.get', side_effect=responses), \
             patch('src.core.services.candidate_comparison.cv2.imdecode', return_value=np.zeros((100,100,3),dtype=np.uint8)):
            return compare_candidates(np.zeros((100,100,3)),rows,detector,model,.5,64)

    def response(self):
        return Mock(status_code=200, content=b'image')

    def test_fallback_and_below_threshold(self):
        import requests
        result = self.run_compare([{'link':'https://linkedin.com/in/person','picture_urls':['https://image/old','https://image/new']}],
                                  [[Mock()],[Mock()]],[requests.HTTPError('403'), self.response()])
        self.assertEqual(.2,result['results'][0]['score'])
        self.assertEqual('COMPARED',result['diagnostics']['candidate_outcomes'][0]['status'])
        self.assertEqual('USABLE',result['diagnostics']['candidate_outcomes'][0]['quality'])
        print('PASS: failed first picture falls back; below-threshold similarity is returned.')

    def test_small_face(self):
        result = self.run_compare([{'link':'https://linkedin.com/in/person','picture_urls':['https://image/small']}],[[Mock()]],[self.response()],14)
        self.assertEqual([],result['results'])
        self.assertEqual('FACE_TOO_SMALL',result['diagnostics']['candidate_outcomes'][0]['status'])
        print('PASS: small face reports inability to compare, not a mismatch.')

    def test_missing_picture(self):
        result = self.run_compare([{'link':'https://linkedin.com/in/person','picture_urls':[]}],[[Mock()]],[])
        self.assertEqual('MISSING_PICTURE',result['diagnostics']['candidate_outcomes'][0]['status'])

    def test_ambiguous_query(self):
        result = self.run_compare([{'link':'https://linkedin.com/in/person','picture_urls':['https://image/picture']}],[[Mock(),Mock()]],[])
        self.assertEqual('MULTIPLE_QUERY_FACES',result['diagnostics']['candidate_outcomes'][0]['status'])
        print('PASS: multiple query faces require review; no arbitrary person is selected.')


if __name__ == '__main__':
    unittest.main()
