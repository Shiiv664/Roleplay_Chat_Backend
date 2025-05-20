"""Tests for the SystemPromptRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.application_settings import ApplicationSettings
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.utils.exceptions import DatabaseError


class TestSystemPromptRepository:
    """Test system prompt repository functionality."""

    @pytest.fixture
    def create_prompts(self, db_session):
        """Create sample system prompts for testing."""
        repo = SystemPromptRepository(db_session)

        prompts = [
            repo.create(
                label="standard",
                content="You are a helpful AI assistant that answers questions accurately.",
            ),
            repo.create(
                label="roleplay",
                content="You are roleplaying as a detective in a noir setting.",
            ),
            repo.create(
                label="creative",
                content="Be creative, imaginative, and entertaining in your responses.",
            ),
        ]

        db_session.commit()
        return prompts

    def test_get_by_label(self, db_session, create_prompts):
        """Test retrieving a system prompt by label."""
        repo = SystemPromptRepository(db_session)

        prompt = repo.get_by_label("roleplay")

        assert prompt is not None
        assert prompt.label == "roleplay"
        assert "detective" in prompt.content
        assert "noir" in prompt.content

    def test_get_by_label_not_found(self, db_session):
        """Test retrieving a non-existent system prompt by label."""
        repo = SystemPromptRepository(db_session)

        prompt = repo.get_by_label("non_existent")

        assert prompt is None

    def test_search(self, db_session, create_prompts):
        """Test searching system prompts by label or content."""
        repo = SystemPromptRepository(db_session)

        # Search by label
        results = repo.search("standard")
        assert len(results) == 1
        assert results[0].label == "standard"

        # Search by content
        results = repo.search("detective")
        assert len(results) == 1
        assert results[0].label == "roleplay"

        # Search with multiple matches
        results = repo.search("creative")
        assert len(results) == 1
        assert results[0].label == "creative"

        # Search case insensitive
        results = repo.search("CREATIVE")
        assert len(results) == 1
        assert results[0].label == "creative"

        # Search with no matches
        results = repo.search("no matches")
        assert len(results) == 0

    def test_get_default_prompt(self, db_session, create_system_prompt):
        """Test getting the default system prompt."""
        repo = SystemPromptRepository(db_session)

        # Create a system prompt
        prompt = create_system_prompt(
            label="default_prompt", content="This is the default system prompt"
        )
        db_session.add(prompt)
        db_session.flush()

        # Create application settings with this prompt as default
        settings = ApplicationSettings(default_system_prompt_id=prompt.id)
        db_session.add(settings)
        db_session.commit()

        # Get default prompt
        default_prompt = repo.get_default_prompt()
        assert default_prompt is not None
        assert default_prompt.id == prompt.id
        assert default_prompt.label == "default_prompt"

    def test_get_default_prompt_not_found(self, db_session):
        """Test getting the default system prompt when none is set."""
        repo = SystemPromptRepository(db_session)

        # Get default prompt without setting one
        default_prompt = repo.get_default_prompt()
        assert default_prompt is None

    def test_database_error_in_get_default_prompt(self, db_session):
        """Test handling of database errors in get_default_prompt method."""
        repo = SystemPromptRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_default_prompt()
