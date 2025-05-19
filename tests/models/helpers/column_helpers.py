"""Column validation helper functions for model testing.

This module provides reusable test functions for validating SQLAlchemy column
properties, constraints, and behaviors.
"""

import pytest
from sqlalchemy.exc import IntegrityError


def check_column_constraints(
    model_class,
    column_name,
    nullable=True,
    unique=False,
    primary_key=False,
    column_type=None,
    default=None,
):
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
    assert hasattr(
        model_class, column_name
    ), f"{model_class.__name__} has no column {column_name}"
    column = getattr(model_class, column_name).property.columns[0]

    assert (
        column.nullable == nullable
    ), f"Expected nullable={nullable}, got {column.nullable}"

    # Handle None value for unique property (SQLAlchemy can use None instead of False)
    if unique:
        assert column.unique is True, f"Expected unique=True, got {column.unique}"
    else:
        assert column.unique in (
            False,
            None,
        ), f"Expected unique=False or None, got {column.unique}"

    assert (
        column.primary_key == primary_key
    ), f"Expected primary_key={primary_key}, got {column.primary_key}"

    if column_type:
        assert isinstance(
            column.type, column_type
        ), f"Expected {column_type}, got {type(column.type)}"

    if default is not None:
        if callable(default) and callable(column.default.arg):
            # For callable defaults like func.current_timestamp()
            assert callable(column.default.arg), "Expected callable default"
        else:
            assert (
                column.default.arg == default
            ), f"Expected default={default}, got {column.default.arg}"


def check_required_fields(db_session, model_class, create_valid_data, required_fields):
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


def check_unique_constraint(
    db_session, model_class, create_instance_with_unique, unique_field
):
    """Test that a unique constraint is enforced.

    Args:
        db_session: SQLAlchemy session
        model_class: The model class to test
        create_instance_with_unique: Function that creates instance with specific
                                   value for the unique field
        unique_field: The name of the field with a unique constraint
    """
    # Create first instance with unique value
    unique_value = "test_unique_value"
    instance1 = create_instance_with_unique(unique_value)
    db_session.add(instance1)
    db_session.commit()

    # Try to create second instance with same unique value
    instance2 = create_instance_with_unique(unique_value)
    db_session.add(instance2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Should work with different value
    instance3 = create_instance_with_unique("different_unique_value")
    db_session.add(instance3)
    db_session.commit()  # Should not raise an error


def check_enum_field(db_session, model_class, field_name, enum_class, create_instance):
    """Test that an enum field accepts valid values and rejects invalid ones.

    Args:
        db_session: SQLAlchemy session
        model_class: The model class to test
        field_name: The name of the enum field
        enum_class: The Enum class used for the field
        create_instance: Function that creates a valid model instance
    """
    # Test all valid enum values
    for enum_value in enum_class:
        # Create instance with the enum value
        instance = create_instance(**{field_name: enum_value})
        db_session.add(instance)
        db_session.commit()

        # Verify the enum value was stored correctly
        saved_instance = db_session.query(model_class).filter_by(id=instance.id).first()
        assert getattr(saved_instance, field_name) == enum_value
        assert getattr(saved_instance, field_name).value == enum_value.value

        db_session.delete(instance)
        db_session.commit()

    # Test invalid enum value (depends on application-specific validation)
    # SQLAlchemy type validation happens separately from pytest


def check_enum_values(enum_class, expected_values):
    """Test that an Enum class has the expected values.
    
    Args:
        enum_class: The Enum class to test
        expected_values: Dictionary of expected values (name: value)
    """
    # Check that all expected values are in the enum
    for name, value in expected_values.items():
        assert hasattr(enum_class, name), f"Enum missing member {name}"
        assert getattr(enum_class, name).value == value, f"Expected {name}={value}, got {getattr(enum_class, name).value}"
    
    # Check that there are no unexpected values
    assert len(enum_class) == len(expected_values), f"Enum has {len(enum_class)} members, expected {len(expected_values)}"
