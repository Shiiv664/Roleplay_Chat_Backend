# Claude Code Integration Plan

## Overview
Add a hard-coded "ClaudeCode" AI model that integrates with the local Claude Code CLI, passing the dynamically built system prompt via the `-p` parameter and conversation via stdin.

## Implementation Plan

### 1. Create Claude Code Service
**New file**: `app/services/claudecode/client.py`
- **ClaudeCodeClient class** with methods:
  - `chat_completion_stream(system_prompt, conversation_text)` 
  - Execute: `claude --print --verbose --output-format "stream-json" --append-system-prompt "{system_prompt}" <<< "{conversation_text}"`
  - Stream subprocess stdout line by line
  - Handle command execution errors and timeouts
  - Parse and yield response chunks similar to OpenRouter format

### 2. Update Message Service
**Modify**: `app/services/message_service.py`
- **Update `generate_streaming_response()`** with label check:
  ```python
  if chat_session.ai_model.label == "ClaudeCode":
      return self.generate_streaming_response_claude_code(...)
  else:
      return self.generate_streaming_response_openrouter(...)
  ```
- **New method**: `generate_streaming_response_claude_code()`
  - Use existing `build_system_prompt()` for dynamic system prompt
  - Format conversation history + new message as text for stdin
  - Call ClaudeCodeClient with system prompt and conversation
  - Stream response chunks back to API

### 3. Update AI Model Service
**Modify**: `app/services/ai_model_service.py`
- **Add deletion protection** in `delete_model()`:
  ```python
  if model.label == "ClaudeCode":
      raise BusinessRuleError("Cannot delete the ClaudeCode model")
  ```

### 4. Default Model Creation
**Modify**: `scripts/db_init.py`
- **Add ClaudeCode model creation**:
  ```python
  claude_model = AIModel(
      label="ClaudeCode",
      description="Local Claude Code CLI integration with dynamic system prompts"
  )
  ```
- **Check if already exists** before creating to avoid duplicates

### 5. Configuration
**Add to**: `app/config.py`
- `CLAUDE_CODE_EXECUTABLE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")`
- `CLAUDE_CODE_TIMEOUT = int(os.getenv("CLAUDE_CODE_TIMEOUT", "120"))`

### 6. Testing
**New test files**:
- `tests/services/test_claudecode_client.py`
- Add Claude Code tests to existing `test_message_service.py`

## Key Technical Details

**Command Format**: `claude --print --verbose --output-format "stream-json" --append-system-prompt "SYSTEM_PROMPT" <<< "CONVERSATION_TEXT"`

**System Prompt**: Same dynamic prompt used for OpenRouter (character + system prompts + context)

**Conversation Format**: Format history + new message as plain text for stdin

**No Database Changes**: Uses existing AIModel schema, just adds one special record

**Stream JSON Output**: Uses `--verbose --output-format "stream-json"` to receive real-time streaming responses in JSON format for forwarding to frontend
- Stream provides 3 message types: `{"type":"system"}`, `{"type":"assistant"}`, `{"type":"result"}`
- Assistant message contains actual response text in `message.content[0].text`
- Result message provides usage stats, cost tracking, and session info

**Testing Results**: ✅ All functionality confirmed working
- Character roleplay with system prompts: Perfect
- Conversation context preservation: Working  
- Response time: ~8 seconds per request
- Cost tracking: ~$0.008-0.009 per request

**Error Handling**: Command execution failures, subprocess timeouts, missing executable

**Optional Enhancements**: 
- Use `--model <model>` parameter to allow users to specify which Claude model variant to use
- Use `--fallback-model <model>` for automatic fallback when primary model is overloaded

This approach is simple, requires no migrations, and integrates cleanly with the existing architecture.