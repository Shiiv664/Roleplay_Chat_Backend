# PNG Character Extraction API - Frontend Reference

## Overview

This API endpoint extracts character data from PNG files containing embedded Character Card v2 metadata (chub.ai format) and returns structured character data plus a clean avatar image for frontend use.

## Endpoint

**POST** `/api/v1/characters/extract-png`

## Request Format

### Content Type
```
Content-Type: multipart/form-data
```

### Form Data
- **file** (required): PNG file containing Character Card v2 metadata
  - Maximum size: 10MB
  - Format: PNG only
  - Must contain embedded character data

### Example JavaScript Request
```javascript
const formData = new FormData();
formData.append('file', selectedFile); // selectedFile from file input

const response = await fetch('/api/v1/characters/extract-png', {
  method: 'POST',
  body: formData
  // Note: Don't set Content-Type header - browser sets it automatically for FormData
});

const result = await response.json();
```

## Response Format

### Success Response (200)
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
      "mime_type": "image/png",
      "size_bytes": 1024
    },
    "extraction_info": {
      "source_format": "Character Card v2",
      "original_filename": "uploaded_file.png",
      "extracted_at": "2024-08-14T12:00:00Z",
      "image_info": {
        "format": "PNG",
        "width": 512,
        "height": 512
      }
    }
  }
}
```

### Error Response (4xx/5xx)
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_FILE_FORMAT` | 400 | File is not a valid PNG image |
| `NO_CHARACTER_DATA` | 400 | PNG contains no Character Card v2 metadata |
| `INVALID_CHARACTER_DATA` | 400 | Character data is corrupted or invalid |
| `NO_FILE_PROVIDED` | 400 | No file was uploaded |
| `INVALID_REQUEST_FORMAT` | 400 | Content-Type is not multipart/form-data |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB limit |
| `PROCESSING_ERROR` | 500 | Internal error during extraction |

## Frontend Integration Workflow

### 1. File Upload Handler
```javascript
function handleFileUpload(file) {
  // Validate file type
  if (!file.type === 'image/png') {
    showError('Please select a PNG file');
    return;
  }
  
  // Validate file size (10MB = 10485760 bytes)
  if (file.size > 10485760) {
    showError('File must be smaller than 10MB');
    return;
  }
  
  extractCharacterData(file);
}
```

### 2. API Call
```javascript
async function extractCharacterData(file) {
  try {
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/v1/characters/extract-png', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      populateCharacterForm(result.data);
    } else {
      handleExtractError(result.error);
    }
  } catch (error) {
    showError('Failed to extract character data');
  } finally {
    setLoading(false);
  }
}
```

### 3. Form Population
```javascript
function populateCharacterForm(extractedData) {
  const { character_data, avatar_image } = extractedData;
  
  // Populate form fields
  document.getElementById('name').value = character_data.name;
  document.getElementById('label').value = character_data.label;
  document.getElementById('description').value = character_data.description;
  
  // Handle first messages
  if (character_data.first_messages.length > 0) {
    document.getElementById('first_message').value = character_data.first_messages[0];
    
    // Display alternate greetings if any
    const alternates = character_data.first_messages.slice(1);
    populateAlternateGreetings(alternates);
  }
  
  // Display avatar preview
  displayAvatarPreview(avatar_image);
}
```

### 4. Avatar Preview
```javascript
function displayAvatarPreview(avatarImage) {
  const previewImg = document.getElementById('avatar-preview');
  const dataUrl = `data:${avatarImage.mime_type};base64,${avatarImage.data}`;
  
  previewImg.src = dataUrl;
  previewImg.style.display = 'block';
  
  // Store for later character creation
  window.extractedAvatar = avatarImage;
}
```

### 5. Error Handling
```javascript
function handleExtractError(error) {
  const errorMessages = {
    'INVALID_FILE_FORMAT': 'Please upload a valid PNG file',
    'NO_CHARACTER_DATA': 'This PNG file does not contain character data',
    'INVALID_CHARACTER_DATA': 'The character data in this file is corrupted',
    'FILE_TOO_LARGE': 'File is too large. Please use a file smaller than 10MB',
    'NO_FILE_PROVIDED': 'Please select a file to upload'
  };
  
  const message = errorMessages[error.code] || error.message || 'Failed to extract character data';
  showError(message);
}
```

## Usage Notes

### Important Considerations
- **No Database Operations**: This endpoint only extracts data - no character is created in the database
- **Form Prefilling**: Use extracted data to prefill your character creation form
- **User Review Required**: Always allow users to review and modify extracted data before creating the character
- **Character Creation**: Create the actual character using the standard `POST /api/v1/characters` endpoint after user review

### Avatar Handling
- **Clean Image**: The returned avatar has all metadata stripped for security
- **Base64 Format**: Avatar data is base64-encoded and ready to display
- **File Creation**: If needed, convert base64 back to File object for character creation:

```javascript
function base64ToFile(base64Data, filename, mimeType) {
  const byteCharacters = atob(base64Data);
  const byteNumbers = new Array(byteCharacters.length);
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  
  const byteArray = new Uint8Array(byteNumbers);
  return new File([byteArray], filename, { type: mimeType });
}
```

### Security
- The API automatically validates file format and size
- All text content is sanitized server-side
- Avatar images are stripped of potentially malicious metadata
- Rate limiting is applied to prevent abuse

### Performance Tips
- Show loading indicators during extraction (can take a few seconds for large files)
- Validate files client-side before uploading to improve user experience
- Consider caching extracted data in component state until character creation is complete