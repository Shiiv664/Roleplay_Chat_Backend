"""Test fixture helper functions for model testing.

This module provides reusable fixtures and patterns for common test scenarios.
"""

import datetime
import time

# pytest will be imported by the test files using these helpers
from sqlalchemy import text


def create_unique_label(prefix="test"):
    """Create a unique label using the current timestamp.

    Args:
        prefix: Prefix for the label (default: "test")

    Returns:
        A string with format "{prefix}_{timestamp}" that can be used for label fields
    """
    timestamp = time.time()
    return f"{prefix}_{timestamp}"


def force_update_timestamp(
    db_session, model_instance, field_name="updated_at", hours_offset=1
):
    """Force update a timestamp field using SQL to test timestamp behavior.

    This is useful for testing updated_at fields that are otherwise hard to test.

    Args:
        db_session: SQLAlchemy session
        model_instance: Model instance to update
        field_name: Name of the timestamp field (default: "updated_at")
        hours_offset: Hours to add to current time (default: 1)

    Returns:
        The new timestamp value
    """
    table_name = model_instance.__tablename__
    new_time = datetime.datetime.now() + datetime.timedelta(hours=hours_offset)

    db_session.execute(
        text(f"UPDATE {table_name} SET {field_name} = :new_time WHERE id = :id"),
        {"new_time": new_time, "id": model_instance.id},
    )
    db_session.commit()

    # Refresh the instance from the database
    db_session.refresh(model_instance)
    return getattr(model_instance, field_name)


def create_model_with_unique_constraint(
    model_class, db_session, unique_field, **kwargs
):
    """Create a model instance with a unique field value.

    Args:
        model_class: The model class to instantiate
        db_session: SQLAlchemy session
        unique_field: Name of the field with a unique constraint
        **kwargs: Additional fields for the model instance

    Returns:
        The created and persisted model instance
    """
    # Make unique label based on timestamp if not provided
    if unique_field not in kwargs:
        kwargs[unique_field] = create_unique_label(model_class.__name__.lower())

    instance = model_class(**kwargs)
    db_session.add(instance)
    db_session.commit()
    return instance


def create_related_models(
    db_session,
    parent_factory,
    child_factory,
    parent_attr,
    child_attr,
    parent_kwargs=None,
    child_kwargs=None,
):
    """Create related parent and child models.

    Args:
        db_session: SQLAlchemy session
        parent_factory: Factory function to create the parent model
        child_factory: Factory function to create the child model
        parent_attr: Attribute name on parent that relates to child(ren)
        child_attr: Attribute name on child that relates to parent
        parent_kwargs: Additional kwargs for parent factory
        child_kwargs: Additional kwargs for child factory

    Returns:
        Tuple of (parent, child) model instances
    """
    parent_kwargs = parent_kwargs or {}
    child_kwargs = child_kwargs or {}

    # Create parent
    parent = parent_factory(**parent_kwargs)
    db_session.add(parent)
    db_session.flush()

    # Create child with relationship to parent
    child_kwargs[child_attr] = parent
    child = child_factory(**child_kwargs)
    db_session.add(child)
    db_session.commit()

    return parent, child
