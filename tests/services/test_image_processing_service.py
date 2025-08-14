"""Tests for Image Processing Service."""

import base64
import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from app.services.image_processing_service import ImageProcessingService
from app.utils.exceptions import ValidationError, ProcessingError


class TestImageProcessingService:
    """Test class for ImageProcessingService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImageProcessingService()
    
    def create_test_png_image(self, width=100, height=100, mode='RGB'):
        """Create a test PNG image."""
        img = Image.new(mode, (width, height), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def create_test_image_with_metadata(self, width=100, height=100):
        """Create a test PNG image with metadata."""
        img = Image.new('RGB', (width, height), color='blue')
        
        # Add some metadata
        from PIL.PngImagePlugin import PngInfo
        metadata = PngInfo()
        metadata.add_text("Author", "Test Author")
        metadata.add_text("Description", "Test Image")
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', pnginfo=metadata)
        return img_bytes.getvalue()

    def test_strip_metadata_from_png_success(self):
        """Test successful metadata removal from PNG."""
        png_data = self.create_test_image_with_metadata()
        
        result = self.service.strip_metadata_from_png(png_data)
        
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify the result is a valid PNG
        with Image.open(io.BytesIO(result)) as img:
            assert img.format == 'PNG'
            assert img.size == (100, 100)
    
    def test_strip_metadata_from_png_preserve_transparency(self):
        """Test metadata removal preserves transparency."""
        # Create RGBA image with transparency
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        png_data = img_bytes.getvalue()
        
        result = self.service.strip_metadata_from_png(png_data)
        
        # Verify transparency is preserved
        with Image.open(io.BytesIO(result)) as img:
            assert img.mode in ('RGBA', 'LA')
    
    def test_strip_metadata_from_png_invalid_format(self):
        """Test metadata removal with invalid image format."""
        # Create JPEG image instead of PNG
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        jpeg_data = img_bytes.getvalue()
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.strip_metadata_from_png(jpeg_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "Expected PNG format, got JPEG" in str(exc_info.value)
    
    def test_strip_metadata_from_png_oversized_image(self):
        """Test metadata removal with oversized image."""
        # Create image larger than max dimension
        large_size = self.service.MAX_IMAGE_DIMENSION + 100
        png_data = self.create_test_png_image(large_size, large_size)
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.strip_metadata_from_png(png_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "exceed maximum allowed size" in str(exc_info.value)
    
    def test_strip_metadata_from_png_corrupted_data(self):
        """Test metadata removal with corrupted image data."""
        corrupted_data = b'corrupted image data'
        
        with pytest.raises(ProcessingError):
            self.service.strip_metadata_from_png(corrupted_data)
    
    def test_encode_image_to_base64(self):
        """Test image encoding to base64."""
        png_data = self.create_test_png_image()
        
        result = self.service.encode_image_to_base64(png_data)
        
        assert isinstance(result, str)
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded == png_data
    
    def test_validate_image_file_success(self):
        """Test successful image file validation."""
        png_data = self.create_test_png_image(200, 150)
        
        result = self.service.validate_image_file(png_data)
        
        assert result['format'] == 'PNG'
        assert result['width'] == 200
        assert result['height'] == 150
        assert result['size'] == (200, 150)
        assert result['file_size_bytes'] == len(png_data)
        assert result['file_size_mb'] > 0
        assert 'has_transparency' in result
    
    def test_validate_image_file_too_large(self):
        """Test validation with file too large."""
        # Create small image data but simulate large size
        png_data = self.create_test_png_image()
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_image_file(png_data, max_size_mb=0.001)  # Very small limit
        
        assert exc_info.value.error_code == "FILE_TOO_LARGE"
        assert "exceeds maximum allowed size" in str(exc_info.value)
    
    def test_validate_image_file_unsupported_format(self):
        """Test validation with unsupported format."""
        # Create JPEG image
        img = Image.new('RGB', (100, 100), color='yellow')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        jpeg_data = img_bytes.getvalue()
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_image_file(jpeg_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "Unsupported format 'JPEG'" in str(exc_info.value)
    
    def test_validate_image_file_invalid_data(self):
        """Test validation with invalid image data."""
        invalid_data = b'not an image'
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_image_file(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "Invalid image file" in str(exc_info.value)
    
    def test_validate_image_dimensions_valid(self):
        """Test dimension validation with valid image."""
        img = Image.new('RGB', (512, 256))
        
        # Should not raise an exception
        self.service._validate_image_dimensions(img)
    
    def test_validate_image_dimensions_too_large(self):
        """Test dimension validation with oversized image."""
        large_size = self.service.MAX_IMAGE_DIMENSION + 1
        img = Image.new('RGB', (large_size, 100))
        
        with pytest.raises(ValidationError) as exc_info:
            self.service._validate_image_dimensions(img)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "exceed maximum allowed size" in str(exc_info.value)
    
    def test_validate_image_dimensions_too_small(self):
        """Test dimension validation with too small image."""
        img = Image.new('RGB', (16, 16))  # Smaller than minimum 32x32
        
        with pytest.raises(ValidationError) as exc_info:
            self.service._validate_image_dimensions(img)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "too small (minimum 32x32 pixels)" in str(exc_info.value)
    
    def test_validate_image_dimensions_zero_size(self):
        """Test dimension validation with zero-sized image."""
        img = Image.new('RGB', (0, 100))
        
        with pytest.raises(ValidationError) as exc_info:
            self.service._validate_image_dimensions(img)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "invalid dimensions" in str(exc_info.value)
    
    def test_create_avatar_response_with_filename(self):
        """Test avatar response creation with filename."""
        png_data = self.create_test_png_image()
        filename = "test_avatar.png"
        
        result = self.service.create_avatar_response(png_data, filename)
        
        assert result['filename'] == filename
        assert result['mime_type'] == 'image/png'
        assert result['size_bytes'] == len(png_data)
        assert 'data' in result
        
        # Verify base64 data is valid
        decoded = base64.b64decode(result['data'])
        assert decoded == png_data
    
    def test_create_avatar_response_without_filename(self):
        """Test avatar response creation without filename."""
        png_data = self.create_test_png_image()
        
        result = self.service.create_avatar_response(png_data)
        
        assert result['filename'] == 'character_avatar.png'
        assert result['mime_type'] == 'image/png'
    
    def test_create_avatar_response_ensure_png_extension(self):
        """Test avatar response ensures PNG extension."""
        png_data = self.create_test_png_image()
        filename = "test_avatar.jpg"  # Wrong extension
        
        result = self.service.create_avatar_response(png_data, filename)
        
        assert result['filename'] == 'test_avatar.png'  # Should be corrected
    
    def test_get_processing_info(self):
        """Test processing info retrieval."""
        info = self.service.get_processing_info()
        
        assert isinstance(info, dict)
        assert 'PNG' in info['supported_formats']
        assert info['max_dimension'] == self.service.MAX_IMAGE_DIMENSION
        assert info['min_dimension'] == 32
        assert 'features' in info
        assert 'metadata_removal' in info['features']
    
    @patch('app.services.image_processing_service.Image.open')
    def test_strip_metadata_error_handling(self, mock_open):
        """Test error handling in metadata stripping."""
        mock_open.side_effect = Exception("PIL error")
        png_data = b'fake png data'
        
        with pytest.raises(ProcessingError) as exc_info:
            self.service.strip_metadata_from_png(png_data)
        
        assert "Failed to process image" in str(exc_info.value)
    
    def test_validate_image_file_with_transparency(self):
        """Test validation recognizes transparency."""
        # Create RGBA image with transparency
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        png_data = img_bytes.getvalue()
        
        result = self.service.validate_image_file(png_data)
        
        assert result['has_transparency'] is True
        assert result['mode'] == 'RGBA'
    
    def test_validate_image_file_without_transparency(self):
        """Test validation recognizes no transparency."""
        png_data = self.create_test_png_image()
        
        result = self.service.validate_image_file(png_data)
        
        assert result['has_transparency'] is False
        assert result['mode'] == 'RGB'