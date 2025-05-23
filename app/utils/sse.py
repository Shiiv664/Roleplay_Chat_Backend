"""Server-Sent Events (SSE) utilities."""

import json
from typing import Any, Dict


def format_sse_event(data: Dict[str, Any]) -> str:
    r"""Format data as an SSE event.

    Args:
        data: Dictionary containing event data

    Returns:
        Formatted SSE event string with 'data:' prefix and double newline

    Example:
        >>> format_sse_event({"type": "content", "data": "Hello"})
        'data: {"type": "content", "data": "Hello"}\n\n'
    """
    return f"data: {json.dumps(data)}\n\n"


def format_content_event(content: str) -> str:
    """Format a content chunk as an SSE event.

    Args:
        content: Content string to send

    Returns:
        Formatted SSE event for content
    """
    return format_sse_event({"type": "content", "data": content})


def format_done_event() -> str:
    """Format a completion event.

    Returns:
        Formatted SSE event for completion
    """
    return format_sse_event({"type": "done"})


def format_error_event(error: str) -> str:
    """Format an error event.

    Args:
        error: Error message

    Returns:
        Formatted SSE event for error
    """
    return format_sse_event({"type": "error", "error": error})


def format_cancelled_event(reason: str = "user_cancelled") -> str:
    """Format a cancellation event.

    Args:
        reason: Reason for cancellation

    Returns:
        Formatted SSE event for cancellation
    """
    return format_sse_event({"type": "cancelled", "reason": reason})
