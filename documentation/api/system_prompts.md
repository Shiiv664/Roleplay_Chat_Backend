# System Prompts API

Endpoints for managing system prompts.

## Endpoints

### Get All System Prompts

```
GET /api/v1/system-prompts
```

Retrieves a paginated list of all system prompts.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "label": "basic_roleplay",
      "content": "You are roleplaying as the character described. Stay in character at all times.",
      "created_at": "2023-01-15T12:00:00Z"
    },
    {
      "id": 2,
      "label": "detailed_roleplay",
      "content": "You are roleplaying as the character described. Stay in character at all times. Use the character's typical speech patterns, vocabulary, and mannerisms...",
      "created_at": "2023-01-15T12:05:00Z"
    },
    // More system prompts...
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 3,
    "total_pages": 1
  }
}
```

### Get System Prompt by ID

```
GET /api/v1/system-prompts/{system_prompt_id}
```

Retrieves a specific system prompt by ID.

**Path Parameters:**
- `system_prompt_id`: ID of the system prompt to retrieve

**Response:**
```json
{
  "id": 1,
  "label": "basic_roleplay",
  "content": "You are roleplaying as the character described. Stay in character at all times.",
  "created_at": "2023-01-15T12:00:00Z"
}
```

### Create System Prompt

```
POST /api/v1/system-prompts
```

Creates a new system prompt.

**Request Body:**
```json
{
  "label": "educational_roleplay",
  "content": "You are roleplaying as the character described, with emphasis on educational content. Make your responses informative while staying in character."
}
```

**Response:**
```json
{
  "id": 4,
  "label": "educational_roleplay",
  "content": "You are roleplaying as the character described, with emphasis on educational content. Make your responses informative while staying in character.",
  "created_at": "2023-01-16T11:40:00Z"
}
```

### Update System Prompt

```
PUT /api/v1/system-prompts/{system_prompt_id}
```

Updates an existing system prompt.

**Path Parameters:**
- `system_prompt_id`: ID of the system prompt to update

**Request Body:**
```json
{
  "content": "Updated system prompt text with improved instructions for educational roleplay."
}
```

**Response:**
```json
{
  "id": 4,
  "label": "educational_roleplay",
  "content": "Updated system prompt text with improved instructions for educational roleplay.",
  "created_at": "2023-01-16T11:40:00Z"
}
```

### Delete System Prompt

```
DELETE /api/v1/system-prompts/{system_prompt_id}
```

Deletes a system prompt.

**Path Parameters:**
- `system_prompt_id`: ID of the system prompt to delete

**Response:**
```json
{
  "message": "System prompt deleted successfully"
}
```
