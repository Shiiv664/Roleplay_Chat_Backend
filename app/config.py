"""Configuration settings for the application."""

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration class."""

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR}/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Flask configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

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
