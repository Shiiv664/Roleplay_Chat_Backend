"""OpenRouter API client for LLM interactions."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_config
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Debug mode - can be controlled via environment variables
DEBUG_OPENROUTER = os.getenv('DEBUG_OPENROUTER', 'false').lower() == 'true'
LOG_OPENROUTER_PAYLOAD = os.getenv('LOG_OPENROUTER_PAYLOAD', 'false').lower() == 'true'

# Set up loggers based on environment variables
debug_logger = None
payload_logger = None

if DEBUG_OPENROUTER or LOG_OPENROUTER_PAYLOAD:
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

if DEBUG_OPENROUTER:
    # Full debug logging (verbose)
    debug_logger = logging.getLogger('openrouter_debug')
    debug_logger.setLevel(logging.DEBUG)
    debug_handler = logging.FileHandler(logs_dir / 'openrouter_debug.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)

if LOG_OPENROUTER_PAYLOAD:
    # Payload-only logging (clean JSON output)
    payload_logger = logging.getLogger('openrouter_payload')
    payload_logger.setLevel(logging.INFO)
    payload_handler = logging.FileHandler(logs_dir / 'openrouter_payload.log')
    payload_handler.setLevel(logging.INFO)
    # Simple formatter for clean JSON output
    payload_formatter = logging.Formatter('%(asctime)s - %(message)s')
    payload_handler.setFormatter(payload_formatter)
    payload_logger.addHandler(payload_handler)


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    def __init__(self, api_key: str, timeout: Optional[int] = None) -> None:
        """Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key for authentication
            timeout: Request timeout in seconds (uses config default if None)

        Raises:
            ValidationError: If API key is invalid
        """
        if not api_key or not api_key.strip():
            raise ValidationError("OpenRouter API key is required")

        config = get_config()
        self.api_key = api_key.strip()
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = timeout or config.OPENROUTER_TIMEOUT

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.OPENROUTER_MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=config.OPENROUTER_CONNECTION_POOL_SIZE,
            pool_maxsize=config.OPENROUTER_CONNECTION_POOL_SIZE,
        )
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

        # Always log essential info
        logger.info(f"Sending chat completion request to model: {model}")

        # LOG OPENROUTER PAYLOAD - Clean JSON output for frequent checking
        if LOG_OPENROUTER_PAYLOAD and payload_logger:
            payload_logger.info(f"🤖 Model: {model.strip()}")
            payload_logger.info("📤 Request Payload:")
            payload_logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            payload_logger.info("-" * 40)

        # DEBUG LOGGING - Verbose output only when full debugging is enabled
        if DEBUG_OPENROUTER and debug_logger:
            debug_logger.info("=" * 80)
            debug_logger.info(f"🚀 OPENROUTER REQUEST - {datetime.now().isoformat()}")
            debug_logger.info("=" * 80)
            debug_logger.info(f"📍 Endpoint: POST {self.base_url}/chat/completions")
            debug_logger.info(f"🤖 Model: {model.strip()}")
            debug_logger.info(f"📨 Stream Mode: {stream}")
            debug_logger.info(f"🔧 Additional Parameters: {kwargs}")
            debug_logger.info("-" * 40)
            debug_logger.info("📝 COMPLETE PAYLOAD:")
            debug_logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
            debug_logger.info("-" * 40)
            debug_logger.info("💬 MESSAGES BREAKDOWN:")
            for i, msg in enumerate(validated_messages):
                debug_logger.info(f"  Message {i+1} ({msg['role']}):")
                debug_logger.info(f"    Content: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
            debug_logger.info("-" * 40)
            debug_logger.info("🔑 HEADERS:")
            headers = self._get_headers()
            safe_headers = {k: v if k != 'Authorization' else f"Bearer {v[7:15]}..." for k, v in headers.items()}
            debug_logger.info(json.dumps(safe_headers, indent=2))
            debug_logger.info("=" * 80)
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
                stream=stream,
            )
            
            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.info(f"📥 RESPONSE STATUS: {response.status_code}")
                debug_logger.info(f"📥 RESPONSE HEADERS: {dict(response.headers)}")
            
            response.raise_for_status()

            if stream:
                if DEBUG_OPENROUTER and debug_logger:
                    debug_logger.info("🌊 Starting stream processing...")
                return {"stream": response}
            else:
                response_data = response.json()
                if DEBUG_OPENROUTER and debug_logger:
                    debug_logger.info("📋 NON-STREAM RESPONSE:")
                    debug_logger.info(json.dumps(response_data, indent=2, ensure_ascii=False))
                return response_data

        except requests.exceptions.RequestException as e:
            # Always log errors to main logger
            logger.error(f"OpenRouter API request failed: {e}")
            
            # Additional debug logging if enabled
            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.error(f"❌ OPENROUTER API REQUEST FAILED: {e}")
                debug_logger.error(f"❌ Error details: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    debug_logger.error(f"❌ Response status: {e.response.status_code}")
                    debug_logger.error(f"❌ Response text: {e.response.text}")
            
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
        if DEBUG_OPENROUTER and debug_logger:
            debug_logger.info("🌊 STARTING STREAMING REQUEST")
        
        response_data = self.chat_completion(model, messages, stream=True, **kwargs)
        response = response_data["stream"]

        try:
            config = get_config()
            buffer = ""
            chunk_count = 0
            
            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.info("📡 Processing streaming chunks...")
            
            for chunk in response.iter_content(
                chunk_size=config.OPENROUTER_STREAM_CHUNK_SIZE, decode_unicode=True
            ):
                if chunk:
                    buffer += chunk
                    chunk_count += 1
                    
                    # Log every 10th chunk to avoid spam (only in debug mode)
                    if DEBUG_OPENROUTER and debug_logger and chunk_count % 10 == 0:
                        debug_logger.debug(f"📦 Processed {chunk_count} chunks, buffer size: {len(buffer)}")

                    while True:
                        line_end = buffer.find("\n")
                        if line_end == -1:
                            break

                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1 :]

                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                if DEBUG_OPENROUTER and debug_logger:
                                    debug_logger.info("✅ Stream completed with [DONE] marker")
                                return

                            if data.startswith(": "):
                                # Skip comments like ": OPENROUTER PROCESSING"
                                if DEBUG_OPENROUTER and debug_logger:
                                    debug_logger.debug(f"💭 SSE Comment: {data}")
                                continue

                            try:
                                data_obj = json.loads(data)
                                
                                # Log the parsed data object (only in debug mode)
                                if DEBUG_OPENROUTER and debug_logger:
                                    if data_obj.get("choices") and data_obj["choices"][0].get("delta"):
                                        delta = data_obj["choices"][0]["delta"]
                                        if delta.get("content"):
                                            debug_logger.debug(f"📝 Content chunk: '{delta['content']}'")
                                        else:
                                            debug_logger.debug(f"🔄 Delta (no content): {delta}")
                                    else:
                                        debug_logger.debug(f"📊 Stream data: {data_obj}")
                                
                                yield data_obj
                            except json.JSONDecodeError as parse_error:
                                if DEBUG_OPENROUTER and debug_logger:
                                    debug_logger.warning(f"⚠️ Failed to parse JSON: {data}")
                                    debug_logger.warning(f"⚠️ Parse error: {parse_error}")
                                # Skip invalid JSON chunks
                                continue

            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.info(f"📊 Stream processing complete. Total chunks: {chunk_count}")

        except Exception as e:
            # Always log errors
            logger.error(f"Error processing OpenRouter stream: {e}")
            
            # Additional debug logging if enabled
            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.error(f"❌ Error processing OpenRouter stream: {e}")
                debug_logger.error(f"❌ Error type: {type(e).__name__}")
            
            raise Exception(f"Stream processing failed: {e}")
        finally:
            if DEBUG_OPENROUTER and debug_logger:
                debug_logger.info("🔒 Closing response stream")
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
