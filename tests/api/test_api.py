import pytest
from fastapi.testclient import TestClient


class TestAPI:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "AI Image Understanding" in data["service"]

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_upload_image(self, client, test_db):
        # Test image upload
        import io
        from PIL import Image
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        response = client.post("/api/images/upload", files=files)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.jpg"

    def test_list_images(self, client, test_db):
        response = client.get("/api/images/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_blog_post(self, client, test_db):
        response = client.post(
            "/api/posts/",
            json={
                "title": "Test Blog Post",
                "content": "This is a test blog post for testing purposes."
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Blog Post"
        assert "id" in data

    def test_list_blog_posts(self, client, test_db):
        response = client.get("/api/posts/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
