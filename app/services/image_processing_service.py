"""
Image Processing Service

Handles image processing operations including metadata removal and format validation.
Uses Pillow (PIL) for safe and efficient image processing.
"""

import base64
import io
from typing import Dict, Any, Tuple
from PIL import Image, PngImagePlugin
from app.utils.exceptions import ValidationError, ProcessingError


class ImageProcessingService:
    """Service for image processing operations."""
    
    MAX_IMAGE_DIMENSION = 2048  # Maximum width or height in pixels
    SUPPORTED_FORMATS = {'PNG'}
    
    def strip_metadata_from_png(self, png_data: bytes) -> bytes:
        """
        Remove all metadata from a PNG image while preserving image quality.
        
        Args:
            png_data: Raw PNG file bytes
            
        Returns:
            Clean PNG bytes without metadata
            
        Raises:
            ValidationError: If image format is invalid
            ProcessingError: If image processing fails
        """
        try:
            # Load image from bytes
            with Image.open(io.BytesIO(png_data)) as img:
                # Validate image format
                if img.format != 'PNG':
                    raise ValidationError("INVALID_FILE_FORMAT", f"Expected PNG format, got {img.format}")
                
                # Validate image dimensions
                self._validate_image_dimensions(img)
                
                # Create a new image without metadata
                # Convert to RGB if necessary, then back to original mode
                if img.mode in ('RGBA', 'LA'):
                    # Preserve transparency
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(list(img.getdata()))
                else:
                    # Convert to RGB and back to remove metadata
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    clean_img = Image.new('RGB', img.size)
                    clean_img.putdata(list(img.getdata()))
                
                # Save to bytes without metadata
                output = io.BytesIO()
                
                # Use PNG format with optimal compression but no metadata
                clean_img.save(
                    output, 
                    format='PNG',
                    optimize=True,
                    compress_level=6  # Good balance of size vs speed
                )
                
                return output.getvalue()
                
        except ValidationError:
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to process image: {str(e)}")
    
    def encode_image_to_base64(self, image_data: bytes) -> str:
        """
        Encode image bytes to base64 string.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64-encoded image data
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def validate_image_file(self, file_data: bytes, max_size_mb: int = 10) -> Dict[str, Any]:
        """
        Validate uploaded image file.
        
        Args:
            file_data: Raw file bytes
            max_size_mb: Maximum file size in megabytes
            
        Returns:
            Dictionary with validation results and image info
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file size
        file_size_mb = len(file_data) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValidationError(
                "FILE_TOO_LARGE", 
                f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )
        
        try:
            # Validate image format and get info
            with Image.open(io.BytesIO(file_data)) as img:
                if img.format not in self.SUPPORTED_FORMATS:
                    raise ValidationError(
                        "INVALID_FILE_FORMAT", 
                        f"Unsupported format '{img.format}'. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                    )
                
                # Validate dimensions
                self._validate_image_dimensions(img)
                
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size_bytes': len(file_data),
                    'file_size_mb': file_size_mb,
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P')
                }
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError("INVALID_FILE_FORMAT", f"Invalid image file: {str(e)}")
    
    def _validate_image_dimensions(self, img: Image.Image) -> None:
        """
        Validate image dimensions are within acceptable limits.
        
        Args:
            img: PIL Image object
            
        Raises:
            ValidationError: If dimensions are invalid
        """
        width, height = img.size
        
        if width <= 0 or height <= 0:
            raise ValidationError("INVALID_FILE_FORMAT", "Image has invalid dimensions")
        
        if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
            raise ValidationError(
                "INVALID_FILE_FORMAT", 
                f"Image dimensions ({width}x{height}) exceed maximum allowed size ({self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION})"
            )
        
        # Check for reasonable minimum size
        if width < 32 or height < 32:
            raise ValidationError("INVALID_FILE_FORMAT", "Image too small (minimum 32x32 pixels)")
    
    def create_avatar_response(self, clean_image_data: bytes, original_filename: str = None) -> Dict[str, Any]:
        """
        Create avatar image response dictionary.
        
        Args:
            clean_image_data: Processed image bytes without metadata
            original_filename: Original filename for reference
            
        Returns:
            Avatar response dictionary
        """
        base64_data = self.encode_image_to_base64(clean_image_data)
        
        # Generate filename if not provided
        if not original_filename:
            original_filename = "character_avatar.png"
        elif not original_filename.lower().endswith('.png'):
            # Ensure PNG extension
            base_name = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            original_filename = f"{base_name}.png"
        
        return {
            'filename': original_filename,
            'data': base64_data,
            'mime_type': 'image/png',
            'size_bytes': len(clean_image_data)
        }
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Return information about image processing capabilities."""
        return {
            'supported_formats': list(self.SUPPORTED_FORMATS),
            'max_dimension': self.MAX_IMAGE_DIMENSION,
            'min_dimension': 32,
            'features': [
                'metadata_removal',
                'format_validation',
                'dimension_validation',
                'transparency_preservation',
                'base64_encoding'
            ]
        }