# Issue: Missing Specific Response Models in OpenAPI Documentation

**Priority**: Medium
**Category**: API Documentation
**Created**: 2025-05-22

## Problem Description

Currently, most API endpoints use the generic `Response` model for their success responses, which provides no information about the actual data structure returned. This makes it difficult for frontend developers to understand what fields are available in API responses.

**Example of current problem:**
```json
// Most endpoints return this generic schema:
{
  "success": boolean,
  "data": "object",  // ❌ No specific structure defined
  "meta": "object",
  "error": "object"
}
```

**What we need:**
```json
// Specific schemas like we implemented for OpenRouter:
{
  "success": true,
  "data": {
    "has_api_key": boolean,  // ✅ Specific fields documented
    "key_length": integer
  }
}
```

## Affected Endpoints

### Characters API (`/characters/`)
- `GET /characters/` - Should document character list with pagination
- `POST /characters/` - Should document created character structure
- `GET /characters/{id}` - Should document single character structure
- `PUT /characters/{id}` - Should document updated character structure
- `GET /characters/search` - Should document search results structure

### User Profiles API (`/user-profiles/`)
- `GET /user-profiles/` - Should document user profile list structure
- `POST /user-profiles/` - Should document created user profile structure
- `GET /user-profiles/{id}` - Should document single user profile structure
- `PUT /user-profiles/{id}` - Should document updated user profile structure
- `GET /user-profiles/search` - Should document search results structure

### AI Models API (`/ai-models/`)
- `GET /ai-models/` - Should document AI model list structure
- `POST /ai-models/` - Should document created AI model structure
- `GET /ai-models/{id}` - Should document single AI model structure
- `PUT /ai-models/{id}` - Should document updated AI model structure
- `GET /ai-models/search` - Should document search results structure

### System Prompts API (`/system-prompts/`)
- `GET /system-prompts/` - Should document system prompt list structure
- `POST /system-prompts/` - Should document created system prompt structure
- `GET /system-prompts/{id}` - Should document single system prompt structure
- `PUT /system-prompts/{id}` - Should document updated system prompt structure
- `GET /system-prompts/search` - Should document search results structure

### Chat Sessions API (`/chat-sessions/`)
- `GET /chat-sessions/` - Should document chat session list structure
- `POST /chat-sessions/` - Should document created chat session structure
- `GET /chat-sessions/{id}` - Should document single chat session structure
- `PUT /chat-sessions/{id}` - Should document updated chat session structure
- `GET /chat-sessions/character/{character_id}` - Should document filtered list structure
- `GET /chat-sessions/user-profile/{profile_id}` - Should document filtered list structure
- `GET /chat-sessions/recent` - Should document recent sessions structure

### Messages API (`/messages/`)
- `GET /messages/chat-sessions/{chat_session_id}` - Should document message list structure
- `POST /messages/chat-sessions/{chat_session_id}` - Should document created message structure
- `GET /messages/{message_id}` - Should document single message structure
- `PUT /messages/{message_id}` - Should document updated message structure
- `POST /messages/chat-sessions/{chat_session_id}/user-message` - Should document user+AI message structure
- `POST /messages/chat-sessions/{chat_session_id}/regenerate` - Should document regenerated message structure

### Settings API (`/settings/`)
- `GET /settings/` - Should document settings structure (partially fixed)
- `PUT /settings/` - Should document updated settings structure
- `POST /settings/reset` - Should document reset confirmation structure

## Solution Approach

### 1. Create Specific Response Models
For each endpoint, create dedicated response models that clearly define:
- The exact structure of the `data` field
- Field types and descriptions
- Optional vs required fields
- Nested object structures

### 2. Example Pattern (Following OpenRouter Implementation)
```python
# In app/api/models/characters.py
character_response_model = Model(
    "CharacterResponse",
    {
        "success": fields.Boolean(default=True, description="Success status"),
        "data": fields.Nested(character_model, description="Character data"),
    }
)

character_list_response_model = Model(
    "CharacterListResponse",
    {
        "success": fields.Boolean(default=True, description="Success status"),
        "data": fields.List(fields.Nested(character_model), description="List of characters"),
        "meta": fields.Nested(pagination_model, description="Pagination information"),
    }
)
```

### 3. Update Endpoint Decorators
Replace generic `@api.response(200, "Success", response_model)` with specific:
```python
@api.marshal_with(character_response_model)
def get_character(self, id):
    # ...
```

### 4. Common Patterns to Implement
- **Single Entity Response**: `{success: true, data: {entity}}`
- **List Response**: `{success: true, data: [entities], meta: {pagination}}`
- **Creation Response**: `{success: true, data: {created_entity}}`
- **Update Response**: `{success: true, data: {updated_entity}}`
- **Deletion Response**: `{success: true, data: {message: "Deleted successfully"}}`
- **Search Response**: `{success: true, data: [matching_entities], meta: {pagination, query}}`

## Benefits of Fixing This

1. **Frontend Development**: Developers know exactly what fields are available
2. **Type Safety**: Can generate TypeScript interfaces from OpenAPI spec
3. **API Testing**: Clear expectations for response validation
4. **Documentation**: Self-documenting API with precise field descriptions
5. **Consistency**: Standardized response formats across all endpoints

## Implementation Priority

1. **High Priority**: Core CRUD operations (GET, POST, PUT, DELETE for main entities)
2. **Medium Priority**: Search and filter endpoints
3. **Low Priority**: Utility endpoints and edge cases

## Reference Implementation

The OpenRouter API key endpoints (`/settings/openrouter-api-key`) provide a good example of properly documented responses with specific models that should be replicated across all endpoints.

## Files to Modify

- `app/api/models/*.py` - Add response models for each namespace
- `app/api/namespaces/*.py` - Update decorators to use specific response models
- Test the changes by running `python scripts/export_openapi.py` and verifying the generated documentation

## Notes

This is a substantial but important improvement that will significantly enhance the developer experience when working with this API. The work can be done incrementally, starting with the most commonly used endpoints.
