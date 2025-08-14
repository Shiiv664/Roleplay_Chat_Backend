"""Claude Code CLI client for LLM interactions."""

import json
import logging
import subprocess
import time
from typing import Iterator, Dict, Any, Optional

from app.config import get_config
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ClaudeCodeClient:
    """Client for interacting with Claude Code CLI."""

    def __init__(self, timeout: Optional[int] = None) -> None:
        """Initialize the Claude Code client.

        Args:
            timeout: Command timeout in seconds (uses config default if None)
        """
        config = get_config()
        self.executable_path = config.CLAUDE_CODE_EXECUTABLE_PATH
        self.timeout = timeout or config.CLAUDE_CODE_TIMEOUT

    def chat_completion_stream(
        self, system_prompt: str, conversation_text: str
    ) -> Iterator[Dict[str, Any]]:
        """Stream a chat completion response from Claude Code CLI.

        Args:
            system_prompt: System prompt to append to the conversation
            conversation_text: Full conversation history and current message

        Yields:
            Parsed streaming JSON response chunks

        Raises:
            ValidationError: If parameters are invalid
            Exception: If CLI execution fails
        """
        if not system_prompt or not system_prompt.strip():
            raise ValidationError("System prompt is required")

        if not conversation_text or not conversation_text.strip():
            raise ValidationError("Conversation text is required")

        # Build the claude command
        command = [
            self.executable_path,
            "--print",
            "--verbose",
            "--output-format", "stream-json",
            "--append-system-prompt", system_prompt.strip()
        ]

        logger.info(f"Executing Claude Code CLI with system prompt length: {len(system_prompt)}")
        logger.debug(f"Command: {' '.join(command[:-1])} '[SYSTEM_PROMPT]'")

        try:
            # Start subprocess with conversation text as stdin
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send conversation text to stdin and close it
            try:
                process.stdin.write(conversation_text.strip().encode('utf-8'))
                process.stdin.close()
            except BrokenPipeError:
                # If the process has already terminated, stdin might be closed
                logger.warning("Stdin write failed - process may have terminated early")

            # Stream output line by line
            start_time = time.time()
            for line in iter(process.stdout.readline, b''):
                # Check timeout
                if time.time() - start_time > self.timeout:
                    process.terminate()
                    process.wait(timeout=5)  # Give it 5 seconds to terminate gracefully
                    if process.poll() is None:
                        process.kill()  # Force kill if it doesn't terminate
                    raise Exception(f"Claude Code CLI timed out after {self.timeout} seconds")

                # Decode bytes to string and strip whitespace
                line = line.decode('utf-8').strip()
                if not line:
                    continue

                try:
                    # Parse JSON response chunk
                    chunk_data = json.loads(line)
                    logger.debug(f"Received chunk type: {chunk_data.get('type', 'unknown')}")
                    yield chunk_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON chunk: {line[:100]}...")
                    logger.warning(f"JSON parse error: {e}")
                    # Skip invalid JSON chunks
                    continue

            # Wait for process to complete and check return code
            return_code = process.wait()
            if return_code != 0:
                # Read stderr for error details
                stderr_output = process.stderr.read().decode('utf-8')
                error_msg = f"Claude Code CLI failed with return code {return_code}"
                if stderr_output:
                    error_msg += f": {stderr_output}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except subprocess.TimeoutExpired:
            logger.error(f"Claude Code CLI timed out after {self.timeout} seconds")
            raise Exception(f"Claude Code CLI timed out after {self.timeout} seconds")
        except FileNotFoundError:
            logger.error(f"Claude Code CLI executable not found: {self.executable_path}")
            raise Exception(f"Claude Code CLI executable not found: {self.executable_path}")
        except Exception as e:
            logger.error(f"Error executing Claude Code CLI: {e}")
            raise Exception(f"Claude Code CLI execution failed: {e}")

    def test_connection(self) -> bool:
        """Test the Claude Code CLI connection.

        Returns:
            True if CLI is accessible and functional, False otherwise
        """
        try:
            # Test with a simple conversation
            system_prompt = "You are a helpful assistant."
            conversation_text = "Hello, this is a connection test."
            
            # Try to get at least one response chunk
            for chunk in self.chat_completion_stream(system_prompt, conversation_text):
                if chunk.get('type') == 'assistant':
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Claude Code CLI connection test failed: {e}")
            return False