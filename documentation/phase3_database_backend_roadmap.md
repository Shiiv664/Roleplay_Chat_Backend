# Phase 3 Implementation Roadmap: Database & Backend Foundation

This roadmap provides implementation guidance for the database and backend foundation of the Roleplay Chat Web App. It follows the technical architecture outlined in `technical_architecture.md` and prioritizes practical implementation steps.

## Database Setup with SQLAlchemy ORM

### Implementation Steps

1. **Create Base SQLAlchemy Configuration**
   - Set up SQLAlchemy engine connection to SQLite
   - Configure Base declarative class
   - Implement session management utilities
   - Add Alembic integration for migrations (confirmed)
   - Write unit tests for database configuration

2. **Implement Database Initialization Script**
   - Create script to initialize database if not exists
   - Set up initial migration
   - Add database version tracking
   - Create script for generating test data (confirmed)
   - Write tests to verify database initialization

3. **Set Up Test Infrastructure**
   - Create test fixtures as defined in testing_strategy.md
   - Set up in-memory SQLite for tests
   - Configure pytest.ini
   - Create test data factory functions

## SQLAlchemy Models Implementation

Follow the structure defined in `technical_architecture.md` under "SQLAlchemy ORM Models" section.

### Implementation Order

Implement models in this dependency order:

1. **Base Model (models/base.py)**
   - Define `Base` class from SQLAlchemy declarative base
   - Set up common model mixin with timestamps if needed
   - Configure metadata

2. **Independent Entity Models**
   - Character model (models/character.py)
   - UserProfile model (models/user_profile.py)
   - AIModel model (models/ai_model.py)
   - SystemPrompt model (models/system_prompt.py)

3. **Dependent Entity Models**
   - ChatSession model (models/chat_session.py) - references characters, profiles, models, prompts
   - Message model (models/message.py) - references chat sessions
   - ApplicationSettings model (models/application_settings.py) - references default entities

### Model Implementation Details

For each model:
- Define table name and columns with appropriate types
- Add constraints (unique, non-null, etc.)
- Implement relationships between models
- Add any model-specific methods
- Set up validation at the SQLAlchemy model level (confirmed approach)
- Create corresponding unit tests following testing_strategy.md, including:
  - Test model initialization
  - Test constraints and validations
  - Test relationship configurations

## Repository Pattern Implementation

Follow the repository pattern details from `technical_architecture.md`.

### Implementation Steps

1. **Create Base Repository**
   - Implement `BaseRepository` class with common CRUD operations
   - Set up session management
   - Add transaction support
   - Implement error handling following error_handling_strategy.md
     - Catch SQLAlchemy exceptions and convert to application exceptions
     - Add appropriate context to exception messages

2. **Entity-Specific Repositories**
   - Character repository
   - UserProfile repository
   - AIModel repository
   - SystemPrompt repository
   - ChatSession repository
   - Message repository
   - ApplicationSettings repository

### Repository Implementation Details

For each repository:
- Extend the `BaseRepository` class
- Implement entity-specific query methods
- Add custom filtering and sorting capabilities
- Implement relationship handling
- Add any complex query logic specific to the entity
- Create corresponding unit tests following testing_strategy.md, including:
  - Test CRUD operations
  - Test query methods
  - Test error handling

## Service Layer Implementation

### Implementation Steps

1. **Create Service Base Structure**
   - Define common service patterns
   - Set up dependency injection for repositories
   - Implement error handling following error_handling_strategy.md
     - Handle business rule validation errors
     - Add contextual information to errors
     - Properly propagate repository exceptions

2. **Core Services**
   - Character service
   - UserProfile service
   - AIModel service
   - SystemPrompt service

3. **Complex Services**
   - ChatService (handling sessions and messages)
   - ApplicationSettingsService
   - AIIntegrationService (for OpenRouter API)

### Service Implementation Details

For each service:
- Implement business logic specific to the entity
- Add validation rules
- Create methods for complex operations across multiple repositories
- Handle any external API interactions
- Ensure proper error handling and transaction management
- Create corresponding unit tests following testing_strategy.md, including:
  - Test business logic with mocked repositories
  - Test validation rules
  - Test error scenarios
  - Test transaction management

## API Endpoints Implementation

Follow the API endpoints defined in `technical_architecture.md`.

### Implementation Steps

1. **API Framework Setup**
   - Configure Flask application structure
   - Set up request parsing and validation
   - Implement response formatting
   - Add error handling middleware following error_handling_strategy.md
     - Implement global exception handlers for each exception type
     - Configure consistent error response format
     - Set up proper HTTP status code mapping

2. **Core API Routes**
   - Character routes
   - UserProfile routes
   - AIModel routes
   - SystemPrompt routes

3. **Session and Message Routes**
   - ChatSession routes
   - Message routes
   - AI generation endpoint

4. **Settings Routes**
   - ApplicationSettings routes

### API Implementation Details

For each route group:
- Implement RESTful endpoints (GET, POST, PUT, DELETE)
- Add request validation
- Connect to appropriate service layer methods
- Format responses consistently
- Document API endpoints with docstrings or comments
- Create corresponding unit tests following testing_strategy.md, including:
  - Test request validation
  - Test response formatting
  - Test status codes
  - Test error handling
  - Test with mocked services

## Error Handling and Logging

Follow the comprehensive approach defined in error_handling_strategy.md.

### Implementation Steps

1. **Custom Exception Hierarchy**
   - Create base `AppError` exception class
   - Implement specific exception types:
     - `DatabaseError` for database operation errors
     - `ValidationError` for data validation errors
     - `ResourceNotFoundError` for not found errors
     - `ExternalAPIError` for OpenRouter API issues
     - `BusinessRuleError` for business rule violations

2. **Layer-Appropriate Error Handling**
   - **Database/ORM Layer**:
     - Allow SQLAlchemy exceptions to bubble up
     - Don't catch exceptions at model level unless necessary
   - **Repository Layer**:
     - Catch SQLAlchemy exceptions and convert to application exceptions
     - Map SQLAlchemy exceptions to appropriate application exceptions
     - Add contextual information to errors
   - **Service Layer**:
     - Handle business rule validation
     - Add contextual information to errors from repositories
     - Log errors with appropriate context
   - **API Layer**:
     - Catch application exceptions and convert to HTTP responses
     - Implement proper status code mapping

3. **Global Error Handling**
   - Set up Flask error handlers for each exception type
   - Configure consistent error response format:
     ```json
     {
       "error": "Human-readable error message",
       "type": "ErrorClassName",
       "details": { /* Optional details */ }
     }
     ```
   - Implement route-specific handling for special cases when needed

4. **Logging Strategy**
   - Configure basic logging setup
   - Define log level usage (ERROR, WARNING, INFO, DEBUG)
   - Implement structured logging approach
   - Log appropriate information at each application layer

## Testing Implementation

Follow the comprehensive approaches defined in testing_strategy.md and error_handling_strategy.md.

### Implementation Steps

1. **Unit Testing**
   - Create tests for models following the patterns in testing_strategy.md
   - Test repositories with mock sessions as outlined in testing_strategy.md
   - Test services with mock repositories
   - Test API routes with mock services

2. **Error Handling Testing**
   - **Test Exception Raising**:
     - Verify repositories raise correct exceptions for database errors
     - Test service layer validation and exception handling
     - Ensure proper exception propagation between layers
   - **Test Global Error Handlers**:
     - Verify error handlers return correct status codes
     - Test error response format consistency
     - Ensure proper mapping of exception types to HTTP status codes
   - **Test Error Logging**:
     - Verify appropriate information is logged for errors
     - Test that sensitive information is not exposed in logs

3. **Test Reporting**
   - Set up test coverage reporting with pytest-cov
   - Establish baseline coverage goals as defined in testing_strategy.md
   - Maintain coverage reports during development

4. **Test Utilities**
   - Create fixtures for test data as specified in testing_strategy.md
   - Implement test helpers
   - Set up test configuration with pytest.ini

## Implementation Checkpoints

Each major component should be tested before moving to the next dependency:

1. First implement and test SQLAlchemy models
2. Then implement and test repositories
3. Next implement and test services
4. Finally implement and test API endpoints

## Development Structure

The implementation can follow this organizational pattern:

```
/models
  base.py
  character.py
  user_profile.py
  ...

/repositories
  base_repository.py
  character_repository.py
  user_profile_repository.py
  ...

/services
  character_service.py
  user_profile_service.py
  ...

/api
  /routes
    character_routes.py
    user_profile_routes.py
    ...
  /middleware
    error_handler.py
    request_validator.py
    ...

/tests
  /models
  /repositories
  /services
  /api
```

This implementation roadmap provides a flexible guide for developing the database and backend foundation of the application, without imposing strict deadlines or formal milestones.