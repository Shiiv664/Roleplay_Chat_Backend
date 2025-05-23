# Chat Streaming Implementation Roadmap

## Overview
Implement real-time AI message generation using OpenRouter API with streaming capabilities for the roleplay chat system.

## Phase 1: Core Infrastructure Setup

### 1.1 OpenRouter API Module
- Create `app/services/openrouter/` directory structure
- Implement base OpenRouter client with authentication
- Create streaming response handler
- Add configuration management for API settings

### 1.2 Dependencies & Configuration
- Add required packages: `requests`, `asyncio` support, `cryptography`
- Create encryption service using `cryptography.fernet`
- Add OpenRouter API key to ApplicationSettings (encrypted storage)
- Add streaming-specific settings (timeouts, buffer sizes)
- Environment variable for encryption key: `ENCRYPTION_KEY`

### 1.3 Encryption Service Implementation
- Create `app/utils/encryption.py` with EncryptionService class
- Implement `encrypt_api_key()` and `decrypt_api_key()` methods
- Use Fernet symmetric encryption for API key protection
- Generate and document encryption key setup process

## Phase 2: Message Generation Service

### 2.1 OpenRouter API Key Management
- Update ApplicationSettingsService to handle encrypted API key storage
- Implement `set_openrouter_api_key()` with encryption
- Implement `get_openrouter_api_key()` with decryption
- Add API key validation and error handling

### 2.2 System Prompt Construction
- Implement prompt builder in message service
- Handle concatenation: `preSystemPrompt + separator + systemPrompt + separator + character.description + separator + userProfile.description`
- Use separator: `\n---\n`

### 2.3 Message History Processing
- Fetch complete chat session message history
- Format messages for OpenRouter API (role + content)
- Combine system prompt + history + postSystemPrompt + new user message

### 2.4 Streaming Message Generation
- Implement streaming OpenRouter API call
- Handle Server-Sent Events (SSE) parsing
- Process streaming chunks and accumulate response
- Save completed AI message to database

## Phase 3: API Endpoint Implementation

### 3.1 New Message Sending Endpoint
- Create `sendMessage` endpoint in messages namespace
- Route: `/api/chat-sessions/<int:chat_session_id>/send-message`
- Method: POST
- Request body: `{"content": string, "stream": boolean (optional, default: true)}`
- Input validation and session existence checks

### 3.2 Request Flow
1. Validate request parameters (content required, stream defaults to true)
2. Save user message to database with role "user"
3. Load chat session with all relationships (ai_model, system_prompt, character, user_profile)
4. Build system prompt using chat session configuration
5. Format message history with system prompt + history + postSystemPrompt + new user message
6. If streaming:
   - Return SSE response with text/event-stream content type
   - Stream AI response chunks to client as they arrive
7. If not streaming (future implementation):
   - Generate complete response
   - Return JSON with both messages
8. Save complete AI response with role "assistant"

### 3.3 Concurrency Control
- Implement session-level locking during streaming
- Prevent multiple concurrent messages per chat session
- Add endpoint status tracking

## Phase 4: Response Streaming

### 4.1 Server-Sent Events (SSE) Implementation
- SSE response directly from sendMessage endpoint when stream=true
- Implement `text/event-stream` response format
- Event types: content, done, error, cancelled

### 4.2 Stream State Management
- Track active streams per chat session in memory/Redis
- Store: `{chatSessionId: {isStreaming: true, partialMessage: "...", streamId: "uuid"}}`
- Accumulate message content as it streams from OpenRouter
- Handle stream lifecycle (start, progress, completion, cancellation)

### 4.3 Multiple Connection Support
- Allow multiple SSE connections per chat session
- Support concurrent tabs/devices for same user
- Broadcast streaming chunks to all active connections
- Connection management: register/unregister, heartbeat detection
- Resource limits: max connections per session, cleanup dead connections

### 4.4 Reconnection & Recovery
- On client reconnect: check for active streams
- Send accumulated content so far, then continue streaming
- Handle page refresh/browser close gracefully
- Timeout inactive streams (e.g., 5 minutes without active connections)

## Phase 5: Error Handling & Edge Cases

### 5.1 Error Scenarios
- OpenRouter API failures
- Network interruptions during streaming
- Invalid API responses
- Database save failures

### 5.2 Fallback Mechanisms
- Graceful degradation on streaming failures
- Proper error messages to client
- Database consistency on partial failures

## Phase 6: Testing & Validation

### 6.1 Unit Tests
- OpenRouter client module tests
- Message generation service tests
- Streaming response parsing tests

### 6.2 Integration Tests
- End-to-end streaming flow tests
- Error scenario testing
- Concurrent request handling tests

### 6.3 Performance Testing
- Streaming latency measurements
- Memory usage during long conversations
- Connection stability tests

## Phase 7: Documentation & Deployment

### 7.1 API Documentation
- Update OpenAPI specification
- Document streaming endpoint behavior
- Add example client implementations

### 7.2 Configuration Documentation
- OpenRouter API key setup
- Streaming configuration options
- Troubleshooting guide

## Implementation Notes

- **Modularity**: OpenRouter implementation should be easily replaceable with other providers (Anthropic, OpenAI)
- **Security**: API keys encrypted using Fernet, encryption key in environment variable
- **API Key Storage**: Stored in ApplicationSettings table (encrypted), managed via settings API
- **Model Selection**: AI model name from `chat_session.ai_model.label`
- **Scalability**: Consider connection limits and resource usage
- **UX**: Clear indicators for streaming state and progress

## Part 2: Stream Cancellation Implementation

### Phase 8: Stream Cancellation Infrastructure

### 8.1 Cancellation API Endpoint
- Create `cancelMessage` endpoint in messages namespace
- Route: `/api/chat-sessions/<int:chat_session_id>/cancel-message`
- Method: POST
- Validate active stream existence
- Return cancellation status

### 8.2 OpenRouter Stream Cancellation
- Implement stream abortion in OpenRouter client
- Use connection.close() or cancel_event.set() pattern from OpenRouter docs
- Handle graceful vs forced cancellation scenarios
- Ensure proper cleanup of OpenRouter connection resources

### 8.3 SSE Client Disconnection
- Broadcast cancellation event to all active SSE connections for the session
- Send final SSE event: `data: {"type": "cancelled", "reason": "user_cancelled"}`
- Close all SSE connections for the chat session
- Clean up connection registry and stream state

### 8.4 Partial Message Handling
- User sees partial response in real-time through SSE (no special database handling needed)
- Partial content remains visible in chat interface until cancellation completes

### 8.5 Stream State Cleanup
- Remove session from active streams registry
- Clear accumulated message content from memory/Redis
- Reset session streaming locks to allow new messages
- Update session status to allow new message sending

### 8.6 Error Handling for Cancellation
- Handle scenarios where OpenRouter stream already completed
- Manage race conditions between completion and cancellation
- Provide appropriate error messages for invalid cancellation attempts
- Handle network failures during cancellation process

### 8.7 Backend Cancellation Response
- Return appropriate HTTP status codes for cancellation requests
- Provide cancellation confirmation in API response
- Handle cancellation error cases and return meaningful messages

### Phase 9: Advanced Cancellation Features

### 9.1 Auto-Cancellation Scenarios
- Timeout-based cancellation (e.g., after 5 minutes of streaming)
- Connection loss cancellation (when all SSE clients disconnect)
- System maintenance cancellation with graceful notifications

### 9.2 Cancellation Analytics
- Track cancellation rates and reasons
- Monitor partial message lengths and user behavior
- Identify patterns for UX improvements

## Frontend Implementation Guide

### Client-Side Streaming Implementation

#### Sending Messages
- POST to `/api/chat-sessions/{id}/send-message` with `{content: string, stream: boolean}`
- Default `stream: true` for SSE response
- Handle response based on Content-Type header

#### SSE Event Format
```json
// Content event
{"type": "content", "data": "chunk of response text"}

// Completion event
{"type": "done"}

// Error event
{"type": "error", "error": "error description"}

// Cancellation event (Phase 8)
{"type": "cancelled", "reason": "user_cancelled"}
```

#### Implementation Approaches

##### Option 1: Manual Stream Reading (Recommended for control)
```javascript
const response = await fetch('/api/chat-sessions/123/send-message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: 'Hello!', stream: true })
});

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
            handleStreamEvent(event);
        }
    }
}
```

##### Option 2: EventSource API (Simpler but less flexible)
Note: Requires separate endpoint for SSE or workaround since EventSource only supports GET

#### Message Display
- Append chunks to message display as they arrive
- Show typing indicator during streaming
- Transition to static display on completion
- Handle markdown formatting in real-time

#### Streaming Controls
- Disable message input during active stream
- Show cancel button while streaming
- POST to `/api/chat-sessions/{id}/cancel-message` to cancel
- Clear indicators on completion or error

#### Error Handling
- Parse error events from SSE stream
- Display user-friendly error messages
- Handle network disconnections gracefully
- Retry logic for transient failures

#### State Management
- Track streaming state: idle, streaming, completed, error
- Store partial message content
- Update UI based on state transitions
- Handle multiple tabs (consider shared state)

### UX Considerations
- Smooth text appearance (avoid flickering)
- Auto-scroll to bottom as content arrives
- Preserve scroll position if user scrolls up
- Loading states for initial connection
- Mobile-optimized streaming experience

### Complete Frontend Example

```typescript
// TypeScript/React example
interface StreamEvent {
    type: 'content' | 'done' | 'error' | 'cancelled';
    data?: string;
    error?: string;
    reason?: string;
}

class ChatService {
    async sendMessage(chatSessionId: number, content: string, stream = true) {
        const response = await fetch(`/api/chat-sessions/${chatSessionId}/send-message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, stream })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to send message');
        }

        if (stream && response.headers.get('content-type')?.includes('text/event-stream')) {
            return this.handleStream(response);
        }

        return response.json();
    }

    private async *handleStream(response: Response): AsyncGenerator<StreamEvent> {
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');

            // Keep incomplete line in buffer
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.slice(6));
                        yield event;
                    } catch (e) {
                        console.error('Failed to parse SSE event:', e);
                    }
                }
            }
        }
    }

    async cancelMessage(chatSessionId: number) {
        const response = await fetch(`/api/chat-sessions/${chatSessionId}/cancel-message`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to cancel message');
        }

        return response.json();
    }
}

// Usage in React component
function ChatComponent({ chatSessionId }: { chatSessionId: number }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streamingMessage, setStreamingMessage] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    const sendMessage = async (content: string) => {
        // Add user message
        const userMessage = { role: 'user', content, timestamp: new Date() };
        setMessages(prev => [...prev, userMessage]);

        // Start streaming
        setIsStreaming(true);
        setStreamingMessage('');

        try {
            const chatService = new ChatService();
            const stream = await chatService.sendMessage(chatSessionId, content);

            for await (const event of stream) {
                switch (event.type) {
                    case 'content':
                        setStreamingMessage(prev => prev + event.data);
                        break;

                    case 'done':
                        // Add completed message to history
                        const aiMessage = {
                            role: 'assistant',
                            content: streamingMessage,
                            timestamp: new Date()
                        };
                        setMessages(prev => [...prev, aiMessage]);
                        setStreamingMessage('');
                        setIsStreaming(false);
                        break;

                    case 'error':
                        console.error('Stream error:', event.error);
                        setIsStreaming(false);
                        // Show error to user
                        break;
                }
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            setIsStreaming(false);
        }
    };

    return (
        <div>
            {/* Render messages and streaming content */}
            {isStreaming && <div className="streaming-message">{streamingMessage}</div>}
        </div>
    );
}
```

## Dependencies to Review
- Current message service structure
- Database transaction handling
- API authentication patterns
- Error handling framework
