"""Tests for the SystemPromptService class."""

from unittest.mock import MagicMock

import pytest

from app.models.system_prompt import SystemPrompt
from app.services.system_prompt_service import SystemPromptService
from app.utils.exceptions import (
    BusinessRuleError,
    ValidationError,
)


class TestSystemPromptService:
    """Test the SystemPromptService functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock system prompt repository."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a SystemPromptService with a mock repository."""
        return SystemPromptService(mock_repository)

    @pytest.fixture
    def sample_prompt(self):
        """Create a sample system prompt for testing."""
        return SystemPrompt(
            id=1, label="test_prompt", content="You are a helpful assistant."
        )

    def test_get_prompt(self, service, mock_repository, sample_prompt):
        """Test getting a system prompt by ID."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        # Execute
        result = service.get_prompt(1)

        # Verify
        assert result == sample_prompt
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_prompt_by_label(self, service, mock_repository, sample_prompt):
        """Test getting a system prompt by label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_prompt

        # Execute
        result = service.get_prompt_by_label("test_prompt")

        # Verify
        assert result == sample_prompt
        mock_repository.get_by_label.assert_called_once_with("test_prompt")

    def test_get_all_prompts(self, service, mock_repository, sample_prompt):
        """Test getting all system prompts."""
        # Setup
        mock_repository.get_all.return_value = [sample_prompt]

        # Execute
        result = service.get_all_prompts()

        # Verify
        assert result == [sample_prompt]
        mock_repository.get_all.assert_called_once()

    def test_search_prompts(self, service, mock_repository, sample_prompt):
        """Test searching for system prompts."""
        # Setup
        mock_repository.search.return_value = [sample_prompt]

        # Execute
        result = service.search_prompts("helpful")

        # Verify
        assert result == [sample_prompt]
        mock_repository.search.assert_called_once_with("helpful")

    def test_search_prompts_validation(self, service, mock_repository):
        """Test search validation for short queries."""
        with pytest.raises(ValidationError) as excinfo:
            service.search_prompts("")

        assert "Search query must be at least 2 characters" in str(excinfo.value)
        mock_repository.search.assert_not_called()

        with pytest.raises(ValidationError):
            service.search_prompts("a")
        mock_repository.search.assert_not_called()

    def test_get_default_prompt(self, service, mock_repository, sample_prompt):
        """Test getting default system prompt."""
        # Setup
        mock_repository.get_default_prompt.return_value = sample_prompt

        # Execute
        result = service.get_default_prompt()

        # Verify
        assert result == sample_prompt
        mock_repository.get_default_prompt.assert_called_once()

    def test_create_prompt(self, service, mock_repository):
        """Test creating a system prompt."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing prompt
        mock_repository.create.return_value = SystemPrompt(
            id=1, label="new_prompt", content="You are a helpful coding assistant."
        )

        # Execute
        result = service.create_prompt(
            label="new_prompt", content="You are a helpful coding assistant."
        )

        # Verify
        assert result.id == 1
        assert result.label == "new_prompt"
        assert result.content == "You are a helpful coding assistant."
        mock_repository.create.assert_called_once_with(
            label="new_prompt", content="You are a helpful coding assistant."
        )

    def test_create_prompt_label_exists(self, service, mock_repository, sample_prompt):
        """Test creating a system prompt with existing label."""
        # Setup
        mock_repository.get_by_label.return_value = sample_prompt  # Existing prompt

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.create_prompt(
                label="test_prompt", content="New content"  # Already exists
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.create.assert_not_called()

    def test_create_prompt_validation_errors(self, service, mock_repository):
        """Test system prompt creation validation."""
        # Setup
        mock_repository.get_by_label.return_value = None  # No existing prompt

        # Test empty label
        with pytest.raises(ValidationError) as excinfo:
            service.create_prompt(label="", content="Content")

        assert "System prompt validation failed" in str(excinfo.value)
        assert "required" in excinfo.value.details.get("label", "")

        # Test short label
        with pytest.raises(ValidationError) as excinfo:
            service.create_prompt(label="a", content="Content")

        assert "System prompt validation failed" in str(excinfo.value)
        assert "at least 2 characters" in excinfo.value.details.get("label", "")

        # Test empty content
        with pytest.raises(ValidationError) as excinfo:
            service.create_prompt(label="valid_label", content="")

        assert "System prompt validation failed" in str(excinfo.value)
        assert "required" in excinfo.value.details.get("content", "")

        # Verify repository not called for any validation failures
        mock_repository.create.assert_not_called()

    def test_update_prompt(self, service, mock_repository, sample_prompt):
        """Test updating a system prompt."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt
        mock_repository.get_by_label.return_value = None  # No conflict with new label

        updated_prompt = SystemPrompt(
            id=1, label="updated_prompt", content="Updated content for the prompt."
        )
        mock_repository.update.return_value = updated_prompt

        # Execute
        result = service.update_prompt(
            prompt_id=1,
            label="updated_prompt",
            content="Updated content for the prompt.",
        )

        # Verify
        assert result == updated_prompt
        mock_repository.update.assert_called_once_with(
            1, label="updated_prompt", content="Updated content for the prompt."
        )

    def test_update_prompt_partial(self, service, mock_repository, sample_prompt):
        """Test partially updating a system prompt."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        updated_prompt = SystemPrompt(
            id=1,
            label="test_prompt",  # Unchanged
            content="Updated content only",  # Only content is updated
        )
        mock_repository.update.return_value = updated_prompt

        # Execute - only update content
        result = service.update_prompt(prompt_id=1, content="Updated content only")

        # Verify
        assert result == updated_prompt
        mock_repository.update.assert_called_once_with(
            1, content="Updated content only"
        )

    def test_update_prompt_label_exists(self, service, mock_repository, sample_prompt):
        """Test updating a prompt with a label that already exists on another prompt."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        # Another prompt with the label we want to use
        existing_prompt = SystemPrompt(
            id=2,  # Different ID
            label="existing_label",
            content="Existing prompt content",
        )
        mock_repository.get_by_label.return_value = existing_prompt

        # Execute & Verify
        with pytest.raises(ValidationError) as excinfo:
            service.update_prompt(
                prompt_id=1, label="existing_label"  # Already used by prompt with ID 2
            )

        assert "already exists" in str(excinfo.value)
        mock_repository.update.assert_not_called()

    def test_update_prompt_same_label(self, service, mock_repository, sample_prompt):
        """Test updating a prompt with its own label is allowed."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt
        mock_repository.get_by_label.return_value = sample_prompt  # Same prompt

        updated_prompt = SystemPrompt(
            id=1,
            label="test_prompt",  # Same label
            content="Updated content only",  # Only content is updated
        )
        mock_repository.update.return_value = updated_prompt

        # Execute - update content but keep same label
        result = service.update_prompt(
            prompt_id=1,
            label="test_prompt",  # Same as current
            content="Updated content only",
        )

        # Verify - update should succeed since label belongs to same prompt
        assert result == updated_prompt
        mock_repository.update.assert_called_once_with(
            1,
            content="Updated content only",  # Label not included in update since it's the same
        )

    def test_delete_prompt(self, service, mock_repository, sample_prompt, mocker):
        """Test deleting a system prompt."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Ensure default_in_settings is None
        sample_prompt.default_in_settings = None

        # Execute
        service.delete_prompt(1)

        # Verify
        mock_repository.delete.assert_called_once_with(1)

    def test_delete_prompt_with_sessions(
        self, service, mock_repository, sample_prompt, mocker
    ):
        """Test cannot delete prompt that is used in chat sessions."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        # Mock chat_sessions relationship with non-zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=2)

        # Ensure default_in_settings is None
        sample_prompt.default_in_settings = None

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_prompt(1)

        assert "Cannot delete system prompt that is used in chat sessions" in str(
            excinfo.value
        )
        mock_repository.delete.assert_not_called()

    def test_delete_prompt_used_as_default(
        self, service, mock_repository, sample_prompt, mocker
    ):
        """Test cannot delete prompt that is set as default in settings."""
        # Setup
        mock_repository.get_by_id.return_value = sample_prompt

        # Mock chat_sessions relationship with zero count
        mocker.patch("sqlalchemy.orm.dynamic.AppenderQuery.count", return_value=0)

        # Mock default_in_settings as non-None
        sample_prompt.default_in_settings = MagicMock()

        # Execute & Verify
        with pytest.raises(BusinessRuleError) as excinfo:
            service.delete_prompt(1)

        assert (
            "Cannot delete system prompt that is set as default in application settings"
            in str(excinfo.value)
        )
        mock_repository.delete.assert_not_called()
