"""Tests for SSE (Server-Sent Events) utilities."""

import json

from app.utils.sse import (
    format_cancelled_event,
    format_content_event,
    format_done_event,
    format_error_event,
    format_sse_event,
)


class TestFormatSSEEvent:
    """Test cases for format_sse_event function."""

    def test_format_simple_event(self):
        """Test formatting a simple event."""
        data = {"type": "test", "value": 123}
        result = format_sse_event(data)
        assert result == 'data: {"type": "test", "value": 123}\n\n'

    def test_format_empty_dict(self):
        """Test formatting an empty dictionary."""
        result = format_sse_event({})
        assert result == "data: {}\n\n"

    def test_format_nested_data(self):
        """Test formatting nested data structures."""
        data = {"type": "complex", "nested": {"level1": {"level2": ["a", "b", "c"]}}}
        result = format_sse_event(data)
        expected_json = json.dumps(data)
        assert result == f"data: {expected_json}\n\n"

    def test_format_with_special_characters(self):
        """Test formatting with special characters."""
        data = {"text": 'Hello\nWorld\t"quoted"'}
        result = format_sse_event(data)
        expected_json = json.dumps(data)
        assert result == f"data: {expected_json}\n\n"


class TestContentEvent:
    """Test cases for format_content_event function."""

    def test_format_simple_content(self):
        """Test formatting simple content."""
        result = format_content_event("Hello world")
        assert result == 'data: {"type": "content", "data": "Hello world"}\n\n'

    def test_format_empty_content(self):
        """Test formatting empty content."""
        result = format_content_event("")
        assert result == 'data: {"type": "content", "data": ""}\n\n'

    def test_format_multiline_content(self):
        """Test formatting multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        result = format_content_event(content)
        expected = 'data: {"type": "content", "data": "Line 1\\nLine 2\\nLine 3"}\n\n'
        assert result == expected

    def test_format_content_with_quotes(self):
        """Test formatting content with quotes."""
        content = 'He said "Hello"'
        result = format_content_event(content)
        expected = 'data: {"type": "content", "data": "He said \\"Hello\\""}\n\n'
        assert result == expected


class TestDoneEvent:
    """Test cases for format_done_event function."""

    def test_format_done_event(self):
        """Test formatting done event."""
        result = format_done_event()
        assert result == 'data: {"type": "done"}\n\n'


class TestErrorEvent:
    """Test cases for format_error_event function."""

    def test_format_simple_error(self):
        """Test formatting simple error message."""
        result = format_error_event("Something went wrong")
        assert result == 'data: {"type": "error", "error": "Something went wrong"}\n\n'

    def test_format_detailed_error(self):
        """Test formatting detailed error message."""
        error_msg = "API rate limit exceeded: 429 Too Many Requests"
        result = format_error_event(error_msg)
        expected = f'data: {{"type": "error", "error": "{error_msg}"}}\n\n'
        assert result == expected

    def test_format_error_with_special_chars(self):
        """Test formatting error with special characters."""
        error_msg = 'Error: "Invalid JSON"\nDetails: {}'
        result = format_error_event(error_msg)
        expected_json = json.dumps({"type": "error", "error": error_msg})
        assert result == f"data: {expected_json}\n\n"


class TestCancelledEvent:
    """Test cases for format_cancelled_event function."""

    def test_format_default_cancelled_event(self):
        """Test formatting cancelled event with default reason."""
        result = format_cancelled_event()
        assert result == 'data: {"type": "cancelled", "reason": "user_cancelled"}\n\n'

    def test_format_custom_cancelled_event(self):
        """Test formatting cancelled event with custom reason."""
        result = format_cancelled_event("timeout")
        assert result == 'data: {"type": "cancelled", "reason": "timeout"}\n\n'

    def test_format_cancelled_with_detailed_reason(self):
        """Test formatting cancelled event with detailed reason."""
        reason = "stream_timeout_after_300_seconds"
        result = format_cancelled_event(reason)
        expected = f'data: {{"type": "cancelled", "reason": "{reason}"}}\n\n'
        assert result == expected


class TestSSEFormatIntegration:
    """Integration tests for SSE formatting."""

    def test_event_sequence(self):
        """Test a typical sequence of events."""
        events = []

        # Content chunks
        events.append(format_content_event("Hello"))
        events.append(format_content_event(" world"))
        events.append(format_content_event("!"))

        # Completion
        events.append(format_done_event())

        # Verify each event has correct format
        assert all(event.startswith("data: ") for event in events)
        assert all(event.endswith("\n\n") for event in events)

        # Parse and verify content
        parsed_events = []
        for event in events:
            json_str = event[6:-2]  # Remove "data: " prefix and "\n\n" suffix
            parsed_events.append(json.loads(json_str))

        assert parsed_events[0] == {"type": "content", "data": "Hello"}
        assert parsed_events[1] == {"type": "content", "data": " world"}
        assert parsed_events[2] == {"type": "content", "data": "!"}
        assert parsed_events[3] == {"type": "done"}

    def test_error_handling_sequence(self):
        """Test error handling event sequence."""
        events = []

        # Some content
        events.append(format_content_event("Partial response"))

        # Error occurs
        events.append(format_error_event("Connection lost"))

        # Parse events
        parsed_events = []
        for event in events:
            json_str = event[6:-2]
            parsed_events.append(json.loads(json_str))

        assert parsed_events[0] == {"type": "content", "data": "Partial response"}
        assert parsed_events[1] == {"type": "error", "error": "Connection lost"}
