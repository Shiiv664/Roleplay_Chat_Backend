# Claude Code AI Model Integration - Implementation Todo List

## Overview
This todo list tracks the implementation of Claude Code CLI integration as an AI model within the Roleplay Chat Backend system. The integration allows users to interact with Claude Code directly through the chat interface while maintaining character roleplay capabilities.

## Implementation Tasks

### Core Service Development
- [ ] **Create ClaudeCodeClient service class** in `app/services/claudecode/client.py` with `chat_completion_stream` method
- [ ] **Implement subprocess execution** for claude CLI command with proper error handling and timeout
- [ ] **Parse and yield streaming JSON response chunks** from claude CLI output

### Message Service Integration
- [ ] **Update MessageService.generate_streaming_response()** to route ClaudeCode requests to new method
- [ ] **Implement MessageService.generate_streaming_response_claude_code()** method using existing system prompt building

### AI Model Service Protection
- [ ] **Add deletion protection** for ClaudeCode model in `AIModelService.delete_model()`

### Database Initialization
- [ ] **Update scripts/db_init.py** to create ClaudeCode AI model with duplicate check

### Configuration
- [ ] **Add configuration variables** to `app/config.py` for Claude Code executable path and timeout

### Testing
- [ ] **Create unit tests** for ClaudeCodeClient in `tests/services/test_claudecode_client.py`
- [ ] **Add Claude Code integration tests** to `tests/services/test_message_service.py`
- [ ] **Test end-to-end conversation flow** with ClaudeCode model
- [ ] **Verify system prompt injection** and character roleplay functionality

### Quality Assurance
- [ ] **Run all existing tests** to ensure no regression from changes
- [ ] **Run code quality checks** (black, isort, flake8, mypy) and fix any issues
- [ ] **Validate API documentation consistency** after implementation

## Technical Specifications

### Command Format
```bash
claude --print --verbose --output-format "stream-json" --append-system-prompt "SYSTEM_PROMPT" <<< "CONVERSATION_TEXT"
```

### Response Parsing
Stream JSON format provides:
- `{"type":"system"}` - Setup and initialization
- `{"type":"assistant"}` - Actual response content  
- `{"type":"result"}` - Usage stats and session info

### Performance Targets
- Response time: ~8 seconds per request
- Cost: ~$0.008-0.009 per request
- Timeout: 120 seconds (configurable)

## Dependencies
- Claude Code CLI installed and accessible
- Valid Claude API credentials configured
- Existing system prompt building logic
- Current message service architecture

## Success Criteria
- ✅ ClaudeCode model appears in AI model list
- ✅ Character roleplay works with Claude Code
- ✅ Streaming responses work in real-time
- ✅ System prompts inject correctly
- ✅ Conversation context preserved
- ✅ Error handling functions properly
- ✅ All tests pass
- ✅ No regression in existing functionality

## Notes
- No database migrations required
- Uses existing AIModel schema
- Maintains consistency with OpenRouter integration
- Protected from deletion via business rules
- Input sanitization for security
- Mock subprocess execution for testing

---
*This file tracks the implementation progress for the Claude Code AI model integration feature.*