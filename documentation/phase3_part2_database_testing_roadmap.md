# Phase 3 Part 2 Implementation Roadmap: Database Model Testing

This roadmap provides implementation guidance for testing the SQLAlchemy models implemented in Phase 3 Part 1. It focuses on creating comprehensive unit tests for the database models to ensure they function as expected.

**Status Legend:**
- [ ] Not started
- [🔄] In progress
- [✓] Completed

## Test Framework Setup

### Testing Technology Stack

1. **Primary Testing Framework**
   - [✓] **pytest** (latest stable version)
   - [✓] Configure via `pytest.ini`
   - [✓] Set up test discovery paths

2. **Supporting Libraries**
   - [✓] **pytest-cov** - For code coverage reporting
   - [✓] **SQLAlchemy in-memory SQLite** - For database testing

3. **Test Configuration**
   - [✓] Create test configuration in `conftest.py`
   - [✓] Set up SQLAlchemy test fixtures
   - [✓] Configure in-memory database for tests

### Implementation Steps

1. **Test Project Structure Setup**
   - [✓] Create test directories mirroring application structure
   - [✓] Set up test configuration files
   - [✓] Create common test fixtures and utilities

2. **Common Test Fixtures**
   - [✓] Create SQLAlchemy engine fixture with in-memory SQLite
   - [✓] Create SQLAlchemy session fixture
   - [✓] Create model factory fixtures for test data
   - [✓] Set up transaction management for tests

## Model Test Implementation

Implement tests for each SQLAlchemy model according to the testing strategy outlined in `testing_strategy.md`. Follow the model dependency order to ensure proper testing.

### Implementation Order

1. **Base Model Tests (tests/models/test_base.py)**
   - [✓] Test `Base` class functionality
   - [✓] Test `to_dict()` and `from_dict()` methods
   - [✓] Test `TimestampMixin` functionality

2. **Independent Entity Model Tests**
   - [✓] Character model tests (tests/models/test_character.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test relationship configurations
     - [✓] Test custom model methods

   - [ ] UserProfile model tests (tests/models/test_user_profile.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test relationship configurations
     - [ ] Test custom model methods

   - [ ] AIModel model tests (tests/models/test_ai_model.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test relationship configurations
     - [ ] Test custom model methods

   - [ ] SystemPrompt model tests (tests/models/test_system_prompt.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test relationship configurations
     - [ ] Test custom model methods

3. **Dependent Entity Model Tests**
   - [ ] ChatSession model tests (tests/models/test_chat_session.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test foreign key constraints
     - [ ] Test relationship configurations
     - [ ] Test cascade operations

   - [ ] Message model tests (tests/models/test_message.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test foreign key constraints
     - [ ] Test relationship configurations
     - [ ] Test cascade operations

   - [ ] ApplicationSettings model tests (tests/models/test_application_settings.py)
     - [ ] Test model initialization with valid data
     - [ ] Test column constraints (unique, non-null)
     - [ ] Test foreign key constraints
     - [ ] Test relationship configurations
     - [ ] Test default application settings

## Test Fixtures and Utilities Implementation

Create reusable fixtures and utilities to simplify test implementation:

1. **Database Session Management (conftest.py)**
   - [ ] Create database engine fixture
   - [ ] Create database session fixture
   - [ ] Set up transaction management for tests
   - [ ] Configure model Base and metadata

2. **Test Data Factories**
   - [ ] Create Character factory fixture
   - [ ] Create UserProfile factory fixture
   - [ ] Create AIModel factory fixture
   - [ ] Create SystemPrompt factory fixture
   - [ ] Create ChatSession factory fixture
   - [ ] Create Message factory fixture
   - [ ] Create ApplicationSettings factory fixture

3. **Helper Functions**
   - [ ] Create validation helper functions
   - [ ] Create relationship testing utilities
   - [ ] Create constraint testing utilities

## Test Coverage Goals

Aim to achieve the following test coverage targets as specified in the testing strategy:

- Models: 95-100% coverage
- Overall test coverage: 80%+

## Running and Verifying Tests

Set up commands and workflows for running and verifying tests:

1. **Test Command Configuration**
   - [ ] Configure pytest command in pyproject.toml
   - [ ] Set up coverage reporting
   - [ ] Set up test discovery

2. **CI Integration**
   - [ ] Configure test running in CI workflows
   - [ ] Set up coverage threshold checks
   - [ ] Enforce test passing for merges

## Model Test Examples

### Base Model Test Example

```python
def test_base_to_dict(db_session):
    """Test Base.to_dict() method."""
    character = Character(label="test_char", name="Test Character")
    db_session.add(character)
    db_session.commit()

    dict_data = character.to_dict()

    assert isinstance(dict_data, dict)
    assert dict_data["id"] == character.id
    assert dict_data["label"] == "test_char"
    assert dict_data["name"] == "Test Character"

def test_timestamp_mixin():
    """Test TimestampMixin adds created_at and updated_at."""
    character = Character(label="test_char", name="Test Character")

    assert hasattr(character, "created_at")
    assert hasattr(character, "updated_at")
```

### Character Model Test Example

```python
def test_character_creation():
    """Test Character model initialization."""
    character = Character(label="test_char", name="Test Character",
                          description="Test description")

    assert character.label == "test_char"
    assert character.name == "Test Character"
    assert character.description == "Test description"
    assert character.created_at is None  # Will be set on commit
    assert character.updated_at is None  # Will be set on commit

def test_character_unique_constraint(db_session):
    """Test Character.label unique constraint."""
    character1 = Character(label="unique_char", name="Character 1")
    db_session.add(character1)
    db_session.commit()

    character2 = Character(label="unique_char", name="Character 2")
    db_session.add(character2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
```

## Getting Started Checklist

1. **Environment Setup**
   - [ ] Ensure Poetry is installed and virtual environment is activated
   - [ ] Install test dependencies: `poetry add --group dev pytest pytest-cov`
   - [ ] Configure pytest.ini and coverage settings

2. **Initial Test Implementation**
   - [ ] Create conftest.py with SQLAlchemy fixtures
   - [ ] Implement Base model tests
   - [ ] Run initial tests to verify configuration

3. **Full Test Suite Implementation**
   - [ ] Implement tests for all models
   - [ ] Run full test suite
   - [ ] Verify coverage meets targets

4. **Documentation**
   - [ ] Document test running procedure
   - [ ] Document coverage reporting
   - [ ] Update project README with testing instructions
