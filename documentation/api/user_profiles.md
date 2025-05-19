# User Profiles API

Endpoints for managing user profiles.

## Endpoints

### Get All User Profiles

```
GET /api/v1/user-profiles
```

Retrieves a paginated list of all user profiles.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "label": "default_user",
      "name": "Default User",
      "avatar_image": "default_user.jpg",
      "description": "Default user profile for casual conversations.",
      "created_at": "2023-01-15T12:00:00Z",
      "updated_at": "2023-01-15T12:00:00Z"
    },
    // More user profiles...
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 3,
    "total_pages": 1
  }
}
```

### Get User Profile by ID

```
GET /api/v1/user-profiles/{user_profile_id}
```

Retrieves a specific user profile by ID.

**Path Parameters:**
- `user_profile_id`: ID of the user profile to retrieve

**Response:**
```json
{
  "id": 1,
  "label": "default_user",
  "name": "Default User",
  "avatar_image": "default_user.jpg",
  "description": "Default user profile for casual conversations.",
  "created_at": "2023-01-15T12:00:00Z",
  "updated_at": "2023-01-15T12:00:00Z"
}
```

### Create User Profile

```
POST /api/v1/user-profiles
```

Creates a new user profile.

**Request Body:**
```json
{
  "label": "researcher",
  "name": "Academic Researcher",
  "avatar_image": "researcher.jpg",
  "description": "A profile for academic and research-focused conversations."
}
```

**Response:**
```json
{
  "id": 4,
  "label": "researcher",
  "name": "Academic Researcher",
  "avatar_image": "researcher.jpg",
  "description": "A profile for academic and research-focused conversations.",
  "created_at": "2023-01-16T09:30:00Z",
  "updated_at": "2023-01-16T09:30:00Z"
}
```

### Update User Profile

```
PUT /api/v1/user-profiles/{user_profile_id}
```

Updates an existing user profile.

**Path Parameters:**
- `user_profile_id`: ID of the user profile to update

**Request Body:**
```json
{
  "name": "Academic Researcher PhD",
  "description": "Updated description for the researcher profile."
}
```

**Response:**
```json
{
  "id": 4,
  "label": "researcher",
  "name": "Academic Researcher PhD",
  "avatar_image": "researcher.jpg",
  "description": "Updated description for the researcher profile.",
  "created_at": "2023-01-16T09:30:00Z",
  "updated_at": "2023-01-16T10:15:00Z"
}
```

### Delete User Profile

```
DELETE /api/v1/user-profiles/{user_profile_id}
```

Deletes a user profile.

**Path Parameters:**
- `user_profile_id`: ID of the user profile to delete

**Response:**
```json
{
  "message": "User profile deleted successfully"
}
```
