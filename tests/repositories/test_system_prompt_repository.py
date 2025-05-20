"""Tests for the SystemPromptRepository class."""

import pytest

from app.repositories.system_prompt_repository import SystemPromptRepository


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
