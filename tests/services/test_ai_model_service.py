"""Tests for the AIModelService class."""

from unittest.mock import MagicMock

import pytest

from app.models.ai_model import AIModel
from app.services.ai_model_service import AIModelService
from app.utils.exceptions import (
    BusinessRuleError,
    ValidationError,
)


class TestAIModelService:
    """Test the AIModelService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock AI model repository."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create an AIModelService with a mock repository."""
        return AIModelService(mock_repository)

    @pytest.fixture
    def sample_model(self):
        """Create a sample AI model for testing."""
        return AIModel(id=1, label="gpt-4", description="Advanced language model")

    def test_get_model(self, service, mock_repository, sample_model):
        """Test getting an AI model by ID."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        # Execute
        result = service.get_model(1)

        # Verify
        assert result == sample_model
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_model_by_label(self, service, mock_repository, sample_model):
        """Test getting an AI model by label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_model

        # Execute
        result = service.get_model_by_label("gpt-4")

        # Verify
        assert result == sample_model
        mock_repository.get_by_label.assert_called_once_with("gpt-4")

    def test_get_all_models(self, service, mock_repository, sample_model):
        """Test getting all AI models."""
        # Setup
        mock_repository.get_all.return_value = [sample_model]

        # Execute
        result = service.get_all_models()

        # Verify
        assert result == [sample_model]
        mock_repository.get_all.assert_called_once()

    def test_search_models(self, service, mock_repository, sample_model):
        """Test searching for AI models."""
        # Setup
        mock_repository.search.return_value = [sample_model]

        # Execute
        result = service.search_models("gpt")

        # Verify
        assert result == [sample_model]
        mock_repository.search.assert_called_once_with("gpt")

    def test_search_models_validation(self, service, mock_repository):
        """Test search validation for short queries."""
        with pytest.raises(ValidationError) as excinfo:
            service.search_models("")

        assert "Search query must be at least 2 characters" in str(excinfo.value)
        mock_repository.search.assert_not_called()

        with pytest.raises(ValidationError):
            service.search_models("a")
        mock_repository.search.assert_not_called()

    def test_get_default_model(self, service, mock_repository, sample_model):
        """Test getting default AI model."""
        # Setup
        mock_repository.get_default_model.return_value = sample_model

        # Execute
        result = service.get_default_model()

        # Verify
        assert result == sample_model
        mock_repository.get_default_model.assert_called_once()

    def test_create_model(self, service, mock_repository):
        """Test creating an AI model."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing model
        mock_repository.create.return_value = AIModel(
            id=1, label="claude-3", description="New language model"
        )

        # Execute
        result = service.create_model(
            label="claude-3", description="New language model"
        )

        # Verify
        assert result.id == 1
        assert result.label == "claude-3"
        assert result.description == "New language model"
        mock_repository.create.assert_called_once_with(
            label="claude-3", description="New language model"
        )

    def test_create_model_label_exists(self, service, mock_repository, sample_model):
        """Test creating an AI model with existing label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_model  # Existing model

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_model(
                label="gpt-4", description="New model"  # Already exists
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.create.assert_not_called()

    def test_create_model_validation_errors(self, service, mock_repository):
        """Test AI model creation validation."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing model

        # Test empty label
        with pytest.raises(ValidationError) as excinfo:
            service.create_model(label="")

        assert "AI model validation failed" in str(excinfo.value)
        assert "required" in excinfo.value.details.get("label", "")

        # Test short label
        with pytest.raises(ValidationError) as excinfo:
            service.create_model(label="a")

        assert "AI model validation failed" in str(excinfo.value)
        assert "at least 2 characters" in excinfo.value.details.get("label", "")

        # Verify repository not called for any validation failures
        mock_repository.create.assert_not_called()

    def test_update_model(self, service, mock_repository, sample_model):
        """Test updating an AI model."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model
        mock_repository.get_by_label.return_value = None  # No conflict with new label

        updated_model = AIModel(
            id=1, label="gpt-4-turbo", description="Updated language model"
        )
        mock_repository.update.return_value = updated_model

        # Execute
        result = service.update_model(
            model_id=1, label="gpt-4-turbo", description="Updated language model"
        )

        # Verify
        assert result == updated_model
        mock_repository.update.assert_called_once_with(
            1, label="gpt-4-turbo", description="Updated language model"
        )

    def test_update_model_partial(self, service, mock_repository, sample_model):
        """Test partially updating an AI model."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        updated_model = AIModel(
            id=1,
            label="gpt-4",  # Unchanged
            description="Updated description",  # Only description is updated
        )
        mock_repository.update.return_value = updated_model

        # Execute - only update description
        result = service.update_model(model_id=1, description="Updated description")

        # Verify
        assert result == updated_model
        mock_repository.update.assert_called_once_with(
            1, description="Updated description"
        )

    def test_update_model_label_exists(self, service, mock_repository, sample_model):
        """Test updating a model with a label that already exists on another model."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        # Another model with the label we want to use
        existing_model = AIModel(
            id=2, label="existing_label", description="Existing model"  # Different ID
        )
        mock_repository.get_by_label.return_value = existing_model

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_model(
                model_id=1, label="existing_label"  # Already used by model with ID 2
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.update.assert_not_called()

    def test_update_model_same_label(self, service, mock_repository, sample_model):
        """Test updating a model with its own label is allowed."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model
        mock_repository.get_by_label.return_value = sample_model  # Same model

        updated_model = AIModel(
            id=1,
            label="gpt-4",  # Same label
            description="Updated description",  # Only description is updated
        )
        mock_repository.update.return_value = updated_model

        # Execute - update description but keep same label
        result = service.update_model(
            model_id=1,
            label="gpt-4",  # Same as current
            description="Updated description",
        )

        # Verify - update should succeed since label belongs to same model
        assert result == updated_model
        mock_repository.update.assert_called_once_with(
            1,
            description="Updated description",  # Label not included in update since it's the same
        )

    def test_delete_model(self, service, mock_repository, sample_model, mocker):
        """Test deleting an AI model."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Ensure default_in_settings is None
        sample_model.default_in_settings = None

        # Execute
        service.delete_model(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)

    def test_delete_model_with_sessions(
        self, service, mock_repository, sample_model, mocker
    ):
        """Test cannot delete model that is used in chat sessions."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        # Mock chat_sessions relationship with non-zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=2)

        # Ensure default_in_settings is None
        sample_model.default_in_settings = None

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_model(1)

        assert "Cannot delete AI model that is used in chat sessions" in str(
            excinfo.value
        )
        mock_repository.delete.assert_not_called()

    def test_delete_model_used_as_default(
        self, service, mock_repository, sample_model, mocker
    ):
        """Test cannot delete model that is set as default in settings."""
        # Setup
        mock_repository.get_by_id.return_value = sample_model

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock default_in_settings as non-None
        sample_model.default_in_settings = MagicMock()

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_model(1)

        assert (
            "Cannot delete AI model that is set as default in application settings"
            in str(excinfo.value)
        )
        mock_repository.delete.assert_not_called()
