# Phase 2: Message Generation Service - Detailed Implementation Guide

## Overview
Phase 2 implements the core logic for generating AI responses using OpenRouter's streaming API. The key principle is that when a user sends a message via the `addUserMessageStreamingMode` endpoint, we use the chat session's configuration to determine all necessary components for the AI response.

## Key Components from Chat Session

When processing a message for `chatSessionId`, we extract:
1. **AI Model**: `chatSession.ai_model.label` → Used as model name for OpenRouter API
2. **System Prompt**: `chatSession.system_prompt.content`
3. **Pre/Post Prompts**: `chatSession.pre_prompt` and `chatSession.post_prompt` (if enabled)
4. **User Profile**: `chatSession.user_profile` → For user description
5. **Character**: `chatSession.character` → For character description

## 2.1 OpenRouter API Key Management (✅ Already Implemented)
- `ApplicationSettingsService.set_openrouter_api_key(api_key: str)`
- `ApplicationSettingsService.get_openrouter_api_key() -> str`
- `ApplicationSettingsService.clear_openrouter_api_key()`

## 2.2 System Prompt Construction

### Required Implementation
Create method in `MessageService`:

```python
def build_system_prompt(self, chat_session: ChatSession) -> str:
    """
    Constructs the complete system prompt for the AI model.

    Args:
        chat_session: The chat session containing all configuration

    Returns:
        Complete system prompt string

    Format:
        [pre_prompt if enabled]
        ---
        [system_prompt.content]
        ---
        [character.name and character.description]
        ---
        [user_profile.name and user_profile.description]
    """
```

### Prompt Components
1. **Pre-prompt** (if `pre_prompt_enabled` is True): `chat_session.pre_prompt`
2. **System prompt**: `chat_session.system_prompt.content`
3. **Character section**: Format as needed, e.g.:
   ```
   Character: {chat_session.character.name}
   {chat_session.character.description if chat_session.character.description else "No description provided"}
   ```
4. **User profile section**: Format as needed, e.g.:
   ```
   User: {chat_session.user_profile.name}
   {chat_session.user_profile.description if chat_session.user_profile.description else "No description provided"}
   ```

**Note**: Both `character.description` and `user_profile.description` are nullable fields, so handle None values appropriately.

### Separator
Use `\n---\n` between major sections

### Example Complete System Prompt
```
[If pre_prompt_enabled] Remember to stay in character at all times.
---
You are an AI assistant playing a role in a collaborative storytelling experience.
---
Character: Alice the Adventurer
A brave explorer who loves discovering ancient ruins and solving mysteries. She's witty, resourceful, and always ready for the next adventure.
---
User: John
A curious individual who enjoys fantasy stories and creative writing.
```

## 2.3 Message History Processing

### Required Implementation
Create method in `MessageService`:

```python
def format_messages_for_openrouter(
    self,
    chat_session_id: int,
    new_user_message: str
) -> List[Dict[str, str]]:
    """
    Formats all messages for OpenRouter API including history and new message.

    Args:
        chat_session_id: ID of the chat session
        new_user_message: The new message from the user

    Returns:
        List of message dictionaries with 'role' and 'content' keys

    Message Order:
        1. System message (from build_system_prompt)
        2. All historical messages (user/assistant pairs)
        3. Post-prompt (if enabled) as system message
        4. New user message
    """
```

### Message Formatting
- System messages: `{"role": "system", "content": "..."}`
- User messages: `{"role": "user", "content": "..."}`
- Assistant messages: `{"role": "assistant", "content": "..."}`

### Post-Prompt Handling
If `post_prompt_enabled` is True, add `chat_session.post_prompt` as a system message before the new user message.

## 2.4 Streaming Message Generation

### Required Implementation
Create method in `MessageService`:

```python
async def generate_streaming_response(
    self,
    chat_session_id: int,
    user_message: str,
    user_message_id: int
) -> AsyncGenerator[str, None]:
    """
    Generates AI response using OpenRouter streaming API.

    Args:
        chat_session_id: ID of the chat session
        user_message: The user's message content
        user_message_id: ID of the saved user message

    Yields:
        Chunks of the AI response as they arrive

    Side Effects:
        - Saves completed AI message to database
        - Updates stream state management

    Process:
        1. Get chat session with all relationships
        2. Build system prompt using chat session config
        3. Format message history + new message
        4. Get model name from chat_session.ai_model.label
        5. Call OpenRouter streaming API
        6. Yield chunks as they arrive
        7. Save complete response to database
    """
```

### Integration Points
1. Use `OpenRouterClient.create_streaming_completion()` with:
   - `model`: from `chat_session.ai_model.label`
   - `messages`: from `format_messages_for_openrouter()`
   - `stream`: True

2. Save AI response after completion:
```python
# After streaming completes
ai_message = Message(
    chat_session_id=chat_session_id,
    role="assistant",
    content=accumulated_response,
    timestamp=datetime.utcnow()
)
self.message_repository.create(ai_message)
```

## 2.5 Main Endpoint Flow

When `addUserMessageStreamingMode(chatSessionId, message)` is called:

1. **Save user message**:
   ```python
   user_message = message_service.create_message(
       chat_session_id=chatSessionId,
       role="user",
       content=message
   )
   ```

2. **Get chat session with all relationships**:
   ```python
   chat_session = chat_session_service.get_by_id(
       chatSessionId,
       load_relationships=True  # Load ai_model, system_prompt, character, user_profile
   )
   ```

3. **Generate streaming response**:
   ```python
   async for chunk in message_service.generate_streaming_response(
       chat_session_id=chatSessionId,
       user_message=message,
       user_message_id=user_message.id
   ):
       yield chunk  # Stream to client via SSE
   ```

## Error Handling

### Required Error Cases
1. **Missing OpenRouter API key**: Check before making API call
2. **Invalid chat session**: Validate session exists and has all required relationships
3. **Missing AI model configuration**: Ensure `chat_session.ai_model.label` exists
4. **OpenRouter API errors**: Handle rate limits, invalid responses, network errors
5. **Database save failures**: Handle message save errors gracefully

### Error Response Format
```python
{
    "error": "error_type",
    "message": "Human-readable error message",
    "details": {...}  # Optional additional context
}
```

## Testing Requirements

### Unit Tests
1. Test `build_system_prompt()` with various configurations
2. Test `format_messages_for_openrouter()` with different message histories
3. Mock OpenRouter API calls for streaming tests

### Integration Tests
1. Test full flow from endpoint to saved AI message
2. Test error scenarios (missing API key, invalid session, etc.)
3. Test with different prompt configurations (pre/post prompts enabled/disabled)

## Implementation Checklist

- [ ] Implement `build_system_prompt()` in MessageService
- [ ] Implement `format_messages_for_openrouter()` in MessageService
- [ ] Implement `generate_streaming_response()` in MessageService
- [ ] Add method to save AI messages after streaming
- [ ] Add method to get chat session with all relationships loaded
- [ ] Create comprehensive unit tests
- [ ] Create integration tests
- [ ] Update API documentation
