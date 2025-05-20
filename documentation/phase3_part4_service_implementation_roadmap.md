# Phase 3 Part 4 Implementation Roadmap: Service Layer

This roadmap outlines the implementation of the service layer for the Roleplay Chat Web App. It builds on the repository layer implemented in Part 3 and establishes the business logic layer that will serve as the foundation for the API.

**Status Legend:**
- [ ] Not started
- [🔄] In progress
- [✓] Completed

## Service Layer Overview

The service layer acts as the application's business logic layer, orchestrating operations across repositories and implementing domain-specific functionality. This layer:

1. Enforces business rules and validation
2. Coordinates operations across multiple repositories
3. Transforms data between persistence and domain formats
4. Handles system-wide concerns like transactions and error management
5. Provides a clean API for the presentation layer

## Core Principles for Service Implementation

1. **Single Responsibility**: Each service focuses on a specific domain area
2. **Repository Dependency**: Services depend on repositories, not directly on the database
3. **Business Logic Centralization**: All business rules reside in the service layer
4. **Error Handling**: Follow the patterns defined in `error_handling_strategy.md`
5. **Testability**: Design services to be easily unit tested with mocked repositories

## General Service Structure

Each service should follow this general structure:

1. Accept repository dependencies through constructor injection
2. Implement domain-specific operations as public methods
3. Apply validation logic before calling repositories
4. Handle errors according to the application's error handling strategy
5. Include appropriate logging at key points

## Service Implementations

### 1. Character Service

**Responsibilities:**
- Manage character entities
- Enforce character-specific business rules
- Support search and filtering operations

**Implementation Tasks:**
- [ ] Create `character_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add search functionality
- [ ] Implement character-specific business logic
- [ ] Write tests with mocked repository

### 2. User Profile Service

**Responsibilities:**
- Manage user profile entities
- Handle default profile logic

**Implementation Tasks:**
- [ ] Create `user_profile_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add default profile management
- [ ] Write tests with mocked repository

### 3. AI Model Service

**Responsibilities:**
- Manage AI model entities
- Filter active/inactive models

**Implementation Tasks:**
- [ ] Create `ai_model_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add active model filtering
- [ ] Write tests with mocked repository

### 4. System Prompt Service

**Responsibilities:**
- Manage system prompt entities
- Support default prompt functionality

**Implementation Tasks:**
- [ ] Create `system_prompt_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add default prompt management
- [ ] Write tests with mocked repository

### 5. Chat Session Service

**Responsibilities:**
- Manage chat session entities
- Handle relationships with characters, user profiles, AI models, and system prompts
- Support session filtering and retrieval operations

**Implementation Tasks:**
- [ ] Create `chat_session_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add session filtering (by character, user profile, etc.)
- [ ] Implement session metadata management
- [ ] Write tests with mocked repositories

### 6. Message Service

**Responsibilities:**
- Manage message entities
- Support pagination and filtering
- Handle bulk message operations

**Implementation Tasks:**
- [ ] Create `message_service.py`
- [ ] Implement CRUD operations with validation
- [ ] Add message retrieval with pagination
- [ ] Implement chat history management
- [ ] Write tests with mocked repository

### 7. Application Settings Service

**Responsibilities:**
- Manage singleton application settings
- Handle default entity references

**Implementation Tasks:**
- [ ] Create `application_settings_service.py`
- [ ] Implement settings retrieval and update
- [ ] Add default entity reference management
- [ ] Write tests with mocked repository

### 8. AI Integration Service (Advanced)

**Responsibilities:**
- Integrate with external AI services (OpenRouter API)
- Format prompts and parse responses
- Handle AI-specific errors

**Implementation Tasks:**
- [ ] Create `ai_integration_service.py`
- [ ] Implement API client for OpenRouter
- [ ] Add prompt formatting and context management
- [ ] Implement response handling and parsing
- [ ] Add error handling for API issues
- [ ] Write tests with mocked HTTP client

## Testing Guidelines

Refer to `testing_strategy.md` for detailed testing guidance. For service layer tests:

1. **Mock Dependencies**
   - Use pytest's mocking capabilities to isolate service tests
   - Mock repository behavior for both success and error scenarios

2. **Test Business Rules**
   - Verify that business rules are correctly enforced
   - Test validation logic thoroughly
   - Check error cases and exception handling

3. **Coverage Goals**
   - Aim for 80-90% test coverage for service classes
   - Focus on testing business logic and edge cases

Example test structure:

```python
def test_service_success_case(mocker):
    # Arrange: Mock repository and set up test data
    mock_repo = mocker.MagicMock()
    mock_repo.get_by_id.return_value = expected_entity
    service = EntityService(mock_repo)

    # Act: Call service method
    result = service.get_entity(1)

    # Assert: Verify results and repository calls
    assert result == expected_entity
    mock_repo.get_by_id.assert_called_once_with(1)

def test_service_validation_failure(mocker):
    # Arrange: Mock repository
    mock_repo = mocker.MagicMock()
    service = EntityService(mock_repo)

    # Act & Assert: Verify validation error is raised
    with pytest.raises(ValidationError):
        service.create_entity(invalid_data)

    # Verify repository was not called
    mock_repo.create.assert_not_called()
```

## Error Handling

Follow the principles defined in `error_handling_strategy.md`:

1. **Validation**
   - Validate all input data before calling repositories
   - Raise `ValidationError` for invalid inputs
   - Include details about validation failures

2. **Business Rules**
   - Enforce business rules at the service layer
   - Raise `BusinessRuleError` for business rule violations

3. **Repository Errors**
   - Handle repository errors appropriately
   - Add context to errors when propagating them

4. **External API Errors**
   - For the AI Integration Service, handle external API errors
   - Raise `ExternalAPIError` for OpenRouter API issues

## Implementation Checklist

1. **Core Services**
   - [ ] Character Service
   - [ ] User Profile Service
   - [ ] AI Model Service
   - [ ] System Prompt Service

2. **Session and Message Services**
   - [ ] Chat Session Service
   - [ ] Message Service

3. **Settings and Integration**
   - [ ] Application Settings Service
   - [ ] AI Integration Service

4. **Testing**
   - [ ] Unit tests for all services
   - [ ] Mock repositories in tests
   - [ ] Test success and error scenarios
   - [ ] Verify business rule enforcement

## Implementation Order

For smooth implementation and dependency management, follow this order:

1. Basic entity services (Character, UserProfile, AIModel, SystemPrompt)
2. Chat Session and Message services
3. Application Settings Service
4. AI Integration Service

## Reference Documentation

- **Error Handling**: Refer to `error_handling_strategy.md` for exception handling guidance
- **Testing**: See `testing_strategy.md` for detailed testing approach
- **Repository Pattern**: Review `phase3_part3_repository_implementation_roadmap.md` for repository interfaces

This implementation roadmap provides a guide for implementing the service layer of the Roleplay Chat Web App without imposing strict deadlines or formal milestones.
