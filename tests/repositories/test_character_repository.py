"""Tests for the CharacterRepository class."""

import pytest

# Character model is imported through the repository
from app.repositories.character_repository import CharacterRepository


class TestCharacterRepository:
    """Test character-specific repository functionality."""

    @pytest.fixture
    def create_characters(self, db_session):
        """Create sample characters for testing."""
        repo = CharacterRepository(db_session)

        characters = [
            repo.create(
                label="char1", name="Character 1", description="First test character"
            ),
            repo.create(
                label="char2", name="Character 2", description="Second test character"
            ),
            repo.create(
                label="char3",
                name="Character 3",
                description="Third test character with special keywords",
            ),
        ]

        db_session.commit()
        return characters

    def test_get_by_label(self, db_session, create_characters):
        """Test retrieving a character by label."""
        repo = CharacterRepository(db_session)

        character = repo.get_by_label("char2")

        assert character is not None
        assert character.label == "char2"
        assert character.name == "Character 2"

    def test_get_by_label_not_found(self, db_session):
        """Test retrieving a non-existent character by label."""
        repo = CharacterRepository(db_session)

        character = repo.get_by_label("non_existent")

        assert character is None

    def test_search(self, db_session, create_characters):
        """Test searching characters by name or description."""
        repo = CharacterRepository(db_session)

        # Search by name
        results = repo.search("Character 1")
        assert len(results) == 1
        assert results[0].name == "Character 1"

        # Search by description
        results = repo.search("special keywords")
        assert len(results) == 1
        assert results[0].name == "Character 3"

        # Search with multiple matches
        results = repo.search("test character")
        assert len(results) == 3

        # Search with no matches
        results = repo.search("no matches")
        assert len(results) == 0
