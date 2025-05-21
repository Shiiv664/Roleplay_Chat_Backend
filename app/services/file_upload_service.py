"""File upload service for handling avatar images and other file uploads."""

import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

try:
    from fastapi import UploadFile
except ImportError:
    # For when FastAPI is not available
    class UploadFile:
        pass


class FileUploadError(Exception):
    """Custom exception for file upload errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FileUploadService:
    """Service for handling file uploads with validation and processing."""

    UPLOAD_DIR = Path("uploads")
    AVATAR_DIR = UPLOAD_DIR / "avatars"

    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_DIMENSIONS = (1024, 1024)

    def __init__(self):
        """Initialize the file upload service and create necessary directories."""
        self._ensure_directories_exist()

    def _ensure_directories_exist(self) -> None:
        """Create upload directories if they don't exist."""
        self.AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    def save_avatar_image_sync(self, file) -> str:
        """
        Save an uploaded avatar image with validation (synchronous version for Flask).

        Args:
            file: The uploaded FileStorage object from Flask

        Returns:
            str: The relative path to the saved file

        Raises:
            HTTPException: If file validation fails
        """
        if not file or not file.filename:
            raise FileUploadError("No file provided")

        # Validate file
        self._validate_avatar_file_sync(file)

        # Generate unique filename
        file_extension = self._get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.AVATAR_DIR / unique_filename

        # Save file
        try:
            file.save(str(file_path))
        except Exception as e:
            raise FileUploadError(f"Failed to save file: {str(e)}", 500)

        # Validate and potentially resize image
        try:
            self._process_image(file_path)
        except Exception as e:
            # Clean up if image processing fails
            if file_path.exists():
                file_path.unlink()
            raise FileUploadError(f"Invalid image file: {str(e)}")

        # Return relative path for database storage
        return f"avatars/{unique_filename}"

    def _validate_avatar_file_sync(self, file) -> None:
        """
        Validate uploaded avatar file (synchronous version for Flask).

        Args:
            file: The uploaded FileStorage object to validate

        Raises:
            HTTPException: If validation fails
        """
        # Check file size by seeking to end and getting position
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > self.MAX_FILE_SIZE:
            raise FileUploadError(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Check MIME type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise FileUploadError(
                f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )

        # Check file extension
        if file.filename:
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in self.ALLOWED_EXTENSIONS:
                raise FileUploadError(
                    f"Invalid file extension. Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )

    async def save_avatar_image(self, file: UploadFile) -> str:
        """
        Save an uploaded avatar image with validation.

        Args:
            file: The uploaded file from FastAPI

        Returns:
            str: The relative path to the saved file

        Raises:
            HTTPException: If file validation fails
        """
        if not file:
            raise FileUploadError("No file provided")

        # Validate file
        await self._validate_avatar_file(file)

        # Generate unique filename
        file_extension = self._get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.AVATAR_DIR / unique_filename

        # Save file
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            raise FileUploadError(f"Failed to save file: {str(e)}", 500)

        # Validate and potentially resize image
        try:
            self._process_image(file_path)
        except Exception as e:
            # Clean up if image processing fails
            if file_path.exists():
                file_path.unlink()
            raise FileUploadError(f"Invalid image file: {str(e)}")

        # Return relative path for database storage
        return f"avatars/{unique_filename}"

    async def _validate_avatar_file(self, file: UploadFile) -> None:
        """
        Validate uploaded avatar file.

        Args:
            file: The uploaded file to validate

        Raises:
            HTTPException: If validation fails
        """
        # Check file size
        contents = await file.read()
        await file.seek(0)  # Reset file pointer

        if len(contents) > self.MAX_FILE_SIZE:
            raise FileUploadError(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Check MIME type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise FileUploadError(
                f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )

        # Check file extension
        if file.filename:
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in self.ALLOWED_EXTENSIONS:
                raise FileUploadError(
                    f"Invalid file extension. Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )

    def _get_file_extension(self, filename: Optional[str]) -> str:
        """
        Extract file extension from filename.

        Args:
            filename: The original filename

        Returns:
            str: The file extension including the dot

        Raises:
            HTTPException: If no valid extension found
        """
        if not filename:
            raise FileUploadError("Filename is required")

        extension = Path(filename).suffix.lower()
        if not extension:
            raise FileUploadError("File must have an extension")

        return extension

    def _process_image(self, file_path: Path) -> None:
        """
        Process and validate image file.

        Args:
            file_path: Path to the saved image file

        Raises:
            Exception: If image processing fails
        """
        with Image.open(file_path) as img:
            # Validate image can be opened (checks if it's really an image)
            img.verify()

        # Reopen for processing (verify() closes the image)
        with Image.open(file_path) as img:
            # Check dimensions
            if (
                img.size[0] > self.MAX_IMAGE_DIMENSIONS[0]
                or img.size[1] > self.MAX_IMAGE_DIMENSIONS[1]
            ):
                # Resize image while maintaining aspect ratio
                img.thumbnail(self.MAX_IMAGE_DIMENSIONS, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)

    def delete_avatar_image(self, relative_path: str) -> bool:
        """
        Delete an avatar image file.

        Args:
            relative_path: The relative path to the image (e.g., "avatars/filename.jpg")

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        if not relative_path or not relative_path.startswith("avatars/"):
            return False

        file_path = self.UPLOAD_DIR / relative_path

        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False

        return False

    def get_avatar_url(self, relative_path: Optional[str]) -> Optional[str]:
        """
        Convert relative path to URL for frontend access.

        Args:
            relative_path: The relative path stored in database

        Returns:
            str: The URL path for frontend access, or None if no path provided
        """
        if not relative_path:
            return None

        # If it's already a URL, return as-is
        if relative_path.startswith(("http://", "https://")):
            return relative_path

        # Convert local path to uploads URL
        return f"/uploads/{relative_path}"
