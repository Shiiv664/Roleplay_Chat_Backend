"""Encryption utilities for secure data storage."""

import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self) -> None:
        """Initialize the encryption service with key from environment."""
        self._key = self._get_encryption_key()
        self._fernet = Fernet(self._key)

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment variable or auto-generate if needed.

        Returns:
            The encryption key as bytes.

        Raises:
            ValueError: If key generation or storage fails.
        """
        # Try environment variable first
        key_str = os.getenv("ENCRYPTION_KEY")

        # If not found, try reading from environment-specific key file
        if not key_str:
            env = os.getenv("FLASK_ENV", "development")
            key_file_path = f"encryption_{env}.key"
            
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, "r") as f:
                        key_str = f.read().strip()
                except OSError as e:
                    raise ValueError(f"Failed to read encryption key file {key_file_path}: {e}")

        # If still not found, try fallback encryption.key file
        if not key_str:
            key_file_path = "encryption.key"
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, "r") as f:
                        key_str = f.read().strip()
                except OSError as e:
                    raise ValueError(f"Failed to read encryption key file: {e}")

        # If still not found, auto-generate and store
        if not key_str:
            key_str = self._auto_generate_and_store_key()

        return key_str.encode()
    
    def _auto_generate_and_store_key(self) -> str:
        """Auto-generate encryption key and store it appropriately.
        
        Returns:
            The generated encryption key as string.
        """
        # Generate new encryption key
        key_str = Fernet.generate_key().decode()
        
        # Try to append to the appropriate .env file first
        env = os.getenv("FLASK_ENV", "development")
        env_file_path = f".env.{env}"
        
        if Path(env_file_path).exists():
            try:
                # Read current content
                with open(env_file_path, "r") as f:
                    content = f.read()
                
                # Check if ENCRYPTION_KEY already exists (empty value)
                if "ENCRYPTION_KEY=" in content:
                    # Replace empty ENCRYPTION_KEY= with the generated key
                    content = content.replace("ENCRYPTION_KEY=", f"ENCRYPTION_KEY={key_str}")
                else:
                    # Append the key
                    if not content.endswith("\n"):
                        content += "\n"
                    content += f"ENCRYPTION_KEY={key_str}\n"
                
                # Write back to file
                with open(env_file_path, "w") as f:
                    f.write(content)
                
                print(f"Auto-generated encryption key and stored in {env_file_path}")
                return key_str
                
            except OSError as e:
                print(f"Warning: Failed to write to {env_file_path}: {e}")
        
        # Fallback: create environment-specific key file
        env_key_file = f"encryption_{env}.key"
        try:
            with open(env_key_file, "w") as f:
                f.write(key_str)
            print(f"Auto-generated encryption key and stored in {env_key_file}")
            return key_str
        except OSError as e:
            print(f"Warning: Failed to write to {env_key_file}: {e}")
        
        # Final fallback: create generic key file
        try:
            with open("encryption.key", "w") as f:
                f.write(key_str)
            print("Auto-generated encryption key and stored in encryption.key")
            return key_str
        except OSError as e:
            raise ValueError(f"Failed to auto-generate and store encryption key: {e}")
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a secure Flask SECRET_KEY.
        
        Returns:
            A cryptographically secure random secret key.
        """
        return secrets.token_urlsafe(32)

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
