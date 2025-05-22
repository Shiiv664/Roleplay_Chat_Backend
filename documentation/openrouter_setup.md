# OpenRouter API Setup Guide

This guide explains how to set up OpenRouter API integration for the LLM Roleplay Chat Client.

## Prerequisites

- Python 3.10+
- OpenRouter API account and API key
- Application dependencies installed (`pip install -r requirements.txt`)

## Encryption Key Setup

The application uses Fernet symmetric encryption to securely store OpenRouter API keys. You need to set up an encryption key using one of these methods:

### Method 1: Environment Variable (Recommended for Production)

Set the `ENCRYPTION_KEY` environment variable:

```bash
# Generate a new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set the environment variable (Linux/Mac)
export ENCRYPTION_KEY="your-generated-key-here"

# Set the environment variable (Windows)
set ENCRYPTION_KEY=your-generated-key-here
```

### Method 2: Key File (Recommended for Development)

Create an `encryption.key` file in the project root:

```bash
# Generate and save key to file
python -c "from cryptography.fernet import Fernet; open('encryption.key', 'w').write(Fernet.generate_key().decode())"
```

**Important:** The `encryption.key` file is automatically gitignored to prevent accidental commits.

## OpenRouter API Key Configuration

### Step 1: Obtain API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account or sign in
3. Navigate to your API keys section
4. Generate a new API key

### Step 2: Configure API Key

Use the application's settings API to securely store your OpenRouter API key:

```bash
# Set the API key using curl
curl -X PUT http://localhost:5000/api/v1/settings/openrouter-api-key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-or-your-api-key-here"}'

# Check API key status
curl http://localhost:5000/api/v1/settings/openrouter-api-key
```

### Step 3: Verify Configuration

Test that the OpenRouter integration is working:

```python
from app.services.application_settings_service import ApplicationSettingsService
from app.services.openrouter.client import OpenRouterClient
from app.utils.db import session_scope

# Get the encrypted API key
with session_scope() as session:
    settings_service = ApplicationSettingsService(session)
    api_key = settings_service.get_openrouter_api_key()

    if api_key:
        # Test the connection
        client = OpenRouterClient(api_key)
        if client.test_connection():
            print("✅ OpenRouter API connection successful!")
        else:
            print("❌ OpenRouter API connection failed!")
    else:
        print("❌ No OpenRouter API key configured!")
```

## Configuration Options

The following environment variables can be used to customize OpenRouter behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_TIMEOUT` | 120 | Request timeout in seconds |
| `OPENROUTER_STREAM_CHUNK_SIZE` | 1024 | Streaming chunk size in bytes |
| `OPENROUTER_MAX_CONNECTIONS_PER_SESSION` | 5 | Max concurrent connections per chat session |
| `OPENROUTER_STREAM_TIMEOUT` | 300 | Stream inactivity timeout in seconds |
| `OPENROUTER_CONNECTION_POOL_SIZE` | 10 | HTTP connection pool size |
| `OPENROUTER_MAX_RETRIES` | 3 | Maximum number of request retries |

Example `.env` file:
```
ENCRYPTION_KEY=your-encryption-key-here
OPENROUTER_TIMEOUT=180
OPENROUTER_STREAM_CHUNK_SIZE=2048
OPENROUTER_MAX_CONNECTIONS_PER_SESSION=3
```

## Security Notes

1. **Never commit encryption keys or API keys to version control**
2. Use environment variables in production environments
3. Rotate API keys regularly
4. Monitor API usage and costs through OpenRouter dashboard
5. The encryption key must be kept secure and backed up safely

## Troubleshooting

### Common Issues

**"No encryption key found" error:**
- Ensure `ENCRYPTION_KEY` environment variable is set OR `encryption.key` file exists
- Verify the key is a valid Fernet key (base64-encoded, 32 bytes)

**"OpenRouter API request failed" error:**
- Check your API key is valid and active
- Verify network connectivity to openrouter.ai
- Check rate limits and usage quotas in OpenRouter dashboard

**"Failed to decrypt API key" error:**
- The encryption key may have changed
- Re-set your OpenRouter API key using the settings API

### Support

For additional support:
- Check the [OpenRouter API documentation](https://openrouter.ai/docs)
- Review application logs for detailed error messages
- Ensure all dependencies are properly installed
