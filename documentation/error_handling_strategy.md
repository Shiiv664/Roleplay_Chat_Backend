# Error Handling Strategy

This document outlines the error handling approach for the Roleplay Chat Web App. It provides guidance on exception handling, logging, and error response practices across different layers of the application.

## Core Principles

1. **Clarity**: Error messages should be clear and actionable
2. **Consistency**: Error handling should be consistent across the application
3. **Layer-Appropriate**: Each layer should handle errors appropriate to its context
4. **Informative**: Errors should provide useful information for debugging without exposing sensitive details
5. **User-Friendly**: API responses should give users meaningful information about errors

## Exception Hierarchy

The application will use a custom exception hierarchy to represent different error types:

```python
# Base exception for the application
class AppError(Exception):
    """Base exception for all application errors"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# Database-related errors
class DatabaseError(AppError):
    """Database operation errors"""
    pass

# Data validation errors
class ValidationError(AppError):
    """Data validation errors"""
    pass

# Resource not found errors
class ResourceNotFoundError(AppError):
    """Resource not found errors"""
    pass

# External API errors (for OpenRouter integration)
class ExternalAPIError(AppError):
    """External API interaction errors"""
    pass

# Business rule violation errors
class BusinessRuleError(AppError):
    """Business rule violation errors"""
    pass
```

## Error Handling by Layer

### 1. Database/ORM Layer

SQLAlchemy provides its own exception types. These should be caught and converted to application-specific exceptions at the repository layer.

#### Approach:

- Use SQLAlchemy's constraints and validations
- Let SQLAlchemy exceptions bubble up to the repository layer
- Don't catch exceptions at the model level unless absolutely necessary

### 2. Repository Layer

The repository layer should catch database-specific exceptions and convert them to application-specific exceptions.

#### Approach:

```python
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound

def get_by_id(self, entity_id):
    try:
        result = self.session.query(Entity).filter_by(id=entity_id).first()
        if not result:
            raise ResourceNotFoundError(f"Entity with ID {entity_id} not found")
        return result
    except SQLAlchemyError as e:
        self.logger.error("Database error", entity_id=entity_id, error=str(e))
        raise DatabaseError(f"Error retrieving entity: {str(e)}")
```

#### Exception Mapping:

| SQLAlchemy Exception | Application Exception | HTTP Status |
|----------------------|-----------------------|-------------|
| `NoResultFound`      | `ResourceNotFoundError` | 404       |
| `IntegrityError`     | `ValidationError`       | 400       |
| Other `SQLAlchemyError` | `DatabaseError`     | 500       |

### 3. Service Layer

The service layer should handle business logic validation and manage exceptions from repositories.

#### Approach:

```python
def create_entity(self, data):
    # Validate business rules
    if not self._is_valid_entity(data):
        raise ValidationError("Invalid entity data", details={"invalid_fields": self._get_invalid_fields(data)})

    try:
        # Create entity in repository
        return self.repository.create(**data)
    except DatabaseError as e:
        # Log the error with context
        self.logger.error("Failed to create entity", data=data, error=str(e))
        # Re-raise the exception
        raise
```

#### Key Responsibilities:

- Perform business rule validation before data reaches the repository
- Add contextual information to errors
- Log errors with appropriate context
- Handle or propagate exceptions as appropriate

### 4. API Layer

The API layer should catch application exceptions and convert them to appropriate HTTP responses.

#### Approach:

Use Flask's error handler to manage application-specific exceptions:

```python
@app.errorhandler(AppError)
def handle_app_error(error):
    response = {
        "error": error.message,
        "type": error.__class__.__name__
    }

    # Add details if available and not sensitive
    if hasattr(error, 'details') and error.details:
        response["details"] = error.details

    # Map exception types to status codes
    if isinstance(error, ResourceNotFoundError):
        status_code = 404
    elif isinstance(error, ValidationError):
        status_code = 400
    elif isinstance(error, BusinessRuleError):
        status_code = 422
    elif isinstance(error, ExternalAPIError):
        status_code = 502
    else:
        status_code = 500

    return jsonify(response), status_code
```

#### HTTP Status Code Mapping:

| Exception Type | HTTP Status Code | Description |
|----------------|------------------|-------------|
| `ValidationError` | 400 (Bad Request) | Invalid input data |
| `ResourceNotFoundError` | 404 (Not Found) | Resource not found |
| `BusinessRuleError` | 422 (Unprocessable Entity) | Valid data but violates business rules |
| `ExternalAPIError` | 502 (Bad Gateway) | Issues with external API (OpenRouter) |
| `DatabaseError` | 500 (Internal Server Error) | Database errors |
| Other `AppError` | 500 (Internal Server Error) | Generic application errors |

## Logging Strategy

The application will use a simple, straightforward logging approach that focuses on essential information:

### Logging Configuration

```python
import logging

# Configure logging once at application startup
def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Use standard logger in modules
logger = logging.getLogger(__name__)
```

### Log Levels

- **ERROR**: Use for exceptions and error conditions
- **WARNING**: Use for concerning but non-exception scenarios
- **INFO**: Use for significant application events
- **DEBUG**: Use for detailed debugging information

### What to Log

1. **Repository Layer**:
   - Database errors with the affected entity ID
   - Basic error message for failed operations

2. **Service Layer**:
   - Basic information about business rule violations
   - External API interaction issues
   - Simple validation failure messages

3. **API Layer**:
   - Basic request path information for failed requests
   - Endpoint and HTTP method information

### Log Format

```
2024-05-18 15:30:45 - app.repositories.character - ERROR - Failed to get character with ID 123: IntegrityError
```

### Logging Examples

```python
# Repository layer
logger.error(f"Failed to get character with ID {character_id}: {str(e)}")

# Service layer
logger.error(f"Failed to create character '{name}': {str(e)}")

# API layer
logger.error(f"Error in POST /api/characters: {str(e)}")
```

### Future Enhancement Path

This simple logging approach can be enhanced later to include more structured context if needed. The transition would require minimal refactoring:

1. Create a wrapper class:
   ```python
   class StructuredLogger:
       def __init__(self, name):
           self.logger = logging.getLogger(name)

       def error(self, message, **kwargs):
           context = json.dumps(kwargs) if kwargs else ""
           self.logger.error(f"{message} {context}")
   ```

2. Update log calls with structured context:
   ```python
   # Before
   logger.error(f"Failed to get character with ID {character_id}: {str(e)}")

   # After
   logger.error("Failed to get character", character_id=character_id, error=str(e))
   ```

## Error Response Format

API error responses will follow a consistent JSON format:

```json
{
  "error": "Human-readable error message",
  "type": "ErrorClassName",
  "details": {
    "field1": "Error details for field1",
    "field2": "Error details for field2"
  }
}
```

Notes:
- The `details` field is optional and only included when additional information is available
- Sensitive information should never be included in error responses
- Stack traces should only be logged, never included in API responses

## Implementation Example

### Model Definition

```python
class Character(Base):
    __tablename__ = 'character'

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    avatar_image = Column(String)
    description = Column(Text)

    # No exception handling at model level
```

### Repository Implementation

```python
class CharacterRepository(BaseRepository):
    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, character_id):
        try:
            character = self.session.query(Character).filter(Character.id == character_id).first()
            if not character:
                raise ResourceNotFoundError(f"Character with ID {character_id} not found")
            return character
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get character with ID {character_id}: {str(e)}")
            raise DatabaseError(f"Error retrieving character: {str(e)}")

    def create(self, label, name, avatar_image=None, description=None):
        try:
            character = Character(
                label=label,
                name=name,
                avatar_image=avatar_image,
                description=description
            )
            self.session.add(character)
            self.session.commit()
            return character
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ValidationError(f"Character with label '{label}' already exists")
            self.logger.error(f"Integrity error creating character '{label}': {str(e)}")
            raise ValidationError(f"Invalid character data: {str(e)}")
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error creating character '{label}': {str(e)}")
            raise DatabaseError(f"Error creating character: {str(e)}")
```

### Service Implementation

```python
class CharacterService:
    def __init__(self, repository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    def create_character(self, label, name, avatar_image=None, description=None):
        # Validate data
        if not label or not name:
            raise ValidationError("Character label and name are required")

        if len(label) < 3:
            raise ValidationError("Character label must be at least 3 characters")

        try:
            return self.repository.create(label, name, avatar_image, description)
        except (ValidationError, DatabaseError) as e:
            # Log error, then re-raise
            self.logger.error(f"Failed to create character '{name}': {str(e)}")
            raise
```

### API Route Implementation with Global Error Handling

With global error handlers in place, route implementations become much simpler, focusing on the "happy path":

```python
@app.route('/api/characters', methods=['POST'])
def create_character():
    data = request.json

    # Basic request validation
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract data
    label = data.get('label')
    name = data.get('name')
    avatar_image = data.get('avatar_image')
    description = data.get('description')

    # Call service - any exceptions will be caught by global handlers
    character = character_service.create_character(label, name, avatar_image, description)

    # Return response
    return jsonify({
        "id": character.id,
        "label": character.label,
        "name": character.name,
        "avatar_image": character.avatar_image,
        "description": character.description
    }), 201
```

Notice the absence of try/except blocks. This approach:
- Makes routes cleaner and more focused
- Ensures consistent error handling across all endpoints
- Centralizes error handling logic
- Reduces code duplication

## Comprehensive Global Error Handling

For Flask applications, implement specialized error handlers for each exception type:

```python
# Register specific handlers for each exception type
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    app.logger.warning(f"Validation error: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": "ValidationError"
    }), 400

@app.errorhandler(ResourceNotFoundError)
def handle_not_found_error(error):
    app.logger.info(f"Resource not found: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": "ResourceNotFoundError"
    }), 404

@app.errorhandler(BusinessRuleError)
def handle_business_rule_error(error):
    app.logger.warning(f"Business rule violation: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": "BusinessRuleError"
    }), 422

@app.errorhandler(ExternalAPIError)
def handle_external_api_error(error):
    app.logger.error(f"External API error: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": "ExternalAPIError"
    }), 502

@app.errorhandler(DatabaseError)
def handle_database_error(error):
    app.logger.error(f"Database error: {str(error)}")
    return jsonify({
        "error": "A database error occurred",
        "type": "DatabaseError"
    }), 500

# Generic handler for any other AppError
@app.errorhandler(AppError)
def handle_app_error(error):
    app.logger.error(f"Application error: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": error.__class__.__name__
    }), 500

# Handle uncaught exceptions
@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.error(f"Unexpected error: {str(error)}")
    return jsonify({
        "error": "An unexpected error occurred",
        "type": "UnexpectedError"
    }), 500
```

### Benefits of Specialized Global Handlers

1. **Type-Specific Handling**: Each error type gets its own specialized handler
2. **Appropriate Logging**: Different error types can be logged at different levels
3. **Clean Routes**: Route handlers focus only on the happy path
4. **Consistent Responses**: Error responses are formatted consistently across the application
5. **DRY Code**: Error handling logic is defined once and used everywhere

### Adding Route-Specific Handling When Needed

For special cases where route-specific handling is required, you can still use try/except blocks in specific routes:

```python
@app.route('/api/special-case', methods=['POST'])
def special_case():
    try:
        # Special case processing
        result = special_service.process(request.json)
        return jsonify(result), 200
    except ValidationError as e:
        # Custom validation handling for this specific endpoint
        return jsonify({
            "error": str(e),
            "custom_field": "additional info",
            "validation_failed": True
        }), 400
```

The global handlers will still catch any exceptions not explicitly handled in the route.

## Testing Error Handling

Unit tests should verify both exception raising and global error handling:

### Testing Exception Raising

Test that repositories and services raise the correct exceptions:

```python
def test_character_repository_not_found():
    # Setup
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    repo = CharacterRepository(session)

    # Test
    with pytest.raises(ResourceNotFoundError):
        repo.get_by_id(999)

def test_character_service_validation():
    # Setup
    repo = MagicMock()
    service = CharacterService(repo)

    # Test
    with pytest.raises(ValidationError):
        service.create_character("", "")  # Empty values should fail validation

    # Verify repository was not called
    repo.create.assert_not_called()
```

### Testing Global Error Handlers

Test that global error handlers return the correct responses:

```python
def test_validation_error_handler(client):
    # Setup
    @app.route('/test_validation_error')
    def raise_validation_error():
        raise ValidationError("Test validation error")

    # Test
    response = client.get('/test_validation_error')

    # Assert
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Test validation error"
    assert data['type'] == "ValidationError"

def test_not_found_error_handler(client):
    # Setup
    @app.route('/test_not_found_error')
    def raise_not_found_error():
        raise ResourceNotFoundError("Resource not found")

    # Test
    response = client.get('/test_not_found_error')

    # Assert
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Resource not found"
    assert data['type'] == "ResourceNotFoundError"
```

This approach ensures that both your domain code and the error handling infrastructure work correctly.

## Conclusion

This error handling strategy provides a consistent approach to managing errors throughout the application, emphasizing global error handlers for simplicity and consistency. By following these guidelines, the application will:

1. Present clear and consistent error messages to users
2. Provide useful information for debugging without verbose logging
3. Keep route handlers clean and focused on the happy path
4. Maintain a clear separation of concerns between layers
5. Handle errors at the appropriate level of abstraction
6. Minimize code duplication through centralized error handling

The implementation focuses on simplicity while maintaining flexibility:
- Global error handlers provide consistency across the application
- Simple logging focuses on essential information
- Route-specific error handling is available when needed for special cases

This approach delivers a good balance between simplicity and robustness for a solo development project, with a clear path to enhance error handling if requirements change in the future.
