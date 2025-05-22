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
- Handle concatenation: `preSystemPrompt + separator + systemPrompt + separator + character_description + separator + userProfile_description`
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

### 3.1 New Streaming Endpoint
- Create `addUserMessageStreamingMode` endpoint in messages namespace
- Parameters: `chatSessionId`, `message`
- Input validation and session existence checks

### 3.2 Request Flow
1. Save user message to database with role "user"
2. Build system prompt (preSystemPrompt + systemPrompt + character_description + userProfile_description)
3. Fetch message history and add postSystemPrompt before new user message
4. Initiate streaming OpenRouter API call
5. Stream response to client
6. Save complete AI response with role "assistant"

### 3.3 Concurrency Control
- Implement session-level locking during streaming
- Prevent multiple concurrent messages per chat session
- Add endpoint status tracking

## Phase 4: Response Streaming

### 4.1 Server-Sent Events (SSE) Implementation
- Create SSE endpoint: `/api/chat/{session_id}/stream`
- Implement `text/event-stream` response format
- Use EventSource API on client side

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
- **Scalability**: Consider connection limits and resource usage
- **UX**: Clear indicators for streaming state and progress
- **Cancellation**: Future endpoint for stopping mid-stream (Phase 8)

## Dependencies to Review
- Current message service structure
- Database transaction handling
- API authentication patterns
- Error handling framework
