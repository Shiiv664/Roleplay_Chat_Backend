"""Integration tests for character avatar upload functionality."""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image


class TestCharacterAvatarUpload:
    """Test character avatar upload functionality."""

    def create_test_image(
        self, filename: str = "test.png", size: tuple = (100, 100)
    ) -> io.BytesIO:
        """Create a test image file in memory."""
        img = Image.new("RGB", size, color="red")
        img_io = io.BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)
        return img_io

    def test_create_character_with_json_only(self, client):
        """Test creating a character with JSON data only (no file upload)."""
        import time

        unique_label = f"test_char_json_{int(time.time() * 1000)}"
        character_data = {
            "label": unique_label,
            "name": "Test Character",
            "description": "A test character",
            "avatar_image": "https://example.com/avatar.jpg",
        }

        response = client.post(
            "/api/v1/characters/",
            json=character_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label
        assert data["data"]["avatar_image"] == "https://example.com/avatar.jpg"
        assert data["data"]["avatar_url"] == "https://example.com/avatar.jpg"

    def test_create_character_with_multipart_without_file(self, client):
        """Test creating a character with multipart form data but no file."""
        import time

        unique_label = f"test_char_multipart_{int(time.time() * 1000)}"
        response = client.post(
            "/api/v1/characters/",
            data={
                "label": unique_label,
                "name": "Test Character Multipart",
                "description": "A test character with multipart form",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label
        assert data["data"]["avatar_image"] is None
        assert data["data"]["avatar_url"] is None

    def test_create_character_with_file_upload(self, client):
        """Test creating a character with file upload."""
        import time

        unique_label = f"test_char_upload_{int(time.time() * 1000)}"
        # Create a test image
        test_image = self.create_test_image()

        response = client.post(
            "/api/v1/characters/",
            data={
                "label": unique_label,
                "name": "Test Character Upload",
                "description": "A test character with uploaded avatar",
                "avatar_image": (test_image, "test_avatar.png"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label

        # Check that avatar_image is a local path
        avatar_image = data["data"]["avatar_image"]
        assert avatar_image is not None
        assert avatar_image.startswith("avatars/")
        assert avatar_image.endswith(".png")

        # Check that avatar_url is an uploads URL
        avatar_url = data["data"]["avatar_url"]
        assert avatar_url is not None
        assert avatar_url.startswith("/uploads/avatars/")
        assert avatar_url.endswith(".png")

    def test_create_character_multipart_missing_required_fields(self, client):
        """Test creating a character with multipart form but missing required fields."""
        test_image = self.create_test_image()

        # Missing name field
        response = client.post(
            "/api/v1/characters/",
            data={
                "label": "test_char_invalid",
                "description": "Missing name field",
                "avatar_image": (test_image, "test_avatar.png"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 400

    def test_create_character_with_large_file(self, client):
        """Test creating a character with a large image file."""
        import time

        unique_label = f"test_char_large_{int(time.time() * 1000)}"
        # Create a large test image
        large_image = self.create_test_image(size=(3000, 3000))

        response = client.post(
            "/api/v1/characters/",
            data={
                "label": unique_label,
                "name": "Test Character Large",
                "avatar_image": (large_image, "large_avatar.png"),
            },
            content_type="multipart/form-data",
        )

        # Should succeed and resize the image
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["avatar_image"] is not None

    def test_create_character_with_invalid_file_type(self, client):
        """Test creating a character with invalid file type."""
        import time

        unique_label = f"test_char_invalid_file_{int(time.time() * 1000)}"
        # Create a text file instead of an image
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            "/api/v1/characters/",
            data={
                "label": unique_label,
                "name": "Test Character Invalid File",
                "avatar_image": (text_file, "not_an_image.txt"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 400

    def test_avatar_url_generation_local_vs_external(self, client):
        """Test that avatar URLs are generated correctly for local vs external images."""
        import time

        unique_label_ext = f"char_external_{int(time.time() * 1000)}"
        unique_label_up = f"char_uploaded_{int(time.time() * 1000)}"

        # Test with external URL
        char_external = {
            "label": unique_label_ext,
            "name": "Character External",
            "avatar_image": "https://example.com/avatar.jpg",
        }

        response = client.post("/api/v1/characters/", json=char_external)
        assert response.status_code == 201
        data = response.get_json()
        assert data["data"]["avatar_url"] == "https://example.com/avatar.jpg"

        # Test with uploaded file
        test_image = self.create_test_image()
        response = client.post(
            "/api/v1/characters/",
            data={
                "label": unique_label_up,
                "name": "Character Uploaded",
                "avatar_image": (test_image, "uploaded_avatar.png"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        avatar_url = data["data"]["avatar_url"]
        assert avatar_url.startswith("/uploads/avatars/")
        assert (
            avatar_url != data["data"]["avatar_image"]
        )  # Should be different from stored path
