"""Tests for the AIModelRepository class."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.application_settings import ApplicationSettings
from app.repositories.ai_model_repository import AIModelRepository
from app.utils.exceptions import DatabaseError


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

    def test_get_default_model(self, db_session, create_ai_model):
        """Test getting the default AI model."""
        repo = AIModelRepository(db_session)

        # Create an AI model
        model = create_ai_model(label="default_model", description="Default AI model")
        db_session.add(model)
        db_session.flush()

        # Create application settings with this model as default
        settings = ApplicationSettings(default_ai_model_id=model.id)
        db_session.add(settings)
        db_session.commit()

        # Get default model
        default_model = repo.get_default_model()
        assert default_model is not None
        assert default_model.id == model.id
        assert default_model.label == "default_model"

    def test_get_default_model_not_found(self, db_session):
        """Test getting the default AI model when none is set."""
        repo = AIModelRepository(db_session)

        # Get default model without setting one
        default_model = repo.get_default_model()
        assert default_model is None

    def test_database_error_in_get_default_model(self, db_session):
        """Test handling of database errors in get_default_model method."""
        repo = AIModelRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(
            db_session, "query", side_effect=SQLAlchemyError("Test error")
        ):
            with pytest.raises(DatabaseError):
                repo.get_default_model()
