# Testing Strategy

This document outlines the testing approach for the Roleplay Chat Web App. It focuses primarily on unit testing while acknowledging other testing types that could be implemented later if needed.

## Testing Framework and Tools

### Primary Testing Framework

- **pytest** (latest stable version) - Used for all test types due to its simplicity, powerful fixtures, and extensive plugin ecosystem
  - Configure via `pytest.ini`
  - Utilize built-in fixture system with different scopes (function, class, module, session)
  - Use native assert statements for clean, readable assertions

### Supporting Libraries and Plugins

- **pytest-flask** - For testing Flask applications, provides client fixture
- **pytest-mock** - For integration with Python's unittest.mock library
- **pytest-cov** - For code coverage reporting and enforcement
- **pytest-asyncio** - For testing any asynchronous code if needed
- **pytest-xdist** - For parallel test execution as the test suite grows
- **Python unittest.mock** - Standard mocking library for test doubles
- **SQLAlchemy in-memory SQLite** - For database testing without persistence

## Project Test Structure

```
/tests
  /unit                         # Unit tests
    /models                     # SQLAlchemy model tests
    /repositories               # Repository tests
    /services                   # Service layer tests
    /api                        # API endpoint tests
  /integration                  # Optional - for later implementation
    /database                   # Database integration tests
    /api                        # API integration tests
  conftest.py                   # Shared test fixtures and utilities
  pytest.ini                    # pytest configuration
```

## Unit Testing Approach

### 1. Model Tests

Test SQLAlchemy models to ensure they are correctly defined and behave as expected.

**What to Test:**
- Model initialization with valid data
- Column constraints (unique, non-null, etc.)
- Default values
- Relationship configurations
- Custom model methods

**Example Test:**

```python
def test_character_creation():
    character = Character(label="test_char", name="Test Character")
    assert character.label == "test_char"
    assert character.name == "Test Character"
    assert character.created_at is not None

def test_character_unique_constraint(db_session):
    character1 = Character(label="unique_char", name="Character 1")
    character2 = Character(label="unique_char", name="Character 2")

    db_session.add(character1)
    db_session.commit()

    db_session.add(character2)
    with pytest.raises(IntegrityError):
        db_session.commit()
```

### 2. Repository Tests

Test repository implementations to ensure they correctly interact with the database.

**What to Test:**
- CRUD operations (Create, Read, Update, Delete)
- Query methods
- Error handling
- Transaction management

**Example Test:**

```python
def test_character_repository_create(db_session):
    repo = CharacterRepository(db_session)
    character = repo.create(label="test_char", name="Test Character")

    assert character.id is not None
    assert character.label == "test_char"

    # Verify it was saved to the database
    db_character = db_session.query(Character).filter_by(id=character.id).first()
    assert db_character is not None

def test_character_repository_get_by_id(db_session):
    # Create a character
    character = Character(label="test_char", name="Test Character")
    db_session.add(character)
    db_session.commit()

    repo = CharacterRepository(db_session)
    result = repo.get_by_id(character.id)

    assert result is not None
    assert result.id == character.id
    assert result.label == "test_char"
```

### 3. Service Tests

Test service layer implementations to ensure business logic is correctly implemented.

**What to Test:**
- Business logic
- Validation rules
- Cross-repository operations
- Error handling and exceptions

**Testing Approach:**
- Mock repositories to isolate service tests
- Test success and failure scenarios
- Verify correct repository methods are called

**Example Test:**

```python
def test_character_service_create(mocker):
    # Mock the repository
    mock_repo = mocker.MagicMock()
    mock_repo.create.return_value = Character(id=1, label="test_char", name="Test Character")

    # Create service with mocked repository
    service = CharacterService(mock_repo)

    # Test service method
    character = service.create_character("test_char", "Test Character")

    # Verify results
    assert character.id == 1
    assert character.label == "test_char"

    # Verify repository was called correctly
    mock_repo.create.assert_called_once_with(label="test_char", name="Test Character")

def test_character_service_validation(mocker):
    # Mock the repository
    mock_repo = mocker.MagicMock()

    # Create service with mocked repository
    service = CharacterService(mock_repo)

    # Test validation failure
    with pytest.raises(ValueError):
        service.create_character("", "")  # Empty values should fail validation

    # Verify repository was not called
    mock_repo.create.assert_not_called()
```

### 4. API Endpoint Tests

Test API endpoints to ensure they correctly handle requests and responses.

**What to Test:**
- Request validation
- Response formatting
- HTTP status codes
- Error handling

**Testing Approach:**
- Use Flask test client
- Mock service layer to isolate API tests
- Test different HTTP methods
- Test various input scenarios

**Example Test:**

```python
def test_create_character_endpoint(client, mocker):
    # Mock the service
    mock_service = mocker.patch('app.services.character_service.CharacterService')
    mock_service.return_value.create_character.return_value = Character(
        id=1, label="test_char", name="Test Character"
    )

    # Test API call
    response = client.post(
        '/api/characters',
        json={'label': 'test_char', 'name': 'Test Character'}
    )

    # Verify response
    assert response.status_code == 201
    assert response.json['id'] == 1
    assert response.json['label'] == "test_char"

    # Verify service was called
    mock_service.return_value.create_character.assert_called_once_with(
        "test_char", "Test Character"
    )

def test_create_character_endpoint_validation(client, mocker):
    # Mock the service
    mock_service = mocker.patch('app.services.character_service.CharacterService')

    # Test invalid input
    response = client.post(
        '/api/characters',
        json={'label': '', 'name': ''}  # Invalid data
    )

    # Verify validation failure response
    assert response.status_code == 400

    # Verify service was not called
    mock_service.return_value.create_character.assert_not_called()
```

## Test Fixtures

Use pytest fixtures to set up test environment and dependencies.

### Common Fixtures

```python
# In conftest.py

@pytest.fixture
def app():
    """Create and configure Flask app for testing."""
    app = create_app(config={'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def db_engine():
    """Create a SQLAlchemy engine connected to an in-memory SQLite database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create a SQLAlchemy session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

# Factory fixtures for creating test data
@pytest.fixture
def create_test_character():
    def _create_character(label="test_char", name="Test Character", description=None):
        return Character(
            label=label,
            name=name,
            description=description
        )
    return _create_character
```

## Test Data

Create factory functions to generate test data consistently:

```python
def create_test_character_data():
    return {
        "label": "test_character",
        "name": "Test Character",
        "description": "A character for testing",
        "avatar_image": "test.png"
    }

def create_test_user_profile_data():
    return {
        "label": "test_profile",
        "name": "Test User",
        "description": "A profile for testing",
        "avatar_image": "user.png"
    }
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/models/test_character.py

# Run specific test function
pytest tests/unit/models/test_character.py::test_character_creation

# Generate coverage report
pytest --cov=app
```

## Test Naming Conventions

Follow these naming conventions for consistency:

- Test files: `test_[module_name].py`
- Test functions: `test_[function_name]_[scenario]`
- Test classes: `Test[ClassName]`
- Test methods: `test_[method_name]_[scenario]`

## Future Testing Considerations

While the current focus is on unit testing, these testing types could be added later if needed:

### Integration Tests

Testing how components work together with real dependencies.

- Database integration tests
- Service-repository integration tests
- API-service integration tests

### Functional Tests

Testing complete features and workflows.

- End-to-end testing of features
- Multi-step workflows

### UI Tests

Testing frontend components.

- Page rendering tests
- User interaction tests
- Form submission tests

### Performance Tests

Testing system performance under various conditions.

- Database query performance
- API response times
- Load testing (probably not necessary for a local application)

## Test Coverage Goals

Initial test coverage goals:

- Models: 95-100% coverage
- Repositories: 90-100% coverage
- Services: 80-90% coverage
- API endpoints: 80-90% coverage

Overall project test coverage goal: 80%+
