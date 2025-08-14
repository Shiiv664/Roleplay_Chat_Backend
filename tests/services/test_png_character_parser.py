"""Tests for PNG Character Parser Service."""

import base64
import json
import struct
import pytest
from unittest.mock import Mock, patch

from app.services.png_character_parser import PngCharacterParser
from app.utils.exceptions import ValidationError, ProcessingError


class TestPngCharacterParser:
    """Test class for PngCharacterParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PngCharacterParser()
        
        # Sample Character Card v2 data
        self.sample_character_data = {
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {
                "name": "Test Character",
                "description": "A test character for unit testing",
                "first_mes": "Hello! I'm a test character.",
                "alternate_greetings": [
                    "Hi there! Nice to meet you.",
                    "Greetings! How are you today?"
                ],
                "avatar": "self",
                "personality": "Friendly and helpful",
                "scenario": "Testing environment",
                "creator": "TestUser"
            }
        }
        
        # Valid PNG signature
        self.png_signature = b'\x89PNG\r\n\x1a\n'
    
    def create_mock_png_with_character_data(self, character_data):
        """Create a mock PNG with embedded character data."""
        # Encode character data
        json_data = json.dumps(character_data)
        encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        
        # Create tEXt chunk with character data
        chara_key = b'chara'
        text_data = chara_key + b'\x00' + encoded_data.encode('utf-8')
        chunk_length = len(text_data)
        
        # Build PNG with tEXt chunk
        png_data = self.png_signature
        
        # Add tEXt chunk
        png_data += struct.pack('>I', chunk_length)  # Length
        png_data += b'tEXt'  # Chunk type
        png_data += text_data  # Chunk data
        png_data += b'\x00\x00\x00\x00'  # CRC (dummy)
        
        # Add IEND chunk
        png_data += struct.pack('>I', 0)  # Length
        png_data += b'IEND'  # Chunk type
        png_data += b'\x00\x00\x00\x00'  # CRC (dummy)
        
        return png_data
    
    def create_invalid_png(self):
        """Create invalid PNG data."""
        return b'invalid png data'
    
    def create_png_without_character_data(self):
        """Create valid PNG without character data."""
        png_data = self.png_signature
        
        # Add IEND chunk only
        png_data += struct.pack('>I', 0)  # Length
        png_data += b'IEND'  # Chunk type
        png_data += b'\x00\x00\x00\x00'  # CRC (dummy)
        
        return png_data

    def test_extract_character_data_success(self):
        """Test successful character data extraction."""
        png_data = self.create_mock_png_with_character_data(self.sample_character_data)
        
        result = self.parser.extract_character_data(png_data)
        
        assert result == self.sample_character_data
        assert result['spec'] == 'chara_card_v2'
        assert result['data']['name'] == 'Test Character'
    
    def test_extract_character_data_invalid_png(self):
        """Test extraction with invalid PNG format."""
        invalid_data = self.create_invalid_png()
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser.extract_character_data(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "not a valid PNG image" in str(exc_info.value)
    
    def test_extract_character_data_no_character_data(self):
        """Test extraction with PNG that has no character data."""
        png_data = self.create_png_without_character_data()
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser.extract_character_data(png_data)
        
        assert exc_info.value.error_code == "NO_CHARACTER_DATA"
        assert "no Character Card v2 metadata" in str(exc_info.value)
    
    def test_extract_character_data_invalid_json(self):
        """Test extraction with invalid JSON in character data."""
        # Create PNG with invalid JSON
        invalid_json = "invalid json data"
        encoded_data = base64.b64encode(invalid_json.encode('utf-8')).decode('utf-8')
        
        # Create tEXt chunk with invalid data
        chara_key = b'chara'
        text_data = chara_key + b'\x00' + encoded_data.encode('utf-8')
        chunk_length = len(text_data)
        
        png_data = self.png_signature
        png_data += struct.pack('>I', chunk_length)
        png_data += b'tEXt'
        png_data += text_data
        png_data += b'\x00\x00\x00\x00'
        png_data += struct.pack('>I', 0)
        png_data += b'IEND'
        png_data += b'\x00\x00\x00\x00'
        
        with pytest.raises(ProcessingError):
            self.parser.extract_character_data(png_data)
    
    def test_extract_character_data_invalid_base64(self):
        """Test extraction with invalid base64 encoding."""
        # Create PNG with invalid base64
        invalid_base64 = "not valid base64!"
        
        chara_key = b'chara'
        text_data = chara_key + b'\x00' + invalid_base64.encode('utf-8')
        chunk_length = len(text_data)
        
        png_data = self.png_signature
        png_data += struct.pack('>I', chunk_length)
        png_data += b'tEXt'
        png_data += text_data
        png_data += b'\x00\x00\x00\x00'
        png_data += struct.pack('>I', 0)
        png_data += b'IEND'
        png_data += b'\x00\x00\x00\x00'
        
        with pytest.raises(ProcessingError):
            self.parser.extract_character_data(png_data)
    
    def test_validate_png_format_valid(self):
        """Test PNG format validation with valid data."""
        png_data = self.png_signature + b'some data'
        
        # Should not raise an exception
        self.parser._validate_png_format(png_data)
    
    def test_validate_png_format_too_small(self):
        """Test PNG format validation with too small data."""
        small_data = b'tiny'
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_png_format(small_data)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "too small" in str(exc_info.value)
    
    def test_validate_png_format_wrong_signature(self):
        """Test PNG format validation with wrong signature."""
        wrong_signature = b'WRONGSIG'
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_png_format(wrong_signature)
        
        assert exc_info.value.error_code == "INVALID_FILE_FORMAT"
        assert "not a valid PNG image" in str(exc_info.value)
    
    def test_validate_character_card_format_valid(self):
        """Test Character Card v2 format validation with valid data."""
        # Should not raise an exception
        self.parser._validate_character_card_format(self.sample_character_data)
    
    def test_validate_character_card_format_not_dict(self):
        """Test validation with non-dictionary data."""
        invalid_data = "not a dictionary"
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_character_card_format(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "must be a JSON object" in str(exc_info.value)
    
    def test_validate_character_card_format_wrong_spec(self):
        """Test validation with wrong spec field."""
        invalid_data = {
            "spec": "wrong_spec",
            "data": {"name": "Test", "description": "Test"}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_character_card_format(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "Invalid or missing Character Card v2 spec" in str(exc_info.value)
    
    def test_validate_character_card_format_missing_data(self):
        """Test validation with missing data field."""
        invalid_data = {
            "spec": "chara_card_v2"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_character_card_format(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "Missing or invalid character data field" in str(exc_info.value)
    
    def test_validate_character_card_format_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_data = {
            "spec": "chara_card_v2",
            "data": {
                "name": "Test"
                # Missing description
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.parser._validate_character_card_format(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_CHARACTER_DATA"
        assert "Missing required field: description" in str(exc_info.value)
    
    def test_decode_character_data_success(self):
        """Test successful character data decoding."""
        json_data = json.dumps(self.sample_character_data)
        encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        
        result = self.parser._decode_character_data(encoded_data)
        
        assert result == self.sample_character_data
    
    def test_decode_character_data_invalid_base64(self):
        """Test character data decoding with invalid base64."""
        invalid_base64 = "not valid base64!"
        
        with pytest.raises(ValueError):
            self.parser._decode_character_data(invalid_base64)
    
    def test_extract_character_text_success(self):
        """Test successful character text extraction from PNG chunks."""
        png_data = self.create_mock_png_with_character_data(self.sample_character_data)
        
        result = self.parser._extract_character_text(png_data)
        
        assert result is not None
        # Should be base64-encoded JSON
        decoded = base64.b64decode(result)
        parsed = json.loads(decoded)
        assert parsed == self.sample_character_data
    
    def test_extract_character_text_no_text_chunks(self):
        """Test extraction with no tEXt chunks."""
        png_data = self.create_png_without_character_data()
        
        result = self.parser._extract_character_text(png_data)
        
        assert result is None
    
    def test_extract_character_text_malformed_chunk(self):
        """Test extraction with malformed chunks."""
        # Create PNG with malformed chunk
        png_data = self.png_signature
        png_data += b'malformed chunk data'
        
        result = self.parser._extract_character_text(png_data)
        
        assert result is None
    
    def test_get_supported_formats(self):
        """Test supported formats information."""
        formats = self.parser.get_supported_formats()
        
        assert isinstance(formats, dict)
        assert formats['format'] == 'Character Card v2 (chub.ai)'
        assert formats['specification'] == 'chara_card_v2'
        assert formats['version'] == '2.0'
        assert formats['encoding'] == 'base64'
        assert formats['storage'] == 'PNG tEXt chunks'
    
    def test_extract_character_text_with_multiple_text_chunks(self):
        """Test extraction when PNG has multiple tEXt chunks."""
        # Create PNG with multiple tEXt chunks
        png_data = self.png_signature
        
        # Add first tEXt chunk (not character data)
        other_key = b'other'
        other_text = other_key + b'\x00' + b'some other data'
        other_length = len(other_text)
        
        png_data += struct.pack('>I', other_length)
        png_data += b'tEXt'
        png_data += other_text
        png_data += b'\x00\x00\x00\x00'
        
        # Add character data tEXt chunk
        json_data = json.dumps(self.sample_character_data)
        encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        chara_key = b'chara'
        chara_text = chara_key + b'\x00' + encoded_data.encode('utf-8')
        chara_length = len(chara_text)
        
        png_data += struct.pack('>I', chara_length)
        png_data += b'tEXt'
        png_data += chara_text
        png_data += b'\x00\x00\x00\x00'
        
        # Add IEND chunk
        png_data += struct.pack('>I', 0)
        png_data += b'IEND'
        png_data += b'\x00\x00\x00\x00'
        
        result = self.parser._extract_character_text(png_data)
        
        assert result is not None
        assert result == encoded_data