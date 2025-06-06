"""Tests for the BaseRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.character import Character
from app.repositories.character_repository import CharacterRepository
from app.utils.exceptions import DatabaseError, ResourceNotFoundError, ValidationError


class TestBaseRepository:
    """Test base repository functionality using CharacterRepository as an example."""

    @pytest.fixture
    def character_data(self):
        """Sample character data for testing."""
        return {
            "label": "test_character",
            "name": "Test Character",
            "description": "A character for testing",
        }

    def test_get_by_id_success(self, db_session, character_data):
        """Test successful retrieval by ID."""
        # Create character
        repo = CharacterRepository(db_session)
        character = repo.create(**character_data)
        db_session.commit()

        # Test get_by_id
        retrieved = repo.get_by_id(character.id)
        assert retrieved is not None
        assert retrieved.id == character.id
        assert retrieved.label == character_data["label"]
        assert retrieved.name == character_data["name"]

    def test_get_by_id_not_found(self, db_session):
        """Test retrieval of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.get_by_id(999)  # Non-existent ID

    def test_create_success(self, db_session, character_data):
        """Test successful entity creation."""
        repo = CharacterRepository(db_session)
        character = repo.create(**character_data)
        db_session.commit()

        assert character is not None
        assert character.id is not None
        assert character.label == character_data["label"]
        assert character.name == character_data["name"]

        # Verify it was saved to the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character is not None

    def test_create_duplicate(self, db_session, character_data):
        """Test creation with duplicate unique field."""
        repo = CharacterRepository(db_session)

        # Create first character
        repo.create(**character_data)
        db_session.commit()

        # Try to create another with the same label
        with pytest.raises(ValidationError):
            repo.create(**character_data)

    def test_update_success(self, db_session, character_data):
        """Test successful entity update."""
        repo = CharacterRepository(db_session)

        # Create character
        character = repo.create(**character_data)
        db_session.commit()

        # Update character
        updated = repo.update(character.id, name="Updated Name")
        db_session.commit()

        assert updated.name == "Updated Name"
        assert updated.label == character_data["label"]  # Unchanged

        # Verify it was updated in the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character.name == "Updated Name"

    def test_update_not_found(self, db_session):
        """Test update of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.update(999, name="Updated Name")  # Non-existent ID

    def test_delete_success(self, db_session, character_data):
        """Test successful entity deletion."""
        repo = CharacterRepository(db_session)

        # Create character
        character = repo.create(**character_data)
        db_session.commit()

        # Delete character
        repo.delete(character.id)
        db_session.commit()

        # Verify it was deleted from the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character is None

    def test_delete_not_found(self, db_session):
        """Test deletion of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.delete(999)  # Non-existent ID

    def test_get_all(self, db_session):
        """Test getting all entities."""
        repo = CharacterRepository(db_session)

        # Create multiple characters
        repo.create(label="char1", name="Character 1")
        repo.create(label="char2", name="Character 2")
        repo.create(label="char3", name="Character 3")
        db_session.commit()

        # Get all characters
        characters = repo.get_all()

        assert len(characters) >= 3

    def test_database_error_handling(self, db_session):
        """Test handling of database errors."""
        repo = CharacterRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_all()

    def test_transaction_commit(self, db_session):
        """Test successful transaction commit."""
        repo = CharacterRepository(db_session)

        with repo.transaction():
            repo.create(label="test_transaction", name="Transaction Test")

        # After successful commit, character should exist in DB
        db_character = repo.get_by_label("test_transaction")
        assert db_character is not None
        assert db_character.name == "Transaction Test"

    def test_transaction_rollback_on_error(self, db_session):
        """Test transaction rollback on error."""
        repo = CharacterRepository(db_session)

        # Should cause rollback
        try:
            with repo.transaction():
                repo.create(label="rollback_test", name="Rollback Test")
                raise ValueError("Test error to trigger rollback")
        except ValueError:
            pass

        # After rollback, character should not exist in DB
        # Check if the character exists in the database
        db_character = (
            db_session.query(Character).filter_by(label="rollback_test").first()
        )
        assert db_character is None
