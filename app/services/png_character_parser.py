"""
PNG Character Card Parser Service

Extracts Character Card v2 format metadata from PNG files.
This service handles parsing of chub.ai format character cards embedded in PNG tEXt chunks.
"""

import base64
import json
import struct
from typing import Dict, Any, Optional, Tuple
from app.utils.exceptions import ValidationError, ProcessingError


class PngCharacterParser:
    """Service for extracting Character Card v2 data from PNG files."""
    
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    TEXT_CHUNK_TYPE = b'tEXt'
    CHARA_KEY = b'chara'
    
    def extract_character_data(self, png_data: bytes) -> Dict[str, Any]:
        """
        Extract Character Card v2 data from PNG file bytes.
        
        Args:
            png_data: Raw PNG file bytes
            
        Returns:
            Parsed character data dictionary
            
        Raises:
            ValidationError: If PNG format is invalid or no character data found
            ProcessingError: If data extraction or parsing fails
        """
        self._validate_png_format(png_data)
        
        # Extract character metadata from tEXt chunks
        character_text = self._extract_character_text(png_data)
        if not character_text:
            raise ValidationError("NO_CHARACTER_DATA", "PNG contains no Character Card v2 metadata")
        
        # Decode and parse the character data
        try:
            character_data = self._decode_character_data(character_text)
            self._validate_character_card_format(character_data)
            return character_data
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            raise ProcessingError(f"Failed to parse character data: {str(e)}")
    
    def _validate_png_format(self, png_data: bytes) -> None:
        """Validate that the data is a valid PNG file."""
        if len(png_data) < 8:
            raise ValidationError("INVALID_FILE_FORMAT", "File too small to be a valid PNG")
        
        if png_data[:8] != self.PNG_SIGNATURE:
            raise ValidationError("INVALID_FILE_FORMAT", "File is not a valid PNG image")
    
    def _extract_character_text(self, png_data: bytes) -> Optional[str]:
        """
        Extract character data from PNG tEXt chunks.
        
        Args:
            png_data: Raw PNG file bytes
            
        Returns:
            Base64-encoded character data string or None if not found
        """
        offset = 8  # Skip PNG signature
        
        while offset < len(png_data) - 8:
            try:
                # Read chunk length (4 bytes, big-endian)
                length = struct.unpack('>I', png_data[offset:offset+4])[0]
                offset += 4
                
                # Read chunk type (4 bytes)
                chunk_type = png_data[offset:offset+4]
                offset += 4
                
                # Check if this is a tEXt chunk
                if chunk_type == self.TEXT_CHUNK_TYPE:
                    chunk_data = png_data[offset:offset+length]
                    
                    # Find null separator between keyword and text
                    null_pos = chunk_data.find(b'\x00')
                    if null_pos != -1:
                        keyword = chunk_data[:null_pos]
                        text_data = chunk_data[null_pos+1:]
                        
                        # Check if this is the character data chunk
                        if keyword == self.CHARA_KEY:
                            return text_data.decode('utf-8', errors='ignore')
                
                # Skip chunk data and CRC (4 bytes)
                offset += length + 4
                
                # Break if we've reached the end chunk
                if chunk_type == b'IEND':
                    break
                    
            except (struct.error, UnicodeDecodeError, IndexError):
                # Skip malformed chunks
                offset += 1
                continue
        
        return None
    
    def _decode_character_data(self, encoded_data: str) -> Dict[str, Any]:
        """
        Decode base64-encoded character data and parse JSON.
        
        Args:
            encoded_data: Base64-encoded JSON string
            
        Returns:
            Parsed character data dictionary
            
        Raises:
            ValueError: If base64 decoding fails
            json.JSONDecodeError: If JSON parsing fails
        """
        try:
            # Decode base64 data
            decoded_bytes = base64.b64decode(encoded_data)
            decoded_text = decoded_bytes.decode('utf-8')
            
            # Parse JSON
            character_data = json.loads(decoded_text)
            return character_data
            
        except Exception as e:
            raise ValueError(f"Failed to decode character data: {str(e)}")
    
    def _validate_character_card_format(self, data: Dict[str, Any]) -> None:
        """
        Validate that the data follows Character Card v2 format.
        
        Args:
            data: Parsed character data dictionary
            
        Raises:
            ValidationError: If format is invalid
        """
        # Check for required top-level structure
        if not isinstance(data, dict):
            raise ValidationError("INVALID_CHARACTER_DATA", "Character data must be a JSON object")
        
        # Check for spec field
        if data.get('spec') != 'chara_card_v2':
            raise ValidationError("INVALID_CHARACTER_DATA", "Invalid or missing Character Card v2 spec")
        
        # Check for data field
        if 'data' not in data or not isinstance(data['data'], dict):
            raise ValidationError("INVALID_CHARACTER_DATA", "Missing or invalid character data field")
        
        char_data = data['data']
        
        # Check for required fields
        required_fields = ['name', 'description']
        for field in required_fields:
            if not char_data.get(field):
                raise ValidationError("INVALID_CHARACTER_DATA", f"Missing required field: {field}")
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Return information about supported formats."""
        return {
            'format': 'Character Card v2 (chub.ai)',
            'specification': 'chara_card_v2',
            'version': '2.0',
            'encoding': 'base64',
            'storage': 'PNG tEXt chunks'
        }