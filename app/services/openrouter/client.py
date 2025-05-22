"""OpenRouter API client for LLM interactions."""

import json
import logging
from typing import Any, Dict, Iterator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    def __init__(self, api_key: str, timeout: int = 120) -> None:
        """Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key for authentication
            timeout: Request timeout in seconds

        Raises:
            ValidationError: If API key is invalid
        """
        if not api_key or not api_key.strip():
            raise ValidationError("OpenRouter API key is required")

        self.api_key = api_key.strip()
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = timeout

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(
        self, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get request headers with authentication and optional extras.

        Args:
            extra_headers: Additional headers to include

        Returns:
            Dictionary of request headers
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://llm-roleplay-chat-client.local",
            "X-Title": "LLM Roleplay Chat Client V3",
        }

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare and validate message format for OpenRouter API.

        Args:
            messages: List of messages with 'role' and 'content' keys

        Returns:
            Validated list of messages

        Raises:
            ValidationError: If message format is invalid
        """
        if not messages:
            raise ValidationError("Messages list cannot be empty")

        validated_messages = []
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValidationError(f"Message {i} must be a dictionary")

            if "role" not in message or "content" not in message:
                raise ValidationError(
                    f"Message {i} must have 'role' and 'content' keys"
                )

            if message["role"] not in ["system", "user", "assistant"]:
                raise ValidationError(
                    f"Message {i} has invalid role: {message['role']}"
                )

            if (
                not isinstance(message["content"], str)
                or not message["content"].strip()
            ):
                raise ValidationError(f"Message {i} content must be a non-empty string")

            validated_messages.append(
                {"role": message["role"], "content": message["content"].strip()}
            )

        return validated_messages

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Send a chat completion request to OpenRouter.

        Args:
            model: Model identifier (e.g., "openai/gpt-4o")
            messages: List of messages with 'role' and 'content' keys
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            API response dictionary

        Raises:
            ValidationError: If request parameters are invalid
            Exception: If API request fails
        """
        if not model or not model.strip():
            raise ValidationError("Model identifier is required")

        validated_messages = self._prepare_messages(messages)

        payload = {
            "model": model.strip(),
            "messages": validated_messages,
            "stream": stream,
            **kwargs,
        }

        try:
            logger.info(f"Sending chat completion request to model: {model}")
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
                stream=stream,
            )
            response.raise_for_status()

            if stream:
                return {"stream": response}
            else:
                return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"OpenRouter API request failed: {e}")

    def chat_completion_stream(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """Stream a chat completion response from OpenRouter.

        Args:
            model: Model identifier (e.g., "openai/gpt-4o")
            messages: List of messages with 'role' and 'content' keys
            **kwargs: Additional parameters for the API

        Yields:
            Parsed SSE chunks as dictionaries

        Raises:
            ValidationError: If request parameters are invalid
            Exception: If API request fails
        """
        response_data = self.chat_completion(model, messages, stream=True, **kwargs)
        response = response_data["stream"]

        try:
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    buffer += chunk

                    while True:
                        line_end = buffer.find("\n")
                        if line_end == -1:
                            break

                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1 :]

                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                return

                            if data.startswith(": "):
                                # Skip comments like ": OPENROUTER PROCESSING"
                                continue

                            try:
                                data_obj = json.loads(data)
                                yield data_obj
                            except json.JSONDecodeError:
                                # Skip invalid JSON chunks
                                continue

        except Exception as e:
            logger.error(f"Error processing OpenRouter stream: {e}")
            raise Exception(f"Stream processing failed: {e}")
        finally:
            response.close()

    def test_connection(self) -> bool:
        """Test the connection to OpenRouter API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            self.chat_completion("openai/gpt-3.5-turbo", test_messages)
            return True
        except Exception as e:
            logger.error(f"OpenRouter connection test failed: {e}")
            return False
