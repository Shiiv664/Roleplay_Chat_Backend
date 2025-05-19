# Characters API

Endpoints for managing character data.

## Endpoints

### Get All Characters

```
GET /api/v1/characters
```

Retrieves a paginated list of all characters.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "label": "sherlock_holmes",
      "name": "Sherlock Holmes",
      "avatar_image": "sherlock.jpg",
      "description": "The world's only consulting detective...",
      "created_at": "2023-01-15T12:00:00Z",
      "updated_at": "2023-01-15T12:00:00Z"
    },
    // More characters...
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 42,
    "total_pages": 3
  }
}
```

### Get Character by ID

```
GET /api/v1/characters/{character_id}
```

Retrieves a specific character by ID.

**Path Parameters:**
- `character_id`: ID of the character to retrieve

**Response:**
```json
{
  "id": 1,
  "label": "sherlock_holmes",
  "name": "Sherlock Holmes",
  "avatar_image": "sherlock.jpg",
  "description": "The world's only consulting detective...",
  "created_at": "2023-01-15T12:00:00Z",
  "updated_at": "2023-01-15T12:00:00Z"
}
```

### Create Character

```
POST /api/v1/characters
```

Creates a new character.

**Request Body:**
```json
{
  "label": "watson",
  "name": "Dr. John Watson",
  "avatar_image": "watson.jpg",
  "description": "Sherlock Holmes' trusted friend and companion..."
}
```

**Response:**
```json
{
  "id": 2,
  "label": "watson",
  "name": "Dr. John Watson",
  "avatar_image": "watson.jpg",
  "description": "Sherlock Holmes' trusted friend and companion...",
  "created_at": "2023-01-15T13:30:00Z",
  "updated_at": "2023-01-15T13:30:00Z"
}
```

### Update Character

```
PUT /api/v1/characters/{character_id}
```

Updates an existing character.

**Path Parameters:**
- `character_id`: ID of the character to update

**Request Body:**
```json
{
  "name": "Dr. John H. Watson",
  "description": "Updated description for Dr. Watson..."
}
```

**Response:**
```json
{
  "id": 2,
  "label": "watson",
  "name": "Dr. John H. Watson",
  "avatar_image": "watson.jpg",
  "description": "Updated description for Dr. Watson...",
  "created_at": "2023-01-15T13:30:00Z",
  "updated_at": "2023-01-15T14:45:00Z"
}
```

### Delete Character

```
DELETE /api/v1/characters/{character_id}
```

Deletes a character.

**Path Parameters:**
- `character_id`: ID of the character to delete

**Response:**
```json
{
  "message": "Character deleted successfully"
}
```
