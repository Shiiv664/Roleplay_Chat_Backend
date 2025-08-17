"""Configuration settings for the application."""

import os
import secrets
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load environment variables from environment-specific .env file
env = os.getenv("FLASK_ENV", "development")
env_file = f".env.{env}"
if Path(env_file).exists():
    load_dotenv(env_file)
else:
    # Fallback to generic .env file
    load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


def _auto_generate_secret_key() -> str:
    """Auto-generate Flask SECRET_KEY if not provided in environment.
    
    Returns:
        A cryptographically secure secret key.
    """
    # Generate a secure key
    secret_key = secrets.token_urlsafe(32)
    
    # Try to store it in the current environment file
    env = os.getenv("FLASK_ENV", "development")
    env_file_path = f".env.{env}"
    
    if Path(env_file_path).exists():
        try:
            # Read current content
            with open(env_file_path, "r") as f:
                content = f.read()
            
            # Check if SECRET_KEY already exists (empty value)
            if "SECRET_KEY=" in content and "SECRET_KEY=\n" in content:
                # Replace empty SECRET_KEY= with the generated key
                content = content.replace("SECRET_KEY=", f"SECRET_KEY={secret_key}")
                
                # Write back to file
                with open(env_file_path, "w") as f:
                    f.write(content)
                
                print(f"Auto-generated SECRET_KEY and stored in {env_file_path}")
            elif "SECRET_KEY=" not in content:
                # Append the key if not present
                if not content.endswith("\n"):
                    content += "\n"
                content += f"SECRET_KEY={secret_key}\n"
                
                with open(env_file_path, "w") as f:
                    f.write(content)
                
                print(f"Auto-generated SECRET_KEY and stored in {env_file_path}")
                
        except OSError as e:
            print(f"Warning: Failed to write SECRET_KEY to {env_file_path}: {e}")
    
    return secret_key


class Config:
    """Base configuration class."""

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR}/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Flask configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY") or _auto_generate_secret_key()
    DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    
    # Host and port configuration
    HOST: str = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    # Application settings
    APP_NAME: str = "LLM Roleplay Chat Client"
    API_VERSION: str = "v1"

    # OpenRouter API streaming configuration
    OPENROUTER_TIMEOUT: int = int(os.getenv("OPENROUTER_TIMEOUT", "120"))  # seconds
    OPENROUTER_STREAM_CHUNK_SIZE: int = int(
        os.getenv("OPENROUTER_STREAM_CHUNK_SIZE", "1024")
    )  # bytes
    OPENROUTER_MAX_CONNECTIONS_PER_SESSION: int = int(
        os.getenv("OPENROUTER_MAX_CONNECTIONS_PER_SESSION", "5")
    )
    OPENROUTER_STREAM_TIMEOUT: int = int(
        os.getenv("OPENROUTER_STREAM_TIMEOUT", "300")
    )  # seconds
    OPENROUTER_CONNECTION_POOL_SIZE: int = int(
        os.getenv("OPENROUTER_CONNECTION_POOL_SIZE", "10")
    )
    OPENROUTER_MAX_RETRIES: int = int(os.getenv("OPENROUTER_MAX_RETRIES", "3"))

    # Claude Code CLI configuration
    CLAUDE_CODE_EXECUTABLE_PATH: str = os.getenv("CLAUDE_CODE_EXECUTABLE_PATH", "claude")
    CLAUDE_CODE_TIMEOUT: int = int(os.getenv("CLAUDE_CODE_TIMEOUT", "120"))  # seconds

    # Encryption configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DEV_DATABASE_URL", f"sqlite:///{BASE_DIR}/app.db"
    )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")

    @classmethod
    def is_valid(cls) -> bool:
        """Validate production configuration."""
        return all([cls.SQLALCHEMY_DATABASE_URI, cls.SECRET_KEY])


# Configuration dictionary
config: Dict[str, Config] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Get the current configuration based on environment."""
    env = os.getenv("FLASK_ENV", "development")
    return config.get(env, config["default"])
