# PNG Character Data Extraction API

## Overview

This API endpoint extracts character data from PNG files containing embedded Character Card v2 format metadata (chub.ai format) and returns both the parsed character data and a clean avatar image. This enables users to import existing characters from the chub.ai ecosystem into the application.

## Endpoint Specification

**POST** `/api/v1/characters/extract-png`

### Request
- **Content-Type**: `multipart/form-data`
- **Body**: PNG file upload with embedded Character Card v2 data

### Response Format
```json
{
  "success": true,
  "data": {
    "character_data": {
      "name": "Character Name",
      "label": "character_name_imported_20240814",
      "description": "Character description and personality traits",
      "first_messages": [
        "Primary greeting message",
        "Alternative greeting 1",
        "Alternative greeting 2"
      ]
    },
    "avatar_image": {
      "filename": "character_avatar.png",
      "data": "base64_encoded_clean_png_data",
      "mime_type": "image/png"
    }
  }
}
```

### Error Responses
```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "File is not a valid PNG image"
  }
}
```

**Error Codes:**
- `INVALID_FILE_FORMAT` (400) - Not a valid PNG file
- `NO_CHARACTER_DATA` (400) - PNG contains no Character Card v2 metadata
- `INVALID_CHARACTER_DATA` (400) - Character data is corrupted or invalid
- `FILE_TOO_LARGE` (413) - File exceeds maximum size limit
- `PROCESSING_ERROR` (500) - Internal error during extraction

## Data Mapping

### Character Card v2 → Application Model

| Source Field | Target Field | Processing |
|-------------|-------------|------------|
| `data.name` | `name` | Direct mapping |
| `data.name` | `label` | Auto-generated: `{name}_imported_{timestamp}` |
| `data.description` | `description` | Direct mapping |
| `data.first_mes` | `first_messages[0]` | Primary greeting |
| `data.alternate_greetings[]` | `first_messages[1:]` | Additional greetings |
| PNG image | `avatar_image` | Stripped of all metadata |

### Ignored Fields
The following Character Card v2 fields are ignored during extraction:
- `personality` (often redundant with description)
- `scenario`, `mes_example`, `creator_notes` 
- `system_prompt`, `post_history_instructions`
- `tags`, `creator`, `character_version`
- `extensions`, `character_book`

## Implementation Requirements

### Core Components

1. **PNG Parser Service** (`app/services/png_character_parser.py`)
   - Extract tEXt chunks from PNG files
   - Decode base64 character data
   - Validate Character Card v2 format
   - Handle parsing errors gracefully

2. **Image Processing Service** (`app/services/image_processing_service.py`)
   - Strip metadata from PNG files using Pillow
   - Return clean PNG data for avatar use
   - Maintain image quality and dimensions

3. **Character Extract Service** (`app/services/character_extract_service.py`)
   - Orchestrate the extraction process
   - Map Character Card v2 data to application format
   - Generate unique labels and validate data

4. **API Endpoint** (`app/api/namespaces/characters.py`)
   - Handle file upload validation
   - Return structured response with character data and avatar
   - Implement proper error handling

### Technical Dependencies

**Required Libraries:**
- `Pillow (PIL)` - PNG processing and metadata removal
- `base64` - Metadata decoding (built-in)
- `json` - JSON parsing (built-in)

**File Size Limits:**
- Maximum PNG file size: 10MB
- Supported formats: PNG only

## Frontend Integration Workflow

1. **User uploads PNG file** via file input
2. **Frontend calls extract API** with the PNG file
3. **Backend processes and returns** character data + clean avatar
4. **Frontend prefills character form** with extracted data
5. **Frontend displays avatar preview** using the clean PNG data
6. **User reviews and modifies** data as needed
7. **User submits character** through normal creation flow
8. **Avatar gets stored** using existing FileUploadService

## Security Considerations

### File Validation
- Verify PNG magic bytes (`89 50 4E 47`)
- Limit file size to prevent DoS attacks
- Validate image dimensions (reasonable limits)
- Scan for malicious content in image data

### Data Sanitization  
- Sanitize all extracted text fields for XSS prevention
- Validate JSON structure before processing
- Escape special characters in descriptions
- Limit text field lengths

### Rate Limiting
- Implement rate limiting on extraction endpoint
- Track extraction frequency per user/IP
- Prevent automated scraping attempts

## Testing Strategy

### Unit Tests
- PNG metadata extraction accuracy
- Character Card v2 parsing edge cases
- Data mapping validation
- Error handling scenarios
- Image processing functionality

### Integration Tests
- End-to-end extraction workflow
- API endpoint response format
- File upload handling
- Error response consistency

### Test Data Requirements
- Valid Character Card v2 PNG files
- Invalid/corrupted PNG files
- PNG files without character data
- Edge cases (missing fields, malformed JSON)

## Error Handling Scenarios

### Invalid Input
- Non-PNG files uploaded
- Corrupted PNG files
- PNG files without tEXt chunks
- Invalid base64 encoding in metadata

### Missing Data
- Required Character Card v2 fields missing
- Empty or null character name/description
- Malformed JSON structure

### Processing Failures
- Image processing errors
- Memory issues with large files
- Encoding/decoding failures

## Performance Considerations

- Stream-based file processing for large PNGs
- Memory-efficient metadata extraction
- Async operations where possible
- Proper cleanup of temporary data

## Configuration

### Environment Variables
```bash
# Maximum file size for PNG extraction (bytes)
MAX_PNG_EXTRACT_SIZE=10485760  # 10MB

# Extraction rate limiting (extractions per hour)
PNG_EXTRACT_RATE_LIMIT=20

# Enable/disable extraction feature
PNG_EXTRACTION_ENABLED=true
```

## Implementation Notes

- This is a **data extraction endpoint**, not an import endpoint
- No database operations are performed - only data extraction and processing
- Frontend handles the actual character creation after user review
- Clean separation between extraction and character creation workflows
- Maintains existing character creation validation and business logic