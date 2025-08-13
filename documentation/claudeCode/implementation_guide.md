# Claude Code AI Model Integration Guide

## Overview
This document describes the integration of Claude Code CLI as an AI model type within the Roleplay Chat Backend system. The integration allows users to interact with Claude Code directly through the chat interface while maintaining the same conversation flow and character roleplay capabilities.

## Technical Implementation

### AI Model Type: ClaudeCode
- **Label**: `ClaudeCode`
- **Description**: Local Claude Code CLI integration with dynamic system prompts
- **Type**: Hard-coded, non-deletable system model
- **Integration Method**: Command-line subprocess execution

### Command Structure
```bash
claude --print --verbose --output-format "stream-json" --append-system-prompt "SYSTEM_PROMPT" <<< "CONVERSATION_TEXT"
```

**Parameters**:
- `--print`: Print responses without interactive mode
- `--verbose`: Enable detailed output including system messages
- `--output-format "stream-json"`: Stream responses in JSON format
- `--append-system-prompt`: Inject dynamic system prompt
- stdin: Conversation history and current message

### Response Format
Claude Code streams responses in JSON format with three message types:

1. **System Messages**: `{"type":"system"}` - Setup and initialization
2. **Assistant Messages**: `{"type":"assistant"}` - Actual response content
3. **Result Messages**: `{"type":"result"}` - Usage stats and session info

Response content is extracted from:
```json
{
  "type": "assistant",
  "message": {
    "content": [{"text": "response text here"}]
  }
}
```

### Performance Characteristics
- **Response Time**: ~8 seconds per request
- **Cost**: ~$0.008-0.009 per request
- **Timeout**: 120 seconds (configurable)

## Architecture Integration

### Service Layer Changes
**ClaudeCodeClient** (`app/services/claudecode/client.py`):
- Manages subprocess execution
- Handles streaming JSON parsing
- Error handling for command failures and timeouts

**MessageService** (`app/services/message_service.py`):
- Route detection based on `ai_model.label == "ClaudeCode"`
- Reuses existing system prompt building logic
- Formats conversation for stdin input

### Database Integration
- Uses existing `AIModel` schema
- No migrations required
- ClaudeCode model created during database initialization
- Protected from deletion via business rules

### Configuration
Environment variables in `app/config.py`:
- `CLAUDE_CODE_EXECUTABLE_PATH`: Path to claude executable (default: "claude")
- `CLAUDE_CODE_TIMEOUT`: Command timeout in seconds (default: 120)

## Features

### Dynamic System Prompts
- Leverages existing system prompt building logic
- Combines character definitions, system prompts, and context
- Maintains consistency with OpenRouter integration

### Conversation Context
- Preserves full conversation history
- Maintains character roleplay continuity
- Supports multi-turn conversations

### Error Handling
- Command execution failures
- Subprocess timeouts
- Missing executable detection
- Graceful fallback messaging

### Security Considerations
- Input sanitization for system prompts and conversation text
- Subprocess execution with timeout limits
- No shell injection vulnerabilities

## Testing Strategy

### Unit Tests
- `tests/services/test_claudecode_client.py`: Client functionality
- `tests/services/test_message_service.py`: Integration tests
- Mock subprocess execution for reliable testing

### Integration Tests
- End-to-end conversation flow
- System prompt injection verification
- Error condition handling

## Future Enhancements

### Model Selection
- Use `--model <model>` parameter for Claude model variants
- Allow users to specify preferred Claude model

### Fallback Support
- Use `--fallback-model <model>` for automatic failover
- Handle model availability issues gracefully

### Performance Optimization
- Connection pooling for reduced startup time
- Caching for frequently used system prompts

## Deployment Notes

### Prerequisites
- Claude Code CLI installed and accessible in PATH
- Valid Claude API credentials configured
- Sufficient system resources for subprocess execution

### Configuration
1. Set `CLAUDE_CODE_EXECUTABLE_PATH` if claude is not in PATH
2. Adjust `CLAUDE_CODE_TIMEOUT` based on expected response times
3. Verify claude CLI functionality before deployment

### Monitoring
- Track subprocess execution success/failure rates
- Monitor response times and timeout occurrences
- Log conversation quality and error patterns

This integration provides a seamless way to leverage Claude Code's capabilities within the existing roleplay chat architecture while maintaining all existing features and user experience patterns.