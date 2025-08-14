"""Tests for Character Extract Service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.character_extract_service import CharacterExtractService
from app.utils.exceptions import ValidationError, ProcessingError


class TestCharacterExtractService:
    """Test class for CharacterExtractService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = CharacterExtractService()
        
        # Mock PNG data
        self.mock_png_data = b'fake png data'
        
        # Sample Character Card v2 data
        self.sample_raw_data = {
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {
                "name": "Test Character",
                "description": "A wonderful test character with amazing personality traits.",
                "first_mes": "Hello! I'm Test Character, nice to meet you!",
                "alternate_greetings": [
                    "Hi there! How are you doing today?",
                    "Greetings! What brings you here?"
                ],
                "avatar": "self",
                "personality": "Friendly and helpful",
                "scenario": "Testing environment",
                "creator": "TestUser",
                "tags": ["test", "character"],
                "extensions": {
                    "chub": {
                        "id": 12345,
                        "full_path": "testuser/test-character"
                    }
                }
            }
        }
        
        # Expected mapped data
        self.expected_character_data = {
            "name": "Test Character",
            "label": "test_character_imported_20240814",  # Will be mocked
            "description": "A wonderful test character with amazing personality traits.",
            "first_messages": [
                "Hello! I'm Test Character, nice to meet you!",
                "Hi there! How are you doing today?",
                "Greetings! What brings you here?"
            ]
        }
        
        # Mock image info
        self.mock_image_info = {
            'format': 'PNG',
            'width': 512,
            'height': 512,
            'file_size_mb': 1.5
        }
        
        # Mock clean image data
        self.mock_clean_image = b'clean png data'
        
        # Mock avatar response
        self.mock_avatar_response = {
            'filename': 'test_character.png',
            'data': 'base64encodeddata',
            'mime_type': 'image/png',
            'size_bytes': 1024
        }

    @patch('app.services.character_extract_service.datetime')
    def test_extract_character_from_png_success(self, mock_datetime):
        """Test successful character extraction from PNG."""
        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = '2024-08-14T12:00:00'
        mock_datetime.utcnow.return_value.strftime.return_value = '20240814'
        
        # Mock services
        self.service.image_processor.validate_image_file.return_value = self.mock_image_info
        self.service.png_parser.extract_character_data.return_value = self.sample_raw_data
        self.service.image_processor.strip_metadata_from_png.return_value = self.mock_clean_image
        self.service.image_processor.create_avatar_response.return_value = self.mock_avatar_response
        
        result = self.service.extract_character_from_png(self.mock_png_data, "test.png")
        
        assert 'character_data' in result
        assert 'avatar_image' in result
        assert 'extraction_info' in result
        
        char_data = result['character_data']
        assert char_data['name'] == 'Test Character'
        assert char_data['description'] == 'A wonderful test character with amazing personality traits.'
        assert len(char_data['first_messages']) == 3
        assert 'test_character_imported_20240814' in char_data['label']
        
        assert result['avatar_image'] == self.mock_avatar_response
        
        extraction_info = result['extraction_info']
        assert extraction_info['source_format'] == 'Character Card v2'
        assert extraction_info['original_filename'] == 'test.png'
    
    def test_extract_character_from_png_validation_error(self):
        """Test extraction with validation error."""
        # Mock validation error
        self.service.image_processor.validate_image_file.side_effect = ValidationError(
            "INVALID_FILE_FORMAT", "Invalid PNG"
        )
        
        with pytest.raises(ValidationError):
            self.service.extract_character_from_png(self.mock_png_data)
    
    def test_extract_character_from_png_processing_error(self):
        """Test extraction with processing error."""
        # Mock services to work until character data extraction fails
        self.service.image_processor.validate_image_file.return_value = self.mock_image_info
        self.service.png_parser.extract_character_data.side_effect = ProcessingError("Parse error")
        
        with pytest.raises(ProcessingError):
            self.service.extract_character_from_png(self.mock_png_data)
    
    def test_extract_character_from_png_unexpected_error(self):
        """Test extraction with unexpected error."""
        # Mock unexpected error
        self.service.image_processor.validate_image_file.side_effect = Exception("Unexpected error")
        
        with pytest.raises(ProcessingError) as exc_info:
            self.service.extract_character_from_png(self.mock_png_data)
        
        assert "Character extraction failed" in str(exc_info.value)
    
    @patch('app.services.character_extract_service.datetime')
    def test_map_character_data_success(self, mock_datetime):
        """Test successful character data mapping."""
        mock_datetime.utcnow.return_value.strftime.return_value = '20240814'
        
        result = self.service._map_character_data(self.sample_raw_data)
        
        assert result['name'] == 'Test Character'
        assert result['description'] == 'A wonderful test character with amazing personality traits.'
        assert len(result['first_messages']) == 3
        assert result['first_messages'][0] == 'Hello! I\'m Test Character, nice to meet you!'
        assert 'test_character_imported_20240814' in result['label']
    
    def test_map_character_data_missing_name(self):
        """Test mapping with missing character name."""
        invalid_data = {
            "spec": "chara_card_v2",
            "data": {
                "description": "A character without a name"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.service._map_character_data(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "Character name is required" in str(exc_info.value)
    
    def test_map_character_data_missing_description(self):
        """Test mapping with missing character description."""
        invalid_data = {
            "spec": "chara_card_v2",
            "data": {
                "name": "Test Character"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.service._map_character_data(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "Character description is required" in str(exc_info.value)
    
    def test_extract_first_messages_with_all_data(self):
        """Test first message extraction with all data present."""
        char_data = {
            "first_mes": "Primary greeting",
            "alternate_greetings": [
                "Alternative 1",
                "Alternative 2",
                "Primary greeting"  # Duplicate should be removed
            ]
        }
        
        result = self.service._extract_first_messages(char_data)
        
        assert len(result) == 3  # No duplicates
        assert result[0] == "Primary greeting"
        assert "Alternative 1" in result
        assert "Alternative 2" in result
    
    def test_extract_first_messages_no_first_mes(self):
        """Test first message extraction without primary message."""
        char_data = {
            "alternate_greetings": ["Alternative 1", "Alternative 2"]
        }
        
        result = self.service._extract_first_messages(char_data)
        
        assert len(result) == 2
        assert "Alternative 1" in result
        assert "Alternative 2" in result
    
    def test_extract_first_messages_no_messages(self):
        """Test first message extraction with no messages."""
        char_data = {}
        
        result = self.service._extract_first_messages(char_data)
        
        assert len(result) == 1
        assert "Hello! I'm a character imported from a PNG file." in result[0]
    
    def test_extract_first_messages_invalid_alternate_greetings(self):
        """Test first message extraction with invalid alternate greetings."""
        char_data = {
            "first_mes": "Primary greeting",
            "alternate_greetings": "not a list"  # Should be ignored
        }
        
        result = self.service._extract_first_messages(char_data)
        
        assert len(result) == 1
        assert result[0] == "Primary greeting"
    
    @patch('app.services.character_extract_service.datetime')
    def test_generate_character_label_normal_name(self, mock_datetime):
        """Test label generation with normal character name."""
        mock_datetime.utcnow.return_value.strftime.return_value = '20240814'
        
        result = self.service._generate_character_label("Test Character")
        
        assert result == "test_character_imported_20240814"
    
    @patch('app.services.character_extract_service.datetime')
    def test_generate_character_label_special_characters(self, mock_datetime):
        """Test label generation with special characters in name."""
        mock_datetime.utcnow.return_value.strftime.return_value = '20240814'
        
        result = self.service._generate_character_label("Test@Character#123!")
        
        assert result == "test_character_123_imported_20240814"
    
    @patch('app.services.character_extract_service.datetime')
    def test_generate_character_label_empty_name(self, mock_datetime):
        """Test label generation with empty name."""
        mock_datetime.utcnow.return_value.strftime.return_value = '20240814'
        
        result = self.service._generate_character_label("")
        
        assert result == "character_imported_20240814"
    
    def test_clean_text_normal_text(self):
        """Test text cleaning with normal text."""
        text = "This is normal text with some   extra spaces."
        
        result = self.service._clean_text(text)
        
        assert result == "This is normal text with some extra spaces."
    
    def test_clean_text_non_string(self):
        """Test text cleaning with non-string input."""
        result = self.service._clean_text(12345)
        
        assert result == "12345"
    
    def test_clean_text_none(self):
        """Test text cleaning with None input."""
        result = self.service._clean_text(None)
        
        assert result == ""
    
    def test_clean_text_too_long(self):
        """Test text cleaning with very long text."""
        long_text = "A" * 10001  # Longer than 10000 character limit
        
        result = self.service._clean_text(long_text)
        
        assert len(result) <= 10003  # 10000 + "..."
        assert result.endswith("...")
    
    def test_get_supported_fields(self):
        """Test supported fields information."""
        result = self.service.get_supported_fields()
        
        assert 'mapped_fields' in result
        assert 'ignored_fields' in result
        assert 'processing_notes' in result
        
        mapped = result['mapped_fields']
        assert 'data.name' in mapped
        assert 'data.description' in mapped
        assert 'data.first_mes' in mapped
        
        ignored = result['ignored_fields']
        assert 'personality' in ignored
        assert 'scenario' in ignored
        assert 'extensions' in ignored
    
    def test_validate_extraction_request_success(self):
        """Test successful extraction request validation."""
        file_data = b'fake png data' * 100  # Small file
        filename = "test.png"
        
        # Mock image processor validation
        self.service.image_processor.validate_image_file.return_value = {'format': 'PNG'}
        
        result = self.service.validate_extraction_request(file_data, filename)
        
        assert result['valid'] is True
        assert result['filename'] == filename
        assert 'file_size_mb' in result
    
    def test_validate_extraction_request_no_data(self):
        """Test validation with no file data."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_extraction_request(b'', "test.png")
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "No file data provided" in str(exc_info.value)
    
    def test_validate_extraction_request_file_too_large(self):
        """Test validation with file too large."""
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB - larger than 10MB limit
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_extraction_request(large_data, "test.png")
        
        assert exc_info.value.error_code == "FILE_TOO_LARGE"
        assert "exceeds limit" in str(exc_info.value)
    
    def test_validate_extraction_request_wrong_extension(self):
        """Test validation with wrong file extension."""
        file_data = b'fake data'
        filename = "test.jpg"
        
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_extraction_request(file_data, filename)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "File must be a PNG image" in str(exc_info.value)
    
    def test_validate_extraction_request_no_filename(self):
        """Test validation without filename."""
        file_data = b'fake png data'
        
        # Mock image processor validation
        self.service.image_processor.validate_image_file.return_value = {'format': 'PNG'}
        
        result = self.service.validate_extraction_request(file_data)
        
        assert result['valid'] is True
        assert result['filename'] == 'unknown.png'
    
    def test_validate_extraction_request_image_validation_error(self):
        """Test validation when image processor raises error."""
        file_data = b'fake data'
        
        # Mock image processor to raise validation error
        self.service.image_processor.validate_image_file.side_effect = ValidationError(
            "INVALID_FILE_FORMAT", "Not a valid image"
        )
        
        with pytest.raises(ValidationError):
            self.service.validate_extraction_request(file_data, "test.png")
    
    def test_extract_first_messages_empty_strings(self):
        """Test first message extraction with empty strings."""
        char_data = {
            "first_mes": "",
            "alternate_greetings": ["", "   ", "Valid message", ""]
        }
        
        result = self.service._extract_first_messages(char_data)
        
        assert len(result) == 1
        assert result[0] == "Valid message"
    
    def test_map_character_data_whitespace_handling(self):
        """Test character data mapping with whitespace handling."""
        data_with_whitespace = {
            "spec": "chara_card_v2",
            "data": {
                "name": "  Test Character  ",
                "description": " A character    with extra   whitespace. ",
                "first_mes": " Hello there!  "
            }
        }
        
        result = self.service._map_character_data(data_with_whitespace)
        
        assert result['name'] == "Test Character"
        assert result['description'] == "A character with extra whitespace."
        assert result['first_messages'][0] == "Hello there!"