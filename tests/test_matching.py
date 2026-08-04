import pytest
from app.services.matching_service import matching_service


class TestMatching:
    def test_cosine_similarity(self):
        # Test cosine similarity calculation
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        similarity = matching_service.cosine_similarity(vec_a, vec_b)
        assert similarity == 1.0
        
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        similarity = matching_service.cosine_similarity(vec_a, vec_b)
        assert similarity == 0.0
        
        vec_a = [1.0, 1.0, 0.0]
        vec_b = [1.0, 0.0, 1.0]
        similarity = matching_service.cosine_similarity(vec_a, vec_b)
        assert 0.4 < similarity < 0.6

    def test_empty_vectors(self):
        similarity = matching_service.cosine_similarity([], [])
        assert similarity == 0.0
        
        similarity = matching_service.cosine_similarity([1.0], [])
        assert similarity == 0.0

    def test_similarity_ranking(self, client, test_db):
        # Test that similarity scores are properly ranked
        response = client.get("/api/matching/posts/1/matches?top_k=3")
        if response.status_code == 200:
            data = response.json()
            if data.get("matches"):
                matches = data["matches"]
                # Check that scores are in descending order
                scores = [m["similarity_score"] for m in matches]
                assert scores == sorted(scores, reverse=True)
