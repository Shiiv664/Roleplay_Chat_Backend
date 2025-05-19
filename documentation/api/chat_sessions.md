# Chat Sessions API

Endpoints for managing chat sessions.

## Endpoints

### Get All Chat Sessions

```
GET /api/v1/chat-sessions
```

Retrieves a paginated list of all chat sessions, with optional filtering by user profile or character.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `user_profile_id` (optional): Filter by user profile ID
- `character_id` (optional): Filter by character ID

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "character_id": 1,
      "user_profile_id": 2,
      "ai_model_id": 2,
      "system_prompt_id": 1,
      "pre_prompt": "Remember you are Sherlock Holmes, the detective.",
      "pre_prompt_enabled": true,
      "post_prompt": null,
      "post_prompt_enabled": false,
      "start_time": "2023-01-15T12:00:00Z",
      "updated_at": "2023-01-15T18:30:00Z",
      "character": {
        "id": 1,
        "name": "Sherlock Holmes",
        "avatar_image": "sherlock.jpg"
      },
      "user_profile": {
        "id": 2,
        "name": "Detective"
      }
    },
    // More chat sessions...
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 3,
    "total_pages": 1
  }
}
```

### Get Chat Session by ID

```
GET /api/v1/chat-sessions/{chat_session_id}
```

Retrieves a specific chat session by ID, including its associated relationships.

**Path Parameters:**
- `chat_session_id`: ID of the chat session to retrieve

**Response:**
```json
{
  "id": 1,
  "character_id": 1,
  "user_profile_id": 2,
  "ai_model_id": 2,
  "system_prompt_id": 1,
  "pre_prompt": "Remember you are Sherlock Holmes, the detective.",
  "pre_prompt_enabled": true,
  "post_prompt": null,
  "post_prompt_enabled": false,
  "start_time": "2023-01-15T12:00:00Z",
  "updated_at": "2023-01-15T18:30:00Z",
  "character": {
    "id": 1,
    "label": "sherlock_holmes",
    "name": "Sherlock Holmes",
    "avatar_image": "sherlock.jpg",
    "description": "The world's only consulting detective..."
  },
  "user_profile": {
    "id": 2,
    "label": "detective",
    "name": "Detective",
    "avatar_image": "detective.jpg"
  },
  "ai_model": {
    "id": 2,
    "label": "gpt-4",
    "description": "OpenAI's GPT-4 model for more advanced and nuanced conversations."
  },
  "system_prompt": {
    "id": 1,
    "label": "basic_roleplay",
    "content": "You are roleplaying as the character described. Stay in character at all times."
  }
}
```

### Create Chat Session

```
POST /api/v1/chat-sessions
```

Creates a new chat session.

**Request Body:**
```json
{
  "character_id": 3,
  "user_profile_id": 1,
  "ai_model_id": 1,
  "system_prompt_id": 2,
  "pre_prompt": "Remember to talk like HAL 9000.",
  "pre_prompt_enabled": true,
  "post_prompt": "Always be slightly ominous.",
  "post_prompt_enabled": true
}
```

**Response:**
```json
{
  "id": 4,
  "character_id": 3,
  "user_profile_id": 1,
  "ai_model_id": 1,
  "system_prompt_id": 2,
  "pre_prompt": "Remember to talk like HAL 9000.",
  "pre_prompt_enabled": true,
  "post_prompt": "Always be slightly ominous.",
  "post_prompt_enabled": true,
  "start_time": "2023-01-16T14:00:00Z",
  "updated_at": "2023-01-16T14:00:00Z",
  "character": {
    "id": 3,
    "name": "HAL 9000",
    "avatar_image": "hal9000.jpg"
  },
  "user_profile": {
    "id": 1,
    "name": "Default User"
  }
}
```

### Update Chat Session

```
PUT /api/v1/chat-sessions/{chat_session_id}
```

Updates an existing chat session.

**Path Parameters:**
- `chat_session_id`: ID of the chat session to update

**Request Body:**
```json
{
  "ai_model_id": 2,
  "pre_prompt": "Updated pre-prompt for HAL 9000.",
  "post_prompt_enabled": false
}
```

**Response:**
```json
{
  "id": 4,
  "character_id": 3,
  "user_profile_id": 1,
  "ai_model_id": 2,
  "system_prompt_id": 2,
  "pre_prompt": "Updated pre-prompt for HAL 9000.",
  "pre_prompt_enabled": true,
  "post_prompt": "Always be slightly ominous.",
  "post_prompt_enabled": false,
  "start_time": "2023-01-16T14:00:00Z",
  "updated_at": "2023-01-16T14:45:00Z"
}
```

### Delete Chat Session

```
DELETE /api/v1/chat-sessions/{chat_session_id}
```

Deletes a chat session and all associated messages.

**Path Parameters:**
- `chat_session_id`: ID of the chat session to delete

**Response:**
```json
{
  "message": "Chat session deleted successfully"
}
```
