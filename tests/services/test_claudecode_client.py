"""Tests for ClaudeCodeClient."""

import json
import subprocess
from unittest.mock import Mock, patch, MagicMock

import pytest

from app.services.claudecode.client import ClaudeCodeClient
from app.utils.exceptions import ValidationError


class TestClaudeCodeClient:
    """Test cases for ClaudeCodeClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = ClaudeCodeClient(timeout=30)

    def test_init_default_timeout(self):
        """Test client initialization with default timeout."""
        with patch("app.services.claudecode.client.get_config") as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.CLAUDE_CODE_EXECUTABLE_PATH = "claude"
            mock_config_obj.CLAUDE_CODE_TIMEOUT = 120
            mock_config.return_value = mock_config_obj
            
            client = ClaudeCodeClient()
            
            assert client.executable_path == "claude"
            assert client.timeout == 120

    def test_init_custom_timeout(self):
        """Test client initialization with custom timeout."""
        with patch("app.services.claudecode.client.get_config") as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.CLAUDE_CODE_EXECUTABLE_PATH = "claude"
            mock_config_obj.CLAUDE_CODE_TIMEOUT = 120
            mock_config.return_value = mock_config_obj
            
            client = ClaudeCodeClient(timeout=60)
            
            assert client.timeout == 60

    def test_chat_completion_stream_empty_system_prompt(self):
        """Test chat completion stream with empty system prompt."""
        with pytest.raises(ValidationError, match="System prompt is required"):
            list(self.client.chat_completion_stream("", "conversation"))

    def test_chat_completion_stream_empty_conversation(self):
        """Test chat completion stream with empty conversation."""
        with pytest.raises(ValidationError, match="Conversation text is required"):
            list(self.client.chat_completion_stream("system prompt", ""))

    @patch("app.services.claudecode.client.subprocess.Popen")
    def test_chat_completion_stream_success(self, mock_popen):
        """Test successful chat completion stream."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.wait.return_value = 0
        mock_process.poll.return_value = 0
        
        # Mock stdout responses
        responses = [
            '{"type":"system","message":"Starting Claude Code"}',
            '{"type":"assistant","message":{"content":[{"text":"Hello, "}]}}',
            '{"type":"assistant","message":{"content":[{"text":"how can I help you?"}]}}',
            '{"type":"result","usage":{"input_tokens":10,"output_tokens":5}}',
            ''  # End of stream
        ]
        mock_process.stdout.readline.side_effect = responses
        
        mock_popen.return_value = mock_process
        
        # Execute
        result = list(self.client.chat_completion_stream(
            "You are helpful", 
            "User: Hello\n"
        ))
        
        # Verify
        expected_chunks = [
            {"type": "system", "message": "Starting Claude Code"},
            {"type": "assistant", "message": {"content": [{"text": "Hello, "}]}},
            {"type": "assistant", "message": {"content": [{"text": "how can I help you?"}]}},
            {"type": "result", "usage": {"input_tokens": 10, "output_tokens": 5}}
        ]
        
        assert result == expected_chunks
        
        # Verify subprocess call
        mock_popen.assert_called_once_with(
            [
                "claude",
                "--print",
                "--verbose", 
                "--output-format", "stream-json",
                "--append-system-prompt", "You are helpful"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Verify stdin input
        mock_process.stdin.write.assert_called_once_with("User: Hello")
        mock_process.stdin.close.assert_called_once()

    @patch("app.services.claudecode.client.subprocess.Popen")
    def test_chat_completion_stream_invalid_json(self, mock_popen):
        """Test chat completion stream with invalid JSON response."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.wait.return_value = 0
        mock_process.poll.return_value = 0
        
        # Mock stdout with invalid JSON
        responses = [
            '{"type":"system","message":"Starting"}',
            'invalid json line',
            '{"type":"assistant","message":{"content":[{"text":"response"}]}}',
            ''  # End of stream
        ]
        mock_process.stdout.readline.side_effect = responses
        
        mock_popen.return_value = mock_process
        
        # Execute - should skip invalid JSON
        result = list(self.client.chat_completion_stream(
            "You are helpful", 
            "User: Hello\n"
        ))
        
        # Verify only valid JSON chunks are returned
        expected_chunks = [
            {"type": "system", "message": "Starting"},
            {"type": "assistant", "message": {"content": [{"text": "response"}]}}
        ]
        
        assert result == expected_chunks

    @patch("app.services.claudecode.client.subprocess.Popen")
    def test_chat_completion_stream_process_error(self, mock_popen):
        """Test chat completion stream with process error."""
        # Mock subprocess with error return code
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.wait.return_value = 1
        mock_process.stderr.read.return_value = "Command failed"
        
        # Mock empty stdout
        mock_process.stdout.readline.side_effect = ['']
        
        mock_popen.return_value = mock_process
        
        # Execute and expect exception
        with pytest.raises(Exception, match="Claude Code CLI failed with return code 1: Command failed"):
            list(self.client.chat_completion_stream(
                "You are helpful", 
                "User: Hello\n"
            ))

    @patch("app.services.claudecode.client.subprocess.Popen")
    def test_chat_completion_stream_file_not_found(self, mock_popen):
        """Test chat completion stream with executable not found."""
        mock_popen.side_effect = FileNotFoundError("File not found")
        
        # Execute and expect exception
        with pytest.raises(Exception, match="Claude Code CLI executable not found: claude"):
            list(self.client.chat_completion_stream(
                "You are helpful", 
                "User: Hello\n"
            ))

    @patch("app.services.claudecode.client.subprocess.Popen")
    @patch("app.services.claudecode.client.time.time")
    def test_chat_completion_stream_timeout(self, mock_time, mock_popen):
        """Test chat completion stream with timeout."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.kill = Mock()
        
        # Mock time to simulate timeout
        mock_time.side_effect = [0, 31]  # Start time, then time after timeout
        
        # Mock stdout that never ends
        def readline_side_effect():
            return '{"type":"system","message":"Starting"}'
        
        mock_process.stdout.readline.side_effect = readline_side_effect
        
        mock_popen.return_value = mock_process
        
        # Execute with 30 second timeout and expect exception
        client = ClaudeCodeClient(timeout=30)
        with pytest.raises(Exception, match="Claude Code CLI timed out after 30 seconds"):
            list(client.chat_completion_stream(
                "You are helpful", 
                "User: Hello\n"
            ))
        
        # Verify timeout handling
        mock_process.terminate.assert_called_once()

    @patch("app.services.claudecode.client.subprocess.Popen")
    def test_chat_completion_stream_broken_pipe(self, mock_popen):
        """Test chat completion stream with broken pipe on stdin."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.wait.return_value = 0
        mock_process.poll.return_value = 0
        
        # Mock broken pipe on stdin write
        mock_process.stdin.write.side_effect = BrokenPipeError("Broken pipe")
        
        # Mock stdout response
        responses = [
            '{"type":"assistant","message":{"content":[{"text":"response"}]}}',
            ''  # End of stream
        ]
        mock_process.stdout.readline.side_effect = responses
        
        mock_popen.return_value = mock_process
        
        # Execute - should handle broken pipe gracefully
        result = list(self.client.chat_completion_stream(
            "You are helpful", 
            "User: Hello\n"
        ))
        
        # Should still get response despite broken pipe
        expected_chunks = [
            {"type": "assistant", "message": {"content": [{"text": "response"}]}}
        ]
        
        assert result == expected_chunks

    @patch.object(ClaudeCodeClient, "chat_completion_stream")
    def test_test_connection_success(self, mock_stream):
        """Test successful connection test."""
        # Mock successful stream response
        mock_stream.return_value = [
            {"type": "system", "message": "Starting"},
            {"type": "assistant", "message": {"content": [{"text": "Hello"}]}}
        ]
        
        result = self.client.test_connection()
        
        assert result is True
        mock_stream.assert_called_once_with(
            "You are a helpful assistant.",
            "Hello, this is a connection test."
        )

    @patch.object(ClaudeCodeClient, "chat_completion_stream")
    def test_test_connection_no_assistant_response(self, mock_stream):
        """Test connection test with no assistant response."""
        # Mock stream response without assistant message
        mock_stream.return_value = [
            {"type": "system", "message": "Starting"}
        ]
        
        result = self.client.test_connection()
        
        assert result is False

    @patch.object(ClaudeCodeClient, "chat_completion_stream")
    def test_test_connection_exception(self, mock_stream):
        """Test connection test with exception."""
        # Mock stream that raises exception
        mock_stream.side_effect = Exception("Connection failed")
        
        result = self.client.test_connection()
        
        assert result is False