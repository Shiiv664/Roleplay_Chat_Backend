"""Tests for encryption utility."""

import os
from unittest.mock import mock_open, patch

import pytest

from app.utils.encryption import EncryptionService


class TestEncryptionService:
    """Test encryption service functionality."""

    def test_encrypt_decrypt_api_key_success(self):
        """Test successful encryption and decryption of API key."""
        # Generate a test key
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            # Test data
            original_key = "sk-or-test-api-key-123456789"

            # Encrypt
            encrypted = service.encrypt_api_key(original_key)
            assert encrypted != original_key
            assert len(encrypted) > len(original_key)

            # Decrypt
            decrypted = service.decrypt_api_key(encrypted)
            assert decrypted == original_key

    def test_encrypt_api_key_empty_string(self):
        """Test encryption fails with empty API key."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            with pytest.raises(ValueError, match="API key cannot be empty"):
                service.encrypt_api_key("")

    def test_encrypt_api_key_none(self):
        """Test encryption fails with None API key."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            with pytest.raises(ValueError, match="API key cannot be empty"):
                service.encrypt_api_key(None)

    def test_decrypt_api_key_empty_string(self):
        """Test decryption fails with empty encrypted key."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            with pytest.raises(ValueError, match="Encrypted API key cannot be empty"):
                service.decrypt_api_key("")

    def test_decrypt_api_key_invalid_data(self):
        """Test decryption fails with invalid encrypted data."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            with pytest.raises(ValueError, match="Failed to decrypt API key"):
                service.decrypt_api_key("invalid-encrypted-data")

    def test_initialization_with_environment_variable(self):
        """Test service initialization with environment variable."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()
            assert service._key == test_key.encode()

    def test_initialization_with_key_file(self):
        """Test service initialization with key file."""
        test_key = EncryptionService.generate_key()

        # Mock file reading
        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=test_key)):
                    service = EncryptionService()
                    assert service._key == test_key.encode()

    def test_initialization_file_read_error(self):
        """Test service initialization handles file read errors."""
        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=IOError("File not accessible")):
                    with pytest.raises(
                        ValueError, match="Failed to read encryption key file"
                    ):
                        EncryptionService()

    def test_initialization_no_key_source(self):
        """Test service initialization fails when no key source available."""
        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with patch("os.path.exists", return_value=False):
                with pytest.raises(ValueError, match="Encryption key not found"):
                    EncryptionService()

    def test_generate_key_returns_valid_key(self):
        """Test that generate_key returns a valid Fernet key."""
        key = EncryptionService.generate_key()

        # Test that the generated key can be used
        with patch.dict(os.environ, {"ENCRYPTION_KEY": key}):
            service = EncryptionService()

            # Should be able to encrypt/decrypt successfully
            test_data = "test-api-key"
            encrypted = service.encrypt_api_key(test_data)
            decrypted = service.decrypt_api_key(encrypted)
            assert decrypted == test_data

    def test_multiple_encryption_operations(self):
        """Test multiple encryption operations produce different results."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            original_key = "sk-or-test-api-key-123456789"

            # Encrypt the same data multiple times
            encrypted1 = service.encrypt_api_key(original_key)
            encrypted2 = service.encrypt_api_key(original_key)

            # Results should be different (Fernet includes timestamp/nonce)
            assert encrypted1 != encrypted2

            # But both should decrypt to the same original
            assert service.decrypt_api_key(encrypted1) == original_key
            assert service.decrypt_api_key(encrypted2) == original_key

    def test_encryption_with_special_characters(self):
        """Test encryption works with special characters in API keys."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            # API key with special characters
            original_key = "sk-or-test_api.key+with/special=chars-123"

            encrypted = service.encrypt_api_key(original_key)
            decrypted = service.decrypt_api_key(encrypted)

            assert decrypted == original_key

    def test_encryption_with_unicode_characters(self):
        """Test encryption works with unicode characters."""
        test_key = EncryptionService.generate_key()

        with patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
            service = EncryptionService()

            # API key with unicode characters
            original_key = "sk-or-tëst-ápì-kéy-üñîcödé-123"

            encrypted = service.encrypt_api_key(original_key)
            decrypted = service.decrypt_api_key(encrypted)

            assert decrypted == original_key
