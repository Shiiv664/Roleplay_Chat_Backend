"""Tests for the file upload service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

from app.services.file_upload_service import FileUploadError, FileUploadService


class TestFileUploadService:
    """Test cases for FileUploadService."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.service = FileUploadService()
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.service.UPLOAD_DIR = self.temp_dir
        self.service.AVATAR_DIR = self.temp_dir / "avatars"
        self.service._ensure_directories_exist()

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_image(
        self, filename: str, size: tuple = (100, 100), format: str = "PNG"
    ) -> Path:
        """Create a test image file."""
        image_path = self.temp_dir / filename
        with Image.new("RGB", size, color="red") as img:
            img.save(image_path, format=format)
        return image_path

    def create_mock_file_storage(
        self, filename: str, content: bytes, content_type: str
    ):
        """Create a mock FileStorage object for Flask."""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=len(content))
        mock_file.save = Mock()
        return mock_file

    def test_ensure_directories_exist(self):
        """Test that directories are created properly."""
        # Directories should already exist from setup
        assert self.service.AVATAR_DIR.exists()
        assert self.service.AVATAR_DIR.is_dir()

    def test_get_file_extension_valid(self):
        """Test extracting file extension from valid filename."""
        extension = self.service._get_file_extension("test.jpg")
        assert extension == ".jpg"

        extension = self.service._get_file_extension("image.PNG")
        assert extension == ".png"

    def test_get_file_extension_no_filename(self):
        """Test extracting file extension with no filename."""
        with pytest.raises(FileUploadError) as exc_info:
            self.service._get_file_extension(None)
        assert "Filename is required" in str(exc_info.value)

    def test_get_file_extension_no_extension(self):
        """Test extracting file extension with no extension."""
        with pytest.raises(FileUploadError) as exc_info:
            self.service._get_file_extension("filename")
        assert "File must have an extension" in str(exc_info.value)

    def test_validate_avatar_file_sync_valid_file(self):
        """Test validation of a valid avatar file."""
        # Create a small test file
        test_content = b"fake image content"
        mock_file = self.create_mock_file_storage(
            "test.jpg", test_content, "image/jpeg"
        )

        # Should not raise an exception
        self.service._validate_avatar_file_sync(mock_file)

    def test_validate_avatar_file_sync_file_too_large(self):
        """Test validation of file that's too large."""
        # Create content larger than max size
        large_content = b"x" * (self.service.MAX_FILE_SIZE + 1)
        mock_file = self.create_mock_file_storage(
            "large.jpg", large_content, "image/jpeg"
        )

        with pytest.raises(FileUploadError) as exc_info:
            self.service._validate_avatar_file_sync(mock_file)
        assert "File too large" in str(exc_info.value)

    def test_validate_avatar_file_sync_invalid_mime_type(self):
        """Test validation of file with invalid MIME type."""
        test_content = b"fake content"
        mock_file = self.create_mock_file_storage(
            "test.txt", test_content, "text/plain"
        )

        with pytest.raises(FileUploadError) as exc_info:
            self.service._validate_avatar_file_sync(mock_file)
        assert "Invalid file type" in str(exc_info.value)

    def test_validate_avatar_file_sync_invalid_extension(self):
        """Test validation of file with invalid extension."""
        test_content = b"fake content"
        mock_file = self.create_mock_file_storage(
            "test.txt", test_content, "image/jpeg"
        )

        with pytest.raises(FileUploadError) as exc_info:
            self.service._validate_avatar_file_sync(mock_file)
        assert "Invalid file extension" in str(exc_info.value)

    def test_process_image_valid(self):
        """Test processing a valid image."""
        # Create a test image
        image_path = self.create_test_image("test.png", (500, 500))

        # Should not raise an exception
        self.service._process_image(image_path)

        # Image should still exist
        assert image_path.exists()

    def test_process_image_resize_large_image(self):
        """Test processing an image that needs resizing."""
        # Create a large test image
        large_size = (2000, 2000)  # Larger than MAX_IMAGE_DIMENSIONS
        image_path = self.create_test_image("large.png", large_size)

        # Process the image
        self.service._process_image(image_path)

        # Check that image was resized
        with Image.open(image_path) as img:
            assert img.size[0] <= self.service.MAX_IMAGE_DIMENSIONS[0]
            assert img.size[1] <= self.service.MAX_IMAGE_DIMENSIONS[1]

    def test_process_image_invalid_file(self):
        """Test processing an invalid image file."""
        # Create a non-image file
        invalid_path = self.temp_dir / "invalid.jpg"
        invalid_path.write_text("This is not an image")

        with pytest.raises(Exception):
            self.service._process_image(invalid_path)

    def test_save_avatar_image_sync_success(self):
        """Test successful avatar image saving."""
        # Create a real image for testing
        test_image_path = self.create_test_image("original.png")

        # Create mock file that will copy the real image
        mock_file = Mock()
        mock_file.filename = "test.png"
        mock_file.content_type = "image/png"
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=1000)  # Small file size

        def mock_save(path):
            # Copy our test image to the target path
            import shutil

            shutil.copy2(test_image_path, path)

        mock_file.save = mock_save

        # Save the image
        result_path = self.service.save_avatar_image_sync(mock_file)

        # Check result
        assert result_path.startswith("avatars/")
        assert result_path.endswith(".png")

        # Check that file was saved
        full_path = self.service.AVATAR_DIR / result_path.split("/", 1)[1]
        assert full_path.exists()

    def test_save_avatar_image_sync_no_file(self):
        """Test avatar image saving with no file."""
        with pytest.raises(FileUploadError) as exc_info:
            self.service.save_avatar_image_sync(None)
        assert "No file provided" in str(exc_info.value)

    def test_save_avatar_image_sync_no_filename(self):
        """Test avatar image saving with no filename."""
        mock_file = Mock()
        mock_file.filename = None

        with pytest.raises(FileUploadError) as exc_info:
            self.service.save_avatar_image_sync(mock_file)
        assert "No file provided" in str(exc_info.value)

    def test_delete_avatar_image_success(self):
        """Test successful deletion of avatar image."""
        # Create a test file
        test_file = self.service.AVATAR_DIR / "test.jpg"
        test_file.write_text("fake image")

        # Delete the file
        result = self.service.delete_avatar_image("avatars/test.jpg")

        assert result is True
        assert not test_file.exists()

    def test_delete_avatar_image_file_not_found(self):
        """Test deletion of non-existent file."""
        result = self.service.delete_avatar_image("avatars/nonexistent.jpg")
        assert result is False

    def test_delete_avatar_image_invalid_path(self):
        """Test deletion with invalid path."""
        result = self.service.delete_avatar_image("../malicious/path.jpg")
        assert result is False

    def test_get_avatar_url_local_path(self):
        """Test getting URL for local avatar path."""
        url = self.service.get_avatar_url("avatars/test.jpg")
        assert url == "/static/avatars/test.jpg"

    def test_get_avatar_url_external_url(self):
        """Test getting URL for external avatar URL."""
        external_url = "https://example.com/avatar.jpg"
        url = self.service.get_avatar_url(external_url)
        assert url == external_url

    def test_get_avatar_url_none(self):
        """Test getting URL for None."""
        url = self.service.get_avatar_url(None)
        assert url is None

    def test_get_avatar_url_empty_string(self):
        """Test getting URL for empty string."""
        url = self.service.get_avatar_url("")
        assert url is None
