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

   - [✓] UserProfile model tests (tests/models/test_user_profile.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test relationship configurations
     - [✓] Test custom model methods

   - [✓] AIModel model tests (tests/models/test_ai_model.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test relationship configurations
     - [✓] Test custom model methods

   - [✓] SystemPrompt model tests (tests/models/test_system_prompt.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test relationship configurations
     - [✓] Test custom model methods

3. **Dependent Entity Model Tests**
   - [✓] ChatSession model tests (tests/models/test_chat_session.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test foreign key constraints
     - [✓] Test relationship configurations
     - [✓] Test cascade operations

   - [✓] Message model tests (tests/models/test_message.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test foreign key constraints
     - [✓] Test relationship configurations
     - [✓] Test cascade operations

   - [✓] ApplicationSettings model tests (tests/models/test_application_settings.py)
     - [✓] Test model initialization with valid data
     - [✓] Test column constraints (unique, non-null)
     - [✓] Test foreign key constraints
     - [✓] Test relationship configurations
     - [✓] Test default application settings

## Test Fixtures and Utilities Implementation

Create reusable fixtures and utilities to simplify test implementation:

1. **Database Session Management (conftest.py)**
   - [✓] Create database engine fixture
   - [✓] Create database session fixture
   - [✓] Set up transaction management for tests
   - [✓] Configure model Base and metadata

2. **Test Data Factories**
   - [✓] Create Character factory fixture
   - [✓] Create UserProfile factory fixture
   - [✓] Create AIModel factory fixture
   - [✓] Create SystemPrompt factory fixture
   - [✓] Create ChatSession factory fixture
   - [✓] Create Message factory fixture
   - [✓] Create ApplicationSettings factory fixture

3. **Helper Functions and Test Refactoring**

   Create helper functions to reduce code duplication and improve test maintainability:

   - [✓] **Helper Module Structure**
     - [✓] Create modular package structure in `tests/models/helpers/`
     - [✓] Set up proper imports and exports in `__init__.py`
     - [✓] Organize helpers by functionality (base, column, relationship, fixture)

   - [✓] **Basic Model Test Helpers** (tests/models/helpers/base_helpers.py)
     - [✓] Create `test_model_inheritance(model_class, parent_class)` helper
     - [✓] Create `test_model_tablename(model_class, expected_tablename)` helper
     - [✓] Create `test_model_repr(model_instance, expected_attributes)` helper
     - [✓] Create `test_model_columns_existence(model_class, column_names)` helper
     - [✓] Create `test_model_to_dict(model_instance, expected_values)` helper

   - [✓] **Column Validation Helpers** (tests/models/helpers/column_helpers.py)
     - [✓] Create `check_column_constraints(model_class, column_name, nullable, unique, primary_key, etc.)` helper
     - [✓] Create `test_required_fields(db_session, model_class, required_fields)` helper
     - [✓] Create `test_unique_constraint(db_session, model_class, unique_field, value1, value2)` helper
     - [✓] Create `test_enum_field(db_session, model_class, field_name, enum_class)` helper

   - [✓] **Relationship Testing Helpers** (tests/models/helpers/relationship_helpers.py)
     - [✓] Create `test_relationship(parent_obj, child_obj, parent_attr, child_attr, is_collection, bidirectional)` helper
     - [✓] Create `test_foreign_key_constraint(db_session, model_factory, fk_field, invalid_id)` helper
     - [✓] Create `test_cascade_delete(db_session, parent_obj, child_obj, parent_attr, child_attr, child_class)` helper
     - [✓] Create `test_many_to_many_relationship(db_session, model1, model2, rel_attr1, rel_attr2)` helper

   - [✓] **Fixture Helpers** (tests/models/helpers/fixture_helpers.py)
     - [✓] Create `create_unique_label(prefix)` utility
     - [✓] Create `force_update_timestamp(db_session, model_instance, field_name, hours_offset)` utility
     - [✓] Create `create_model_with_unique_constraint(model_class, db_session, unique_field, **kwargs)` utility
     - [✓] Create `create_related_models(db_session, parent_factory, child_factory, parent_attr, child_attr)` utility

   - [🔄] **Model Test Refactoring - Independent Entities**
     - [✓] Refactor Character model tests to use helper functions
     - [✓] Refactor Base model tests to use helper functions
     - [ ] Refactor UserProfile model tests to use helper functions
     - [ ] Refactor AIModel model tests to use helper functions
     - [ ] Refactor SystemPrompt model tests to use helper functions

   - [ ] **Model Test Refactoring - Dependent Entities**
     - [ ] Refactor ChatSession model tests to use helper functions
     - [ ] Refactor Message model tests to use helper functions
     - [ ] Refactor ApplicationSettings model tests to use helper functions

   - [ ] **Add Common Test Fixtures**
     - [ ] Create fixtures for common test patterns
     - [ ] Create parameterized tests for similar models
     - [ ] Create reusable test cases that work across model types

## Test Coverage Goals

Aim to achieve the following test coverage targets as specified in the testing strategy:

- Models: 95-100% coverage
- Overall test coverage: 80%+

## Running and Verifying Tests

Set up commands and workflows for running and verifying tests:

1. **Test Command Configuration**
   - [✓] Configure pytest command in pyproject.toml
   - [✓] Set up coverage reporting
   - [✓] Set up test discovery

2. **CI Integration**
   - [ ] Configure test running in CI workflows
   - [ ] Set up coverage threshold checks
   - [ ] Enforce test passing for merges

## Helper Function Examples

### Basic Model Test Helpers

```python
# tests/models/helpers.py

def test_model_inheritance(model_class, parent_class):
    """Test that a model inherits from the correct parent class.

    Args:
        model_class: The model class to test
        parent_class: The expected parent class
    """
    assert issubclass(model_class, parent_class)


def test_model_tablename(model_class, expected_tablename):
    """Test that a model has the correct table name.

    Args:
        model_class: The model class to test
        expected_tablename: The expected table name
    """
    assert model_class.__tablename__ == expected_tablename


def test_model_repr(model_instance, expected_attributes):
    """Test the string representation of a model instance.

    Args:
        model_instance: The model instance to test
        expected_attributes: Dictionary of attribute names and values expected in __repr__
    """
    repr_string = repr(model_instance)
    model_name = model_instance.__class__.__name__
    assert model_name in repr_string

    for attr_name, attr_value in expected_attributes.items():
        expected_text = f"{attr_name}={attr_value}"
        assert expected_text in repr_string
```

### Column Validation Helpers

```python
def check_column_constraints(model_class, column_name, nullable=True, unique=False,
                            primary_key=False, column_type=None, default=None):
    """Check constraints on a model column.

    Args:
        model_class: The model class to check
        column_name: The name of the column to check
        nullable: Whether the column should allow NULL values
        unique: Whether the column should have a unique constraint
        primary_key: Whether the column is a primary key
        column_type: Expected SQLAlchemy column type
        default: Expected default value for the column
    """
    assert hasattr(model_class, column_name), f"{model_class.__name__} has no column {column_name}"
    column = getattr(model_class, column_name).property.columns[0]

    assert column.nullable == nullable, f"Expected nullable={nullable}, got {column.nullable}"
    assert column.unique == unique, f"Expected unique={unique}, got {column.unique}"
    assert column.primary_key == primary_key, f"Expected primary_key={primary_key}, got {column.primary_key}"

    if column_type:
        assert isinstance(column.type, column_type), f"Expected {column_type}, got {type(column.type)}"

    if default is not None:
        assert column.default.arg == default, f"Expected default={default}, got {column.default.arg}"


def test_required_fields(db_session, model_class, create_valid_data, required_fields):
    """Test that required fields cannot be NULL.

    Args:
        db_session: SQLAlchemy session
        model_class: The model class to test
        create_valid_data: Function that returns a dict of valid data for model creation
        required_fields: List of field names that should be required
    """
    # For each required field, test that it cannot be NULL
    for field in required_fields:
        valid_data = create_valid_data()
        valid_data.pop(field)  # Remove the required field

        # Create model instance without the required field
        instance = model_class(**valid_data)
        db_session.add(instance)

        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
```

### Relationship Testing Helpers

```python
def test_relationship(db_session, parent_obj, child_obj, parent_attr, child_attr,
                     is_collection=True, bidirectional=True):
    """Test a relationship between two model instances.

    Args:
        db_session: SQLAlchemy session
        parent_obj: Parent model instance
        child_obj: Child model instance
        parent_attr: Attribute name on parent that relates to child
        child_attr: Attribute name on child that relates to parent
        is_collection: Whether the parent-to-child relationship is a collection
        bidirectional: Whether the relationship is bidirectional
    """
    # Add both objects to session and flush to generate IDs
    db_session.add_all([parent_obj, child_obj])
    db_session.flush()

    # Set up the relationship from child to parent
    setattr(child_obj, child_attr, parent_obj)
    db_session.flush()

    # Test parent to child relationship
    parent_rel = getattr(parent_obj, parent_attr)
    if is_collection:
        assert child_obj in parent_rel
    else:
        assert parent_rel == child_obj

    # Test child to parent relationship if bidirectional
    if bidirectional:
        child_rel = getattr(child_obj, child_attr)
        assert child_rel == parent_obj


def test_cascade_delete(db_session, parent_obj, child_obj, parent_attr, child_attr):
    """Test that deleting a parent cascades to its children.

    Args:
        db_session: SQLAlchemy session
        parent_obj: Parent model instance
        child_obj: Child model instance
        parent_attr: Attribute name on parent that relates to child
        child_attr: Attribute name on child that relates to parent
    """
    # Set up relationship
    setattr(child_obj, child_attr, parent_obj)
    db_session.add_all([parent_obj, child_obj])
    db_session.commit()

    # Store child ID for verification
    child_id = child_obj.id
    child_class = child_obj.__class__

    # Delete parent
    db_session.delete(parent_obj)
    db_session.commit()

    # Verify child was deleted
    deleted_child = db_session.query(child_class).filter_by(id=child_id).first()
    assert deleted_child is None
```

## Refactored Test Examples

### Using Basic Model Test Helpers

```python
# Original test function
def test_character_inheritance():
    """Test Character model inherits from correct base class."""
    assert issubclass(Character, Base)

# Refactored using helper
def test_character_inheritance():
    """Test Character model inherits from correct base class."""
    test_model_inheritance(Character, Base)


# Original test function
def test_character_tablename():
    """Test Character model has the correct table name."""
    assert Character.__tablename__ == "character"

# Refactored using helper
def test_character_tablename():
    """Test Character model has the correct table name."""
    test_model_tablename(Character, "character")
```

### Using Column Validation Helpers

```python
# Original test
def test_character_columns():
    """Test Character model has the expected columns."""
    assert hasattr(Character, "id")
    assert hasattr(Character, "label")
    assert hasattr(Character, "name")
    assert hasattr(Character, "description")
    assert hasattr(Character, "avatar_image")

# Refactored using helpers
def test_character_columns():
    """Test Character model has the expected columns."""
    # Check primary key
    check_column_constraints(Character, "id", nullable=False, primary_key=True,
                            column_type=Integer)

    # Check required fields
    check_column_constraints(Character, "label", nullable=False, unique=True,
                            column_type=String)
    check_column_constraints(Character, "name", nullable=False, column_type=String)

    # Check optional fields
    check_column_constraints(Character, "description", nullable=True, column_type=Text)
    check_column_constraints(Character, "avatar_image", nullable=True, column_type=String)
```

## Getting Started Checklist

1. **Environment Setup**
   - [✓] Ensure Poetry is installed and virtual environment is activated
   - [✓] Install test dependencies: `poetry add --group dev pytest pytest-cov`
   - [✓] Configure pytest.ini and coverage settings

2. **Initial Test Implementation**
   - [✓] Create conftest.py with SQLAlchemy fixtures
   - [✓] Implement Base model tests
   - [✓] Run initial tests to verify configuration

3. **Full Test Suite Implementation**
   - [✓] Implement tests for all models
   - [✓] Run full test suite
   - [✓] Verify coverage meets targets

4. **Documentation**
   - [✓] Document test running procedure
   - [✓] Document coverage reporting
   - [✓] Update project README with testing instructions
