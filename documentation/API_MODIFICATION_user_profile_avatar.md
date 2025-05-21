# API Modification: User Profile Avatar Upload

## Overview
This document outlines the modifications needed to add avatar image upload functionality to the User Profile API endpoints. The implementation follows the same pattern as the Character avatar upload feature.

## API Changes

### 1.1 Modify User Profile Creation Endpoint
- **Endpoint**: `POST /api/v1/user-profiles/` (existing endpoint)
- **Request**: `multipart/form-data` with:
  - `label`: string
  - `name`: string
  - `description`: string (optional)
  - `avatar_image`: File (optional) - replaces URL string
- **Response**: Same as current (user profile object with generated avatar URL)
- **Backend Processing**:
  - Accept both `application/json` (URL mode) and `multipart/form-data` (file mode)
  - When file provided: save to `/uploads/avatars/`, generate unique filename
  - Set `avatar_image` field to generated file path/URL before saving user profile
- **Validation**:
  - File type: JPG, PNG, GIF, WebP
  - File size: Max 5MB
  - Image dimensions: Max 1024x1024px
- **Security**:
  - Sanitize filenames
  - Generate unique filenames (UUID + extension)
  - Validate file headers (not just extension)

### 1.2 Modify User Profile Update Endpoint
- **Endpoint**: `PUT /api/v1/user-profiles/{id}` (existing endpoint)
- **Current Behavior**: JSON-only updates
- **Enhanced Behavior**: Support both JSON and multipart/form-data for avatar updates
- **Implementation**: Same file upload logic as creation endpoint

## Implementation Approach

### 1. Database Schema Updates
- The existing `avatar_image` field in the UserProfile model already supports string storage for URLs/paths
- No schema changes required - the field can store either URLs or local file paths

### 2. File Storage Strategy
- **Storage Location**: `/uploads/avatars/` directory (shared with Character avatars)
- **File Naming**: `{uuid4()}.{original_extension}` to prevent conflicts and security issues
- **URL Generation**: `/uploads/avatars/{filename}` for frontend access

### 3. Backend Implementation Steps
1. **Update User Profile Creation Endpoint** (`app/api/namespaces/user_profiles.py`):
   - Accept `Content-Type: multipart/form-data`
   - Handle both JSON (URL mode) and multipart (file upload mode)
   - Add file validation using existing FileUploadService

2. **Reuse Existing File Upload Service** (`app/services/file_upload_service.py`):
   - The FileUploadService already exists and handles avatar image uploads
   - Use `save_avatar_image_sync()` method for synchronous file processing
   - No additional service changes needed

3. **Add Avatar URL Method to UserProfile Model**:
   - Add `get_avatar_url()` method similar to Character model
   - Generate proper URL for uploaded avatar images

4. **Update Serialization**:
   - Create `serialize_user_profile()` function to include avatar_url
   - Ensure consistent response format with avatar URL generation

### 4. Model Updates Required
1. **UserProfile Model** (`app/models/user_profile.py`):
   - Add `get_avatar_url()` method for URL generation

2. **API Models** (`app/api/models/user_profile.py`):
   - Add `user_profile_create_multipart_model` for form documentation
   - Include `avatar_url` field in response models

### 5. Migration Considerations
- Existing user profiles with URL-based avatars continue to work
- New user profiles can use either URL or uploaded file approach
- File storage directory is shared with Character avatars for consistency
- No database migrations needed

### 6. Testing Requirements
- Test multipart/form-data uploads
- Test JSON-only creation (backwards compatibility)
- Test file validation (size, type, dimensions)
- Test avatar URL generation
- Test error handling for invalid uploads

## Files to Modify
1. `app/api/namespaces/user_profiles.py` - Main implementation
2. `app/models/user_profile.py` - Add get_avatar_url() method
3. `app/api/models/user_profile.py` - Add multipart model and avatar_url field
4. Test files for comprehensive coverage

## Dependencies
- Existing FileUploadService (already implemented)
- Existing ValidationError and FileUploadError classes
- Flask file upload handling (already in use)
