"""OpenRouter streaming response handler."""

import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from app.config import get_config
from app.services.openrouter.client import OpenRouterClient

logger = logging.getLogger(__name__)


class StreamState:
    """Represents the state of an active stream."""

    def __init__(self, stream_id: str, chat_session_id: int, model: str):
        """Initialize stream state.

        Args:
            stream_id: Unique identifier for this stream
            chat_session_id: ID of the chat session
            model: AI model being used
        """
        self.stream_id = stream_id
        self.chat_session_id = chat_session_id
        self.model = model
        self.is_active = True
        self.accumulated_content = ""
        self.start_time = time.time()
        self.connections: Set[str] = set()
        self.error: Optional[str] = None
        self._lock = threading.Lock()

    def add_content(self, content: str) -> None:
        """Add content to the accumulated message.

        Args:
            content: Content chunk to add
        """
        with self._lock:
            self.accumulated_content += content

    def add_connection(self, connection_id: str) -> None:
        """Add a connection to this stream.

        Args:
            connection_id: Unique identifier for the connection
        """
        with self._lock:
            self.connections.add(connection_id)

    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from this stream.

        Args:
            connection_id: Unique identifier for the connection
        """
        with self._lock:
            self.connections.discard(connection_id)

    def has_connections(self) -> bool:
        """Check if stream has any active connections.

        Returns:
            True if there are active connections, False otherwise
        """
        with self._lock:
            return len(self.connections) > 0

    def stop(self, error: Optional[str] = None) -> None:
        """Stop the stream.

        Args:
            error: Optional error message if stream stopped due to error
        """
        with self._lock:
            self.is_active = False
            self.error = error


class StreamingHandler:
    """Handles OpenRouter streaming responses and state management."""

    def __init__(self):
        """Initialize the streaming handler."""
        self._active_streams: Dict[int, StreamState] = {}
        self._stream_lock = threading.Lock()

    def get_active_stream(self, chat_session_id: int) -> Optional[StreamState]:
        """Get the active stream for a chat session.

        Args:
            chat_session_id: ID of the chat session

        Returns:
            StreamState if active, None otherwise
        """
        with self._stream_lock:
            return self._active_streams.get(chat_session_id)

    def start_stream(
        self,
        chat_session_id: int,
        client: OpenRouterClient,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> StreamState:
        """Start a new streaming request.

        Args:
            chat_session_id: ID of the chat session
            client: OpenRouter client instance
            model: AI model to use
            messages: Messages to send to the AI
            **kwargs: Additional parameters for the API

        Returns:
            StreamState for the new stream

        Raises:
            ValueError: If a stream is already active for this session
        """
        with self._stream_lock:
            if chat_session_id in self._active_streams:
                raise ValueError(f"Stream already active for session {chat_session_id}")

            stream_id = str(uuid.uuid4())
            stream_state = StreamState(stream_id, chat_session_id, model)
            self._active_streams[chat_session_id] = stream_state

        logger.info(f"Starting stream {stream_id} for session {chat_session_id}")

        # Start streaming in a separate thread
        thread = threading.Thread(
            target=self._process_stream,
            args=(stream_state, client, model, messages, kwargs),
            daemon=True,
        )
        thread.start()

        return stream_state

    def stop_stream(self, chat_session_id: int, reason: str = "user_cancelled") -> bool:
        """Stop an active stream.

        Args:
            chat_session_id: ID of the chat session
            reason: Reason for stopping the stream

        Returns:
            True if stream was stopped, False if no active stream
        """
        with self._stream_lock:
            stream_state = self._active_streams.get(chat_session_id)
            if not stream_state:
                return False

            stream_state.stop(f"Stream cancelled: {reason}")
            logger.info(
                f"Stopped stream {stream_state.stream_id} for session {chat_session_id}"
            )
            return True

    def _process_stream(
        self,
        stream_state: StreamState,
        client: OpenRouterClient,
        model: str,
        messages: List[Dict[str, str]],
        kwargs: Dict[str, Any],
    ) -> None:
        """Process the streaming response in a background thread.

        Args:
            stream_state: State object for this stream
            client: OpenRouter client instance
            model: AI model to use
            messages: Messages to send to the AI
            kwargs: Additional API parameters
        """
        try:
            for chunk in client.chat_completion_stream(model, messages, **kwargs):
                if not stream_state.is_active:
                    break

                # Extract content from chunk
                content = self._extract_content_from_chunk(chunk)
                if content:
                    stream_state.add_content(content)

                # Check if we still have connections
                if not stream_state.has_connections():
                    logger.info(
                        f"No active connections for stream {stream_state.stream_id}, stopping"
                    )
                    break

        except Exception as e:
            logger.error(f"Error in stream {stream_state.stream_id}: {e}")
            stream_state.stop(str(e))
        finally:
            # Clean up stream state
            with self._stream_lock:
                self._active_streams.pop(stream_state.chat_session_id, None)

            stream_state.stop()
            logger.info(f"Stream {stream_state.stream_id} completed")

    def _extract_content_from_chunk(self, chunk: Dict[str, Any]) -> Optional[str]:
        """Extract content from a streaming chunk.

        Args:
            chunk: Parsed JSON chunk from OpenRouter

        Returns:
            Content string if present, None otherwise
        """
        try:
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content")
        except (KeyError, IndexError, TypeError):
            pass
        return None

    def add_connection(
        self, chat_session_id: int, connection_id: str
    ) -> Optional[StreamState]:
        """Add a connection to an active stream.

        Args:
            chat_session_id: ID of the chat session
            connection_id: Unique identifier for the connection

        Returns:
            StreamState if stream exists, None otherwise
        """
        stream_state = self.get_active_stream(chat_session_id)
        if stream_state:
            stream_state.add_connection(connection_id)
            logger.debug(
                f"Added connection {connection_id} to stream {stream_state.stream_id}"
            )
        return stream_state

    def remove_connection(self, chat_session_id: int, connection_id: str) -> None:
        """Remove a connection from an active stream.

        Args:
            chat_session_id: ID of the chat session
            connection_id: Unique identifier for the connection
        """
        stream_state = self.get_active_stream(chat_session_id)
        if stream_state:
            stream_state.remove_connection(connection_id)
            logger.debug(
                f"Removed connection {connection_id} from stream {stream_state.stream_id}"
            )

    def cleanup_inactive_streams(self, max_age_seconds: Optional[int] = None) -> None:
        """Clean up streams that have been inactive for too long.

        Args:
            max_age_seconds: Maximum age in seconds before cleanup (uses config default if None)
        """
        if max_age_seconds is None:
            config = get_config()
            max_age_seconds = config.OPENROUTER_STREAM_TIMEOUT

        current_time = time.time()
        to_remove = []

        with self._stream_lock:
            for chat_session_id, stream_state in self._active_streams.items():
                age = current_time - stream_state.start_time
                if age > max_age_seconds and not stream_state.has_connections():
                    to_remove.append(chat_session_id)
                    stream_state.stop("timeout")

            for chat_session_id in to_remove:
                self._active_streams.pop(chat_session_id, None)
                logger.info(f"Cleaned up inactive stream for session {chat_session_id}")


# Global streaming handler instance
streaming_handler = StreamingHandler()
