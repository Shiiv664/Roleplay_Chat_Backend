"""Tests for the AIModelRepository class."""

import pytest

from app.repositories.ai_model_repository import AIModelRepository


class TestAIModelRepository:
    """Test AI model repository functionality."""

    @pytest.fixture
    def create_models(self, db_session):
        """Create sample AI models for testing."""
        repo = AIModelRepository(db_session)

        models = [
            repo.create(label="gpt3", description="GPT-3 language model"),
            repo.create(label="gpt4", description="Advanced GPT-4 model"),
            repo.create(
                label="claude",
                description="Claude AI assistant with reasoning capabilities",
            ),
        ]

        db_session.commit()
        return models

    def test_get_by_label(self, db_session, create_models):
        """Test retrieving an AI model by label."""
        repo = AIModelRepository(db_session)

        model = repo.get_by_label("gpt4")

        assert model is not None
        assert model.label == "gpt4"
        assert model.description == "Advanced GPT-4 model"

    def test_get_by_label_not_found(self, db_session):
        """Test retrieving a non-existent AI model by label."""
        repo = AIModelRepository(db_session)

        model = repo.get_by_label("non_existent")

        assert model is None

    def test_search(self, db_session, create_models):
        """Test searching AI models by label or description."""
        repo = AIModelRepository(db_session)

        # Search by label
        results = repo.search("gpt")
        assert len(results) == 2
        assert {r.label for r in results} == {"gpt3", "gpt4"}

        # Search by description
        results = repo.search("reasoning")
        assert len(results) == 1
        assert results[0].label == "claude"

        # Search with multiple matches
        results = repo.search("model")
        assert len(results) == 2
        assert {r.label for r in results} == {"gpt3", "gpt4"}

        # Search with no matches
        results = repo.search("no matches")
        assert len(results) == 0
