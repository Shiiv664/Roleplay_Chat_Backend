"""Encryption utilities for secure data storage."""

import os

from cryptography.fernet import Fernet


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self) -> None:
        """Initialize the encryption service with key from environment."""
        self._key = self._get_encryption_key()
        self._fernet = Fernet(self._key)

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment variable or key file.

        Returns:
            The encryption key as bytes.

        Raises:
            ValueError: If neither ENCRYPTION_KEY environment variable nor encryption.key file is found.
        """
        # Try environment variable first
        key_str = os.getenv("ENCRYPTION_KEY")

        # If not found, try reading from encryption.key file
        if not key_str:
            key_file_path = "encryption.key"
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, "r") as f:
                        key_str = f.read().strip()
                except OSError as e:
                    raise ValueError(f"Failed to read encryption key file: {e}")

        if not key_str:
            raise ValueError(
                "Encryption key not found. Either set ENCRYPTION_KEY environment variable "
                "or create an encryption.key file. Generate a key with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' > encryption.key"
            )

        return key_str.encode()

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage.

        Args:
            api_key: The plaintext API key to encrypt.

        Returns:
            The encrypted API key as a base64-encoded string.
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        encrypted_bytes = self._fernet.encrypt(api_key.encode())
        return encrypted_bytes.decode()

    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt an API key from storage.

        Args:
            encrypted_api_key: The encrypted API key as a base64-encoded string.

        Returns:
            The decrypted API key as plaintext.

        Raises:
            ValueError: If the encrypted key is invalid or cannot be decrypted.
        """
        if not encrypted_api_key:
            raise ValueError("Encrypted API key cannot be empty")

        try:
            decrypted_bytes = self._fernet.decrypt(encrypted_api_key.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {e}")

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key for use in ENCRYPTION_KEY environment variable.

        Returns:
            A base64-encoded encryption key.
        """
        return Fernet.generate_key().decode()


# Global instance for application use
encryption_service = EncryptionService()
