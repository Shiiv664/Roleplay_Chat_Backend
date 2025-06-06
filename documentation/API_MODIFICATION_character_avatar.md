#### 1.1 Modify Character Creation Endpoint
- **Endpoint**: `POST /api/v1/characters/` (existing endpoint)
- **Request**: `multipart/form-data` with:
  - `label`: string
  - `name`: string
  - `description`: string (optional)
  - `avatar_image`: File (optional) - replaces URL string
- **Response**: Same as current (character object with generated avatar URL)
- **Backend Processing**:
  - Accept both `application/json` (URL mode) and `multipart/form-data` (file mode)
  - When file provided: save to `/uploads/avatars/`, generate unique filename
  - Set `avatar_image` field to generated file path/URL before saving character
- **Validation**:
  - File type: JPG, PNG, GIF, WebP
  - File size: Max 5MB
  - Image dimensions: Max 1024x1024px
- **Security**:
  - Sanitize filenames
  - Generate unique filenames (UUID + extension)
  - Validate file headers (not just extension)

## Implementation Approach

### 1. Database Schema Updates
- The existing `avatar_image` field in the Character model already supports string storage for URLs/paths
- No schema changes required - the field can store either URLs or local file paths

### 2. File Storage Strategy
- **Storage Location**: `/uploads/avatars/` directory (create if not exists)
- **File Naming**: `{uuid4()}.{original_extension}` to prevent conflicts and security issues
- **URL Generation**: `/static/avatars/{filename}` for frontend access

### 3. Backend Implementation Steps
1. **Update Character Creation Endpoint** (`app/api/characters.py`):
   - Accept `Content-Type: multipart/form-data`
   - Handle both JSON (URL mode) and multipart (file upload mode)
   - Add file validation middleware

2. **File Upload Service** (`app/services/file_upload.py`):
   ```python
   async def save_avatar_image(file: UploadFile) -> str:
       # Validate file type and size
       # Generate unique filename
       # Save to uploads/avatars/
       # Return relative path for database storage
   ```

3. **Static File Serving**:
   - Configure FastAPI to serve uploaded files from `/static/avatars/`
   - Ensure proper MIME type headers

### 4. Frontend Integration
- Update character creation forms to support file input
- Handle both drag-and-drop and file picker interfaces
- Preview uploaded images before submission
- Send `multipart/form-data` instead of JSON when file is selected

### 5. Migration Considerations
- Existing characters with URL-based avatars continue to work
- New characters can use either URL or uploaded file approach
- Consider adding image optimization/resizing for performance
