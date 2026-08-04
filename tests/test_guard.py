import pytest
from app.services.guard_service import guard


class TestMismatchGuard:
    def test_similarity_check(self):
        # Test similarity threshold
        passed, reason = guard.check_similarity(0.8, 0.5)
        assert passed is True
        assert "meets threshold" in reason
        
        passed, reason = guard.check_similarity(0.3, 0.5)
        assert passed is False
        assert "below threshold" in reason

    def test_subject_match(self):
        # Test subject matching
        passed, reason = guard.check_subject_match("Red Fox", "Red Fox")
        assert passed is True
        assert "matches exactly" in reason
        
        passed, reason = guard.check_subject_match("Red Fox", "Fox")
        assert passed is True
        assert "share common words" in reason
        
        passed, reason = guard.check_subject_match("Red Fox", "Wolf")
        assert passed is False
        assert "Subject mismatch" in reason

    def test_confidence_check(self):
        # Test confidence threshold
        passed, reason = guard.check_confidence(0.9, 0.7)
        assert passed is True
        
        passed, reason = guard.check_confidence(0.5, 0.7)
        assert passed is False
        assert "below minimum" in reason

    def test_category_match(self):
        # Test category matching
        passed, reason = guard.check_category_match("animal", "animal")
        assert passed is True
        
        passed, reason = guard.check_category_match("animal", "vehicle")
        assert passed is False
        assert "Category mismatch" in reason
