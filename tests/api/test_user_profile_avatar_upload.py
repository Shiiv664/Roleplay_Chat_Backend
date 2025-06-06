"""Test User Profile Avatar Upload functionality."""

import io
import time

from PIL import Image


class TestUserProfileAvatarUpload:
    """Test cases for user profile avatar upload functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.base_url = "/api/v1/user-profiles/"

    def create_test_image(self, size=(100, 100), format="PNG"):
        """Create a test image file."""
        img = Image.new("RGB", size, color="red")
        img_file = io.BytesIO()
        img.save(img_file, format=format)
        img_file.seek(0)
        return img_file

    def test_create_user_profile_with_avatar_upload(self, client, db_session):
        """Test user profile creation with avatar file upload."""
        # Create test image
        img_file = self.create_test_image()
        unique_label = f"test_user_with_avatar_{int(time.time() * 1000)}"

        # Create multipart form data
        response = client.post(
            self.base_url,
            data={
                "label": unique_label,
                "name": "Test User with Avatar",
                "description": "A test user with an uploaded avatar",
                "avatar_image": (img_file, "test.png"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label
        assert data["data"]["avatar_image"] is not None
        assert data["data"]["avatar_url"] is not None
        assert data["data"]["avatar_url"].startswith("/uploads/avatars/")

    def test_create_user_profile_multipart_without_file(self, client, db_session):
        """Test user profile creation with multipart form but no file."""
        unique_label = f"test_user_no_avatar_{int(time.time() * 1000)}"

        response = client.post(
            self.base_url,
            data={
                "label": unique_label,
                "name": "Test User No Avatar",
                "description": "A test user without avatar",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label
        assert data["data"]["avatar_image"] is None
        assert data["data"]["avatar_url"] is None

    def test_create_user_profile_json_mode_still_works(self, client, db_session):
        """Test that JSON mode still works after avatar upload implementation."""
        unique_label = f"test_user_json_{int(time.time() * 1000)}"

        response = client.post(
            self.base_url,
            json={
                "label": unique_label,
                "name": "Test User JSON",
                "description": "A test user created via JSON",
                "avatar_image": "https://example.com/avatar.png",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["label"] == unique_label
        assert data["data"]["avatar_image"] == "https://example.com/avatar.png"
        assert data["data"]["avatar_url"] == "https://example.com/avatar.png"

    def test_multipart_missing_required_fields(self, client, db_session):
        """Test validation error when required fields are missing in multipart form."""
        response = client.post(
            self.base_url,
            data={"description": "Missing label and name"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Label and name are required" in data["error"]["message"]

    def test_get_user_profile_includes_avatar_url(self, client, db_session):
        """Test that getting a user profile includes the avatar URL."""
        # First create a user profile with avatar
        img_file = self.create_test_image()
        unique_label = f"test_user_get_avatar_{int(time.time() * 1000)}"

        create_response = client.post(
            self.base_url,
            data={
                "label": unique_label,
                "name": "Test User Get Avatar",
                "avatar_image": (img_file, "test.png"),
            },
            content_type="multipart/form-data",
        )

        assert create_response.status_code == 201
        user_id = create_response.get_json()["data"]["id"]

        # Get the user profile
        response = client.get(f"{self.base_url}{user_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["avatar_image"] is not None
        assert data["data"]["avatar_url"] is not None
        assert data["data"]["avatar_url"].startswith("/uploads/avatars/")

    def test_list_user_profiles_includes_avatar_urls(self, client, db_session):
        """Test that listing user profiles includes avatar URLs."""
        # Create a user profile with avatar
        img_file = self.create_test_image()
        unique_label = f"test_user_list_avatar_{int(time.time() * 1000)}"

        client.post(
            self.base_url,
            data={
                "label": unique_label,
                "name": "Test User List Avatar",
                "avatar_image": (img_file, "test.png"),
            },
            content_type="multipart/form-data",
        )

        # List user profiles
        response = client.get(self.base_url)

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Find our test user profile
        test_profile = next(
            (p for p in data["data"] if p["label"] == unique_label), None
        )
        assert test_profile is not None
        assert test_profile["avatar_image"] is not None
        assert test_profile["avatar_url"] is not None
        assert test_profile["avatar_url"].startswith("/uploads/avatars/")

    def test_search_user_profiles_includes_avatar_urls(self, client, db_session):
        """Test that searching user profiles includes avatar URLs."""
        # Create a user profile with avatar
        img_file = self.create_test_image()
        unique_label = f"searchable_user_avatar_{int(time.time() * 1000)}"

        client.post(
            self.base_url,
            data={
                "label": unique_label,
                "name": "Searchable User Avatar",
                "avatar_image": (img_file, "test.png"),
            },
            content_type="multipart/form-data",
        )

        # Search user profiles
        response = client.get(f"{self.base_url}search?query=searchable")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) > 0

        # Check that avatar URLs are included in search results
        found_profile = None
        for profile in data["data"]:
            if profile["label"] == unique_label:
                found_profile = profile
                break

        assert found_profile is not None
        assert found_profile["avatar_image"] is not None
        assert found_profile["avatar_url"] is not None
        assert found_profile["avatar_url"].startswith("/uploads/avatars/")
