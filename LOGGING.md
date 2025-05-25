# Debug Logging Configuration

The LLM Roleplay Chat Client has configurable debug logging to help with development and troubleshooting.

## Environment Variables

### `LOG_OPENROUTER_PAYLOAD=true`
**Recommended for frequent checking**
- Logs only the clean JSON payload sent to OpenRouter
- Perfect for checking message formatting and system prompts
- Minimal, focused output
- File: `logs/openrouter_payload.log`

### `DEBUG_OPENROUTER=true` 
**Full OpenRouter debugging**
- Comprehensive logging of all OpenRouter API interactions
- Includes headers, response status, streaming chunks
- Verbose output for deep troubleshooting  
- File: `logs/openrouter_debug.log`

### `DEBUG_MESSAGE_SERVICE=true`
**Message service debugging**
- System prompt construction details
- Message history formatting  
- Database operations
- File: `logs/message_service_debug.log`

## Usage Examples

### Quick Payload Checking (Recommended)
```bash
# Enable just the OpenRouter payload logging
export LOG_OPENROUTER_PAYLOAD=true
./venv/bin/python app.py

# Check the clean JSON output
tail -f logs/openrouter_payload.log
```

### Full Debug Mode
```bash
# Enable all debug logging
export DEBUG_OPENROUTER=true
export DEBUG_MESSAGE_SERVICE=true  
export LOG_OPENROUTER_PAYLOAD=true
./venv/bin/python app.py
```

### Production Mode (Default)
```bash
# No debug logging (clean production logs only)
./venv/bin/python app.py
```

## Log Files

When debug logging is enabled, files are created in:
- `logs/openrouter_payload.log` - Clean JSON payloads only
- `logs/openrouter_debug.log` - Full OpenRouter API debugging  
- `logs/message_service_debug.log` - Message service debugging

## Sample Output

### OpenRouter Payload Log
```
2025-05-25 01:30:15 - 🤖 Model: gpt-3.5-turbo
2025-05-25 01:30:15 - 📤 Request Payload:
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "system", 
      "content": "You are roleplaying as the character described..."
    },
    {
      "role": "user",
      "content": "Hello there!"
    }
  ],
  "stream": true
}
----------------------------------------
```

This gives you exactly what you need to verify the JSON being sent to OpenRouter!
