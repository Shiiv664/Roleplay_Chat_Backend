# AI Models API

Endpoints for managing AI models.

## Endpoints

### Get All AI Models

```
GET /api/v1/ai-models
```

Retrieves a paginated list of all AI models.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "label": "gpt-3.5-turbo",
      "description": "OpenAI's GPT-3.5 Turbo model for general purpose conversations.",
      "created_at": "2023-01-15T12:00:00Z"
    },
    {
      "id": 2,
      "label": "gpt-4",
      "description": "OpenAI's GPT-4 model for more advanced and nuanced conversations.",
      "created_at": "2023-01-15T12:05:00Z"
    },
    // More AI models...
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 4,
    "total_pages": 1
  }
}
```

### Get AI Model by ID

```
GET /api/v1/ai-models/{ai_model_id}
```

Retrieves a specific AI model by ID.

**Path Parameters:**
- `ai_model_id`: ID of the AI model to retrieve

**Response:**
```json
{
  "id": 1,
  "label": "gpt-3.5-turbo",
  "description": "OpenAI's GPT-3.5 Turbo model for general purpose conversations.",
  "created_at": "2023-01-15T12:00:00Z"
}
```

### Create AI Model

```
POST /api/v1/ai-models
```

Creates a new AI model.

**Request Body:**
```json
{
  "label": "gemini-pro",
  "description": "Google's Gemini Pro model for advanced reasoning and generation."
}
```

**Response:**
```json
{
  "id": 5,
  "label": "gemini-pro",
  "description": "Google's Gemini Pro model for advanced reasoning and generation.",
  "created_at": "2023-01-16T14:20:00Z"
}
```

### Update AI Model

```
PUT /api/v1/ai-models/{ai_model_id}
```

Updates an existing AI model.

**Path Parameters:**
- `ai_model_id`: ID of the AI model to update

**Request Body:**
```json
{
  "description": "Updated description for Google's Gemini Pro model."
}
```

**Response:**
```json
{
  "id": 5,
  "label": "gemini-pro",
  "description": "Updated description for Google's Gemini Pro model.",
  "created_at": "2023-01-16T14:20:00Z"
}
```

### Delete AI Model

```
DELETE /api/v1/ai-models/{ai_model_id}
```

Deletes an AI model.

**Path Parameters:**
- `ai_model_id`: ID of the AI model to delete

**Response:**
```json
{
  "message": "AI model deleted successfully"
}
```
