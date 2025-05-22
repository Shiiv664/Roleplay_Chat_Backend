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
- Add required packages: `requests`, `asyncio` support
- Update configuration for OpenRouter API key handling
- Add streaming-specific settings (timeouts, buffer sizes)

## Phase 2: Message Generation Service

### 2.1 System Prompt Construction
- Implement prompt builder in message service
- Handle concatenation: `preSystemPrompt + separator + systemPrompt + separator + character_description + separator + userProfile_description + separator + postSystemPrompt`
- Use separator: `\n---\n`

### 2.2 Message History Processing
- Fetch complete chat session message history
- Format messages for OpenRouter API (role + content)
- Combine system prompt + history + new user message

### 2.3 Streaming Message Generation
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
2. Build complete prompt context
3. Initiate streaming OpenRouter API call
4. Stream response to client
5. Save complete AI response with role "assistant"

### 3.3 Concurrency Control
- Implement session-level locking during streaming
- Prevent multiple concurrent messages per chat session
- Add endpoint status tracking

## Phase 4: Response Streaming

### 4.1 Streaming Implementation Options
**Option A**: WebSocket connection for real-time streaming
**Option B**: Server-Sent Events (SSE) endpoint
**Option C**: Long polling with chunked responses

### 4.2 Client Communication
- Design streaming response format
- Handle connection errors and reconnection
- Implement proper cleanup on completion/cancellation

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
- **Security**: API keys should be server-side only, properly encrypted
- **Scalability**: Consider connection limits and resource usage
- **UX**: Clear indicators for streaming state and progress
- **Cancellation**: Future endpoint for stopping mid-stream (Phase 8)

## Dependencies to Review
- Current message service structure
- Database transaction handling
- API authentication patterns
- Error handling framework
