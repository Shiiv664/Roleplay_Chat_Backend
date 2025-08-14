"""
Character Extract Service

Orchestrates the extraction of character data from PNG files containing Character Card v2 metadata.
Maps Character Card v2 format to application format and handles the complete extraction workflow.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.png_character_parser import PngCharacterParser
from app.services.image_processing_service import ImageProcessingService
from app.utils.exceptions import ValidationError, ProcessingError


class CharacterExtractService:
    """Service for extracting and mapping character data from PNG files."""
    
    def __init__(self):
        self.png_parser = PngCharacterParser()
        self.image_processor = ImageProcessingService()
    
    def extract_character_from_png(self, png_data: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Extract character data and clean avatar from a PNG file.
        
        Args:
            png_data: Raw PNG file bytes
            filename: Original filename for reference
            
        Returns:
            Dictionary containing character_data and avatar_image
            
        Raises:
            ValidationError: If file format or data is invalid
            ProcessingError: If extraction fails
        """
        try:
            # Validate image file first
            image_info = self.image_processor.validate_image_file(png_data)
            
            # Extract character data from PNG metadata
            raw_character_data = self.png_parser.extract_character_data(png_data)
            
            # Map Character Card v2 data to application format
            character_data = self._map_character_data(raw_character_data)
            
            # Process image to remove metadata
            clean_image_data = self.image_processor.strip_metadata_from_png(png_data)
            
            # Create avatar response
            avatar_image = self.image_processor.create_avatar_response(clean_image_data, filename)
            
            return {
                'character_data': character_data,
                'avatar_image': avatar_image,
                'extraction_info': {
                    'source_format': 'Character Card v2',
                    'original_filename': filename or 'unknown.png',
                    'extracted_at': datetime.utcnow().isoformat() + 'Z',
                    'image_info': image_info
                }
            }
            
        except (ValidationError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Character extraction failed: {str(e)}")
    
    def _map_character_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Character Card v2 format to application character format.
        
        Args:
            raw_data: Raw Character Card v2 data
            
        Returns:
            Mapped character data for application use
        """
        char_data = raw_data.get('data', {})
        
        # Extract basic character information
        name = self._clean_text(char_data.get('name', ''))
        description = self._clean_text(char_data.get('description', ''))
        
        if not name:
            raise ValidationError("INVALID_CHARACTER_DATA", "Character name is required")
        
        if not description:
            raise ValidationError("INVALID_CHARACTER_DATA", "Character description is required")
        
        # Generate unique label
        label = self._generate_character_label(name)
        
        # Build first_messages array
        first_messages = self._extract_first_messages(char_data)
        
        # Map to application format
        mapped_data = {
            'name': name,
            'label': label,
            'description': description,
            'first_messages': first_messages
        }
        
        return mapped_data
    
    def _extract_first_messages(self, char_data: Dict[str, Any]) -> List[str]:
        """
        Extract and clean first messages from Character Card v2 data.
        
        Args:
            char_data: Character data from Character Card v2
            
        Returns:
            List of first messages (primary + alternates)
        """
        messages = []
        
        # Primary greeting message
        first_mes = self._clean_text(char_data.get('first_mes', ''))
        if first_mes:
            messages.append(first_mes)
        
        # Alternative greetings
        alt_greetings = char_data.get('alternate_greetings', [])
        if isinstance(alt_greetings, list):
            for greeting in alt_greetings:
                if isinstance(greeting, str):
                    cleaned_greeting = self._clean_text(greeting)
                    if cleaned_greeting and cleaned_greeting not in messages:
                        messages.append(cleaned_greeting)
        
        # Ensure we have at least one message
        if not messages:
            messages.append("Hello! I'm a character imported from a PNG file.")
        
        return messages
    
    def _generate_character_label(self, name: str) -> str:
        """
        Generate a unique character label based on name and timestamp.
        
        Args:
            name: Character name
            
        Returns:
            Generated label string
        """
        # Clean name for use in label
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.lower())
        clean_name = re.sub(r'_+', '_', clean_name).strip('_')
        
        # Generate timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        
        # Combine name and timestamp
        if clean_name:
            return f"{clean_name}_imported_{timestamp}"
        else:
            return f"character_imported_{timestamp}"
    
    def _clean_text(self, text: Any) -> str:
        """
        Clean and sanitize text input.
        
        Args:
            text: Input text (any type)
            
        Returns:
            Cleaned text string
        """
        if not isinstance(text, str):
            if text is None:
                return ""
            text = str(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Basic length limit (can be adjusted based on requirements)
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text
    
    def get_supported_fields(self) -> Dict[str, Any]:
        """
        Return information about supported Character Card v2 fields.
        
        Returns:
            Dictionary describing field mapping and support
        """
        return {
            'mapped_fields': {
                'data.name': 'name (required)',
                'data.description': 'description (required)',
                'data.first_mes': 'first_messages[0]',
                'data.alternate_greetings[]': 'first_messages[1:]',
                'png_image': 'avatar_image (processed)'
            },
            'ignored_fields': [
                'personality',
                'scenario',
                'mes_example',
                'creator_notes',
                'system_prompt',
                'post_history_instructions',
                'tags',
                'creator',
                'character_version',
                'extensions',
                'character_book'
            ],
            'processing_notes': {
                'label_generation': 'Auto-generated from name + timestamp',
                'text_sanitization': 'Applied to all text fields',
                'image_processing': 'Metadata stripped, PNG format preserved',
                'greeting_deduplication': 'Duplicate messages removed'
            }
        }
    
    def validate_extraction_request(self, file_data: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Validate extraction request before processing.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            
        Returns:
            Validation result dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        # Basic file validation
        if not file_data:
            raise ValidationError("INVALID_FILE_FORMAT", "No file data provided")
        
        # Validate file size (10MB limit as specified)
        max_size_mb = 10
        file_size_mb = len(file_data) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValidationError(
                "FILE_TOO_LARGE", 
                f"File size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
            )
        
        # Validate filename if provided
        if filename:
            if not filename.lower().endswith('.png'):
                raise ValidationError("INVALID_FILE_FORMAT", "File must be a PNG image")
        
        # Validate PNG format
        self.image_processor.validate_image_file(file_data, max_size_mb)
        
        return {
            'valid': True,
            'file_size_mb': file_size_mb,
            'filename': filename or 'unknown.png'
        }