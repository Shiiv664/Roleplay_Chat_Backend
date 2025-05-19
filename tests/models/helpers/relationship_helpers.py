"""Relationship testing helper functions for model testing.

This module provides reusable test functions for validating SQLAlchemy relationship
configurations, cascade behaviors, and bidirectional references.
"""

import pytest
from sqlalchemy.exc import IntegrityError


def test_relationship(
    db_session,
    parent_obj,
    child_obj,
    parent_attr,
    child_attr,
    is_collection,  # Required parameter, no default
    bidirectional,  # Required parameter, no default
):
    """Test a relationship between two model instances.

    Args:
        db_session: SQLAlchemy session
        parent_obj: Parent model instance
        child_obj: Child model instance
        parent_attr: Attribute name on parent that relates to child
        child_attr: Attribute name on child that relates to parent
        is_collection: Whether the parent-to-child relationship is a collection (many)
                     Specify True for one-to-many or many-to-many, False for one-to-one
        bidirectional: Whether the relationship is bidirectional
                      Specify True for bidirectional relationships, False for one-way
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
        if hasattr(parent_rel, "all"):  # For dynamic relationships
            assert child_obj in parent_rel.all()
        else:
            assert child_obj in parent_rel
    else:
        assert parent_rel == child_obj

    # Test child to parent relationship if bidirectional
    if bidirectional:
        child_rel = getattr(child_obj, child_attr)
        assert child_rel == parent_obj


def test_foreign_key_constraint(db_session, model_factory, fk_field, invalid_id):
    """Test that a foreign key constraint is enforced.

    Args:
        db_session: SQLAlchemy session
        model_factory: Function that creates a model instance
        fk_field: Foreign key field name to test
        invalid_id: Invalid ID to test with (typically a large number like 999999)
    """
    # Create instance with invalid foreign key
    instance = model_factory(**{fk_field: invalid_id})
    db_session.add(instance)

    # Should raise IntegrityError due to foreign key constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete(
    db_session, parent_obj, child_obj, parent_attr, child_attr, child_class
):
    """Test that deleting a parent cascades to its children.

    Args:
        db_session: SQLAlchemy session
        parent_obj: Parent model instance
        child_obj: Child model instance
        parent_attr: Attribute name on parent that relates to child
        child_attr: Attribute name on child that relates to parent
        child_class: Class of the child model to use for database queries
    """
    # Use provided child_class for queries

    # Set up relationship
    setattr(child_obj, child_attr, parent_obj)
    db_session.add_all([parent_obj, child_obj])
    db_session.commit()

    # Store child ID for verification
    child_id = child_obj.id

    # Delete parent
    db_session.delete(parent_obj)
    db_session.commit()

    # Verify child was deleted
    deleted_child = db_session.query(child_class).filter_by(id=child_id).first()
    assert (
        deleted_child is None
    ), "Expected child to be deleted via cascade, but it still exists"


def test_many_to_many_relationship(db_session, model1, model2, rel_attr1, rel_attr2):
    """Test a many-to-many relationship between two models.

    Args:
        db_session: SQLAlchemy session
        model1: First model instance
        model2: Second model instance
        rel_attr1: Relationship attribute on model1 that links to model2
        rel_attr2: Relationship attribute on model2 that links to model1
    """
    # Add both objects to session and flush to generate IDs
    db_session.add_all([model1, model2])
    db_session.flush()

    # Set up the relationship in one direction
    getattr(model1, rel_attr1).append(model2)
    db_session.flush()

    # Test relationships in both directions
    assert model2 in getattr(model1, rel_attr1)
    assert model1 in getattr(model2, rel_attr2)

    # Remove the relationship
    getattr(model1, rel_attr1).remove(model2)
    db_session.flush()

    # Test that relationships are removed in both directions
    assert model2 not in getattr(model1, rel_attr1)
    assert model1 not in getattr(model2, rel_attr2)
