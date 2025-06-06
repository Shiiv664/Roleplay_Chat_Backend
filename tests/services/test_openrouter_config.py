"""Tests for OpenRouter configuration integration."""

import os
from unittest.mock import patch

from cryptography.fernet import Fernet

from app.config import get_config
from app.services.openrouter.client import OpenRouterClient
from app.services.openrouter.streaming import StreamingHandler


class TestOpenRouterConfig:
    """Test OpenRouter configuration integration."""

    def test_config_default_values(self):
        """Test that config default values are properly set."""
        config = get_config()

        # Check default timeout
        assert config.OPENROUTER_TIMEOUT == 120
        assert config.OPENROUTER_STREAM_CHUNK_SIZE == 1024
        assert config.OPENROUTER_MAX_CONNECTIONS_PER_SESSION == 5
        assert config.OPENROUTER_STREAM_TIMEOUT == 300
        assert config.OPENROUTER_CONNECTION_POOL_SIZE == 10
        assert config.OPENROUTER_MAX_RETRIES == 3

    def test_config_environment_override(self):
        """Test that environment variables can override default config values."""
        # Test that the configuration can read environment variables
        with patch.dict(os.environ, {"OPENROUTER_TIMEOUT": "180"}):
            # Import Config class fresh to pick up env vars
            import importlib

            import app.config

            importlib.reload(app.config)
            from app.config import Config

            # Create fresh instance
            config = Config()
            assert config.OPENROUTER_TIMEOUT == 180

    def test_openrouter_client_uses_config_defaults(self):
        """Test that OpenRouter client uses configuration defaults."""
        api_key = Fernet.generate_key().decode()

        with patch("app.services.openrouter.client.get_config") as mock_config:
            mock_config.return_value.OPENROUTER_TIMEOUT = 150
            mock_config.return_value.OPENROUTER_MAX_RETRIES = 4
            mock_config.return_value.OPENROUTER_CONNECTION_POOL_SIZE = 15

            client = OpenRouterClient(api_key)

            assert client.timeout == 150
            # Verify config was called during initialization
            mock_config.assert_called()

    def test_openrouter_client_timeout_override(self):
        """Test that OpenRouter client timeout can be overridden."""
        api_key = Fernet.generate_key().decode()

        with patch("app.services.openrouter.client.get_config") as mock_config:
            mock_config.return_value.OPENROUTER_TIMEOUT = 150

            client = OpenRouterClient(api_key, timeout=200)

            assert client.timeout == 200

    def test_streaming_handler_uses_config_timeout(self):
        """Test that streaming handler uses configuration timeout."""
        handler = StreamingHandler()

        with patch("app.services.openrouter.streaming.get_config") as mock_config:
            mock_config.return_value.OPENROUTER_STREAM_TIMEOUT = 400

            # Test that cleanup uses config timeout when none provided
            handler.cleanup_inactive_streams()

            # Verify config was called
            mock_config.assert_called()

    def test_streaming_handler_timeout_override(self):
        """Test that streaming handler timeout can be overridden."""
        handler = StreamingHandler()

        with patch("app.services.openrouter.streaming.get_config") as mock_config:
            mock_config.return_value.OPENROUTER_STREAM_TIMEOUT = 400

            # Test that explicit timeout overrides config
            handler.cleanup_inactive_streams(max_age_seconds=100)

            # Config should not be called when explicit timeout provided
            mock_config.assert_not_called()

    def test_config_encryption_key_setting(self):
        """Test that encryption key can be set through config."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-key-value"}):
            # Import Config class fresh to pick up env vars
            import importlib

            import app.config

            importlib.reload(app.config)
            from app.config import Config

            config = Config()
            assert config.ENCRYPTION_KEY == "test-key-value"
