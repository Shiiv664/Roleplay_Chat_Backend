"""Tests for Character Extract PNG API endpoint."""

import json
import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from app.api.namespaces.characters import api
from app.utils.exceptions import ValidationError, ProcessingError


class TestCharacterExtractApi:
    """Test class for Character Extract PNG API."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = None  # Will be set by conftest.py
        
        # Mock extraction result
        self.mock_extraction_result = {
            'character_data': {
                'name': 'Test Character',
                'label': 'test_character_imported_20240814',
                'description': 'A test character for API testing',
                'first_messages': [
                    'Hello! I\'m a test character.',
                    'Hi there! Nice to meet you.'
                ]
            },
            'avatar_image': {
                'filename': 'test_character.png',
                'data': 'base64encodedimagedata',
                'mime_type': 'image/png',
                'size_bytes': 1024
            },
            'extraction_info': {
                'source_format': 'Character Card v2',
                'original_filename': 'test.png',
                'extracted_at': '2024-08-14T12:00:00Z',
                'image_info': {
                    'format': 'PNG',
                    'width': 512,
                    'height': 512
                }
            }
        }
    
    def create_test_png_file(self):
        """Create a test PNG file for upload."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_success(self, mock_service_class, test_client):
        """Test successful PNG character extraction."""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.return_value = self.mock_extraction_result
        
        # Create test file
        test_file = self.create_test_png_file()
        
        # Make request
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'character_data' in data['data']
        assert 'avatar_image' in data['data']
        assert 'extraction_info' in data['data']
        
        char_data = data['data']['character_data']
        assert char_data['name'] == 'Test Character'
        assert char_data['label'] == 'test_character_imported_20240814'
        assert len(char_data['first_messages']) == 2
        
        avatar = data['data']['avatar_image']
        assert avatar['filename'] == 'test_character.png'
        assert avatar['mime_type'] == 'image/png'
    
    def test_extract_png_wrong_content_type(self, test_client):
        """Test extraction with wrong content type."""
        response = test_client.post(
            '/api/v1/characters/extract-png',
            json={'test': 'data'},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_REQUEST_FORMAT' in data['error']['message']
    
    def test_extract_png_no_file(self, test_client):
        """Test extraction without file upload."""
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'NO_FILE_PROVIDED' in data['error']['message']
    
    def test_extract_png_wrong_file_extension(self, test_client):
        """Test extraction with wrong file extension."""
        test_file = io.BytesIO(b'fake image data')
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.jpg')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_FILE_FORMAT' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_validation_error(self, mock_service_class, test_client):
        """Test extraction with validation error."""
        # Mock the service to raise validation error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.side_effect = ValidationError(
            "INVALID_FILE_FORMAT", "Not a valid PNG file"
        )
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_FILE_FORMAT' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_no_character_data(self, mock_service_class, test_client):
        """Test extraction with PNG that has no character data."""
        # Mock the service to raise no character data error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.side_effect = ValidationError(
            "NO_CHARACTER_DATA", "PNG contains no Character Card v2 metadata"
        )
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'NO_CHARACTER_DATA' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_invalid_character_data(self, mock_service_class, test_client):
        """Test extraction with invalid character data."""
        # Mock the service to raise invalid character data error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.side_effect = ValidationError(
            "INVALID_CHARACTER_DATA", "Character data is corrupted or invalid"
        )
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_CHARACTER_DATA' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_file_too_large(self, mock_service_class, test_client):
        """Test extraction with file too large."""
        # Mock the service to raise file too large error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.side_effect = ValidationError(
            "FILE_TOO_LARGE", "File size exceeds maximum allowed size"
        )
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'FILE_TOO_LARGE' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_processing_error(self, mock_service_class, test_client):
        """Test extraction with processing error."""
        # Mock the service to raise processing error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.side_effect = ProcessingError(
            "Internal error during extraction"
        )
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_unexpected_error(self, mock_service_class, test_client):
        """Test extraction with unexpected error."""
        # Mock the service to raise unexpected error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.side_effect = Exception("Unexpected error")
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_filename_without_extension(self, mock_service_class, test_client):
        """Test extraction with filename without extension."""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.return_value = self.mock_extraction_result
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'character_without_extension')},
            content_type='multipart/form-data'
        )
        
        # Should fail validation due to missing .png extension
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_FILE_FORMAT' in data['error']['message']
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_service_instantiation(self, mock_service_class, test_client):
        """Test that service is properly instantiated."""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.return_value = self.mock_extraction_result
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        # Verify service was instantiated
        mock_service_class.assert_called_once()
        
        # Verify service methods were called with correct parameters
        mock_service.validate_extraction_request.assert_called_once()
        mock_service.extract_character_from_png.assert_called_once()
        
        # Check the arguments passed to extract_character_from_png
        args, kwargs = mock_service.extract_character_from_png.call_args
        assert len(args) == 2  # file_data, filename
        assert args[1] == 'test.png'  # filename
        assert isinstance(args[0], bytes)  # file_data should be bytes
    
    def test_extract_png_endpoint_documentation(self):
        """Test that endpoint has proper documentation."""
        # This test ensures the endpoint is properly documented
        # by checking the route exists and has the correct configuration
        routes = [rule.rule for rule in api.app.url_map.iter_rules()]
        
        # The exact route will depend on Flask-RESTX namespace setup
        # This is more of a smoke test to ensure the endpoint is registered
        assert any('/extract-png' in route for route in routes)
    
    @patch('app.api.namespaces.characters.CharacterExtractService')
    def test_extract_png_response_structure(self, mock_service_class, test_client):
        """Test that response follows the expected structure."""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.validate_extraction_request.return_value = {'valid': True}
        mock_service.extract_character_from_png.return_value = self.mock_extraction_result
        
        test_file = self.create_test_png_file()
        
        response = test_client.post(
            '/api/v1/characters/extract-png',
            data={'file': (test_file, 'test.png')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check top-level structure
        assert 'success' in data
        assert 'data' in data
        assert data['success'] is True
        
        # Check data structure matches specification
        extraction_data = data['data']
        assert 'character_data' in extraction_data
        assert 'avatar_image' in extraction_data
        assert 'extraction_info' in extraction_data
        
        # Check character_data structure
        char_data = extraction_data['character_data']
        required_char_fields = ['name', 'label', 'description', 'first_messages']
        for field in required_char_fields:
            assert field in char_data
        
        # Check avatar_image structure
        avatar = extraction_data['avatar_image']
        required_avatar_fields = ['filename', 'data', 'mime_type']
        for field in required_avatar_fields:
            assert field in avatar
        
        # Check extraction_info structure
        info = extraction_data['extraction_info']
        required_info_fields = ['source_format', 'original_filename', 'extracted_at']
        for field in required_info_fields:
            assert field in info