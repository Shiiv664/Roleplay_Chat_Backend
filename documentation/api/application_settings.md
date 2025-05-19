# Application Settings API

Endpoints for managing global application settings. This is a singleton resource with only one record.

## Endpoints

### Get Application Settings

```
GET /api/v1/settings
```

Retrieves the current application settings.

**Response:**
```json
{
  "id": 1,
  "default_ai_model_id": 1,
  "default_system_prompt_id": 1,
  "default_user_profile_id": 1,
  "default_avatar_image": "default_avatar.jpg",
  "default_ai_model": {
    "id": 1,
    "label": "gpt-3.5-turbo",
    "description": "OpenAI's GPT-3.5 Turbo model for general purpose conversations."
  },
  "default_system_prompt": {
    "id": 1,
    "label": "basic_roleplay",
    "content": "You are roleplaying as the character described. Stay in character at all times."
  },
  "default_user_profile": {
    "id": 1,
    "label": "default_user",
    "name": "Default User",
    "avatar_image": "default_user.jpg"
  }
}
```

### Update Application Settings

```
PUT /api/v1/settings
```

Updates the application settings.

**Request Body:**
```json
{
  "default_ai_model_id": 2,
  "default_system_prompt_id": 3,
  "default_avatar_image": "new_default_avatar.jpg"
}
```

**Response:**
```json
{
  "id": 1,
  "default_ai_model_id": 2,
  "default_system_prompt_id": 3,
  "default_user_profile_id": 1,
  "default_avatar_image": "new_default_avatar.jpg",
  "default_ai_model": {
    "id": 2,
    "label": "gpt-4",
    "description": "OpenAI's GPT-4 model for more advanced and nuanced conversations."
  },
  "default_system_prompt": {
    "id": 3,
    "label": "creative_writing",
    "content": "You are roleplaying as the character described. Write responses in a creative, engaging narrative style..."
  },
  "default_user_profile": {
    "id": 1,
    "label": "default_user",
    "name": "Default User",
    "avatar_image": "default_user.jpg"
  }
}
```

### Reset Application Settings

```
POST /api/v1/settings/reset
```

Resets the application settings to their default values.

**Response:**
```json
{
  "message": "Application settings reset to defaults",
  "settings": {
    "id": 1,
    "default_ai_model_id": 1,
    "default_system_prompt_id": 1,
    "default_user_profile_id": 1,
    "default_avatar_image": "default_avatar.jpg"
  }
}
```
