# API Documentation

This directory contains documentation for the LLM Roleplay Chat Client API endpoints.

## API Overview

The API follows RESTful principles and uses JSON for request and response bodies. The base URL for all endpoints is `/api/v1`.

## Authentication

Authentication will be implemented in future versions of the API. Currently, all endpoints are accessible without authentication for development purposes.

## Available Endpoints

- [Characters API](characters.md)
- [UserProfiles API](user_profiles.md)
- [AIModels API](ai_models.md)
- [SystemPrompts API](system_prompts.md)
- [ChatSessions API](chat_sessions.md)
- [Messages API](messages.md)
- [ApplicationSettings API](application_settings.md)

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests:

- 200 OK: The request was successful
- 201 Created: A new resource was created successfully
- 400 Bad Request: The request was malformed or contains invalid parameters
- 404 Not Found: The requested resource was not found
- 500 Internal Server Error: An unexpected error occurred on the server

Error responses include a JSON body with details about the error:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found",
    "details": "Character with ID 123 does not exist"
  }
}
```

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: Page number (1-based)
- `per_page`: Number of items per page (default: 20, max: 100)

Paginated responses include metadata about the pagination:

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 42,
    "total_pages": 3
  }
}
```
