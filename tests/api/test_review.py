import pytest


class TestReviewFlow:
    def test_get_suggestions(self, client, test_db):
        # Create a test blog post first
        post_response = client.post(
            "/api/posts/",
            json={
                "title": "Review Test Post",
                "content": "Testing review flow"
            }
        )
        assert post_response.status_code == 201
        
        # Get suggestions
        response = client.get("/api/review/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_get_pending_suggestions(self, client, test_db):
        response = client.get("/api/review/suggestions/pending")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_approve_suggestion(self, client, test_db):
        # First get a pending suggestion
        response = client.get("/api/review/suggestions/pending")
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            if suggestions:
                suggestion_id = suggestions[0]["id"]
                approve_response = client.post(
                    f"/api/review/suggestions/{suggestion_id}/approve?reviewer=test_user"
                )
                assert approve_response.status_code == 200

    def test_reject_suggestion(self, client, test_db):
        response = client.get("/api/review/suggestions/pending")
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            if suggestions:
                suggestion_id = suggestions[0]["id"]
                reject_response = client.post(
                    f"/api/review/suggestions/{suggestion_id}/reject?reviewer=test_user"
                )
                assert reject_response.status_code == 200

    def test_review_stats(self, client, test_db):
        response = client.get("/api/review/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_suggestions" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
