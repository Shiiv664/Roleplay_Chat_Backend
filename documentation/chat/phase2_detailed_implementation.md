# Phase 2: Message Generation Service - Detailed Implementation Guide

## Overview
Phase 2 implements the core logic for generating AI responses using OpenRouter's streaming API. The key principle is that when a user sends a message via the `sendMessage` endpoint with `stream: true`, we use the chat session's configuration to determine all necessary components for the AI response.

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
        [character.description]
        ---
        [user_profile.description]
    """
```

### Prompt Components
1. **Pre-prompt** (if `pre_prompt_enabled` is True): `chat_session.pre_prompt`
2. **System prompt**: `chat_session.system_prompt.content`
3. **Character section**: Format as needed, e.g.:
   ```
   {chat_session.character.description if chat_session.character.description else "No description provided"}
   ```
4. **User profile section**: Format as needed, e.g.:
   ```
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
Character is Alice the Adventurer. A brave explorer who loves discovering ancient ruins and solving mysteries. She's witty, resourceful, and always ready for the next adventure.
---
User is John. A curious individual who enjoys fantasy stories and creative writing.
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

## 2.5 Endpoint Design

### Endpoint Definition
**Route**: `/api/chat-sessions/<int:chat_session_id>/send-message`
**Method**: `POST`
**Name**: `sendMessage`

### Request Body
```json
{
    "content": "string (required) - The message content from the user",
    "stream": "boolean (optional, default: true) - Whether to stream the response"
}
```

### Response Format (Streaming Mode)
When `stream: true`, the endpoint returns:
- Status: `200 OK`
- Headers: `Content-Type: text/event-stream`
- Body: Server-Sent Events stream

### Response Format (Non-Streaming Mode - Future)
When `stream: false`, the endpoint would return:
```json
{
    "success": true,
    "data": {
        "userMessage": { /* message object */ },
        "aiResponse": { /* message object */ }
    }
}
```

## 2.6 Main Endpoint Flow

When `sendMessage(chatSessionId, {content, stream})` is called:

1. **Validate request**:
   ```python
   content = request.json.get("content")
   stream = request.json.get("stream", True)  # Default to streaming

   if not content:
       raise ValidationError("Message content is required")
   ```

2. **Save user message**:
   ```python
   user_message = message_service.create_message(
       chat_session_id=chatSessionId,
       role="user",
       content=content
   )
   ```

3. **Get chat session with all relationships**:
   ```python
   chat_session = chat_session_service.get_by_id(
       chatSessionId,
       load_relationships=True  # Load ai_model, system_prompt, character, user_profile
   )
   ```

4. **Handle based on streaming mode**:
   ```python
   if stream:
       # Return SSE response
       return Response(
           stream_with_context(
               message_service.generate_streaming_response(
                   chat_session_id=chatSessionId,
                   user_message=content,
                   user_message_id=user_message.id
               )
           ),
           mimetype="text/event-stream"
       )
   else:
       # Non-streaming mode - not implemented yet
       raise NotImplementedError("Non-streaming mode not yet implemented")
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

## API Models Required

### Request Models
Create in `app/api/models/message.py`:
```python
# Request model for sending messages
send_message_model = Model(
    'SendMessage',
    {
        'content': fields.String(
            required=True,
            description='The message content to send',
            example='Hello, can you help me understand quantum physics?'
        ),
        'stream': fields.Boolean(
            required=False,
            default=True,
            description='Whether to stream the AI response. If true, returns SSE stream. If false, returns complete response (not implemented yet).',
            example=True
        )
    }
)

# Response model for streaming events
stream_event_model = Model(
    'StreamEvent',
    {
        'type': fields.String(
            required=True,
            description='Event type',
            enum=['content', 'error', 'done'],
            example='content'
        ),
        'data': fields.String(
            required=False,
            description='Event data (chunk of response text for content events)',
            example='Quantum physics is'
        ),
        'error': fields.String(
            required=False,
            description='Error message (only for error events)',
            example='OpenRouter API rate limit exceeded'
        )
    }
)

# Response model for non-streaming mode (future)
send_message_response_model = Model(
    'SendMessageResponse',
    {
        'user_message': fields.Nested(message_model, description='The created user message'),
        'ai_response': fields.Nested(message_model, description='The generated AI response')
    }
)

# Error response model
send_message_error_model = Model(
    'SendMessageError',
    {
        'success': fields.Boolean(default=False, description='Always false for errors'),
        'error': fields.String(description='Error type', example='VALIDATION_ERROR'),
        'message': fields.String(description='Human-readable error message', example='Message content is required'),
        'details': fields.Raw(description='Additional error details', required=False)
    }
)
```

## Endpoint Implementation

### SendMessage Endpoint
Create in `app/api/namespaces/messages.py`:

```python
@api.route("/chat-sessions/<int:chat_session_id>/send-message")
@api.param("chat_session_id", "The chat session identifier")
class SendMessageResource(Resource):
    """Send a message to the chat session and get AI response."""

    @api.doc("send_message",
        description="Send a user message and receive an AI-generated response. "
                    "Supports both streaming (SSE) and non-streaming modes.")
    @api.expect(send_message_model)
    @api.response(200, "Success (streaming mode returns SSE stream)")
    @api.response(201, "Success (non-streaming mode)", send_message_response_model)
    @api.response(400, "Validation error", send_message_error_model)
    @api.response(404, "Chat session not found", send_message_error_model)
    @api.response(500, "Internal server error", send_message_error_model)
    @api.response(503, "OpenRouter service unavailable", send_message_error_model)
    @api.produces(['text/event-stream', 'application/json'])
    def post(self, chat_session_id: int):
        """Send a message and get AI response.

        When stream=true (default):
        - Returns Server-Sent Events stream
        - Content-Type: text/event-stream
        - Events format:
          - data: {"type": "content", "data": "chunk of text"}
          - data: {"type": "done"}
          - data: {"type": "error", "error": "error message"}

        When stream=false:
        - Returns JSON with both messages
        - Content-Type: application/json

        Note: Non-streaming mode is not implemented yet.
        """
        # Implementation here
```

### CancelMessage Endpoint (Phase 8)
Create in `app/api/namespaces/messages.py`:

```python
@api.route("/chat-sessions/<int:chat_session_id>/cancel-message")
@api.param("chat_session_id", "The chat session identifier")
class CancelMessageResource(Resource):
    """Cancel an ongoing message stream."""

    @api.doc("cancel_message",
        description="Cancel an active AI message generation stream. "
                    "Only works if there's an active stream for the session.")
    @api.response(200, "Cancellation successful", response_model)
    @api.response(400, "No active stream to cancel", send_message_error_model)
    @api.response(404, "Chat session not found", send_message_error_model)
    def post(self, chat_session_id: int):
        """Cancel active message stream.

        Returns:
        - 200: Stream cancelled successfully
        - 400: No active stream for this session
        - 404: Chat session doesn't exist
        """
        # Implementation here
```

### Stream Event Format Documentation
```
## Server-Sent Events Format

Each event is sent as:
data: <JSON object>\n\n

Event types:
1. Content chunk: {"type": "content", "data": "partial response text"}
2. Completion: {"type": "done"}
3. Error: {"type": "error", "error": "error description"}
4. Cancelled: {"type": "cancelled", "reason": "user_cancelled"}

Example stream:
data: {"type": "content", "data": "Quantum physics is a"}\n\n
data: {"type": "content", "data": " fundamental theory in"}\n\n
data: {"type": "content", "data": " physics that describes"}\n\n
data: {"type": "done"}\n\n

Example cancelled stream:
data: {"type": "content", "data": "Quantum physics is a"}\n\n
data: {"type": "cancelled", "reason": "user_cancelled"}\n\n
```

## Frontend Integration Examples

### Using the SendMessage Endpoint

#### JavaScript/TypeScript Example (Streaming)
```typescript
// Streaming mode (default)
const response = await fetch('/api/chat-sessions/123/send-message', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        content: 'Hello, how are you?',
        stream: true  // optional, defaults to true
    })
});

// Handle SSE stream
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6));

            switch (event.type) {
                case 'content':
                    // Append to message display
                    appendToMessage(event.data);
                    break;
                case 'done':
                    // Message complete
                    onMessageComplete();
                    break;
                case 'error':
                    // Handle error
                    onError(event.error);
                    break;
            }
        }
    }
}
```

#### Using EventSource API (Recommended for SSE)
```typescript
const eventSource = new EventSource('/api/chat-sessions/123/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'content':
            appendToMessage(data.data);
            break;
        case 'done':
            eventSource.close();
            onMessageComplete();
            break;
        case 'error':
            eventSource.close();
            onError(data.error);
            break;
    }
};

eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
};

// Send message to trigger streaming
await fetch('/api/chat-sessions/123/send-message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: 'Hello!' })
});
```

### Cancelling a Stream
```typescript
// Cancel ongoing stream
const cancelResponse = await fetch('/api/chat-sessions/123/cancel-message', {
    method: 'POST'
});

if (cancelResponse.ok) {
    console.log('Stream cancelled successfully');
}
```

## Implementation Checklist

- [ ] Create all API models (send_message_model, stream_event_model, etc.)
- [ ] Implement `build_system_prompt()` in MessageService
- [ ] Implement `format_messages_for_openrouter()` in MessageService
- [ ] Implement `generate_streaming_response()` in MessageService
- [ ] Add method to save AI messages after streaming
- [ ] Add method to get chat session with all relationships loaded
- [ ] Create `sendMessage` endpoint with full OpenAPI documentation
- [ ] Create `cancelMessage` endpoint with full OpenAPI documentation
- [ ] Add SSE formatter utility function
- [ ] Create comprehensive unit tests
- [ ] Create integration tests
- [ ] Update OpenAPI JSON export
- [ ] Add CORS headers for SSE support
