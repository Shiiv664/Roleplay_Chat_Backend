"""Service for SystemPrompt entity operations."""

import logging
from typing import Dict, List, Optional

from app.models.system_prompt import SystemPrompt
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.utils.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


class SystemPromptService:
    """Service for managing SystemPrompt entities.

    This service implements business logic and validation for SystemPrompt entities,
    using the SystemPromptRepository for data access.
    """

    def __init__(self, system_prompt_repository: SystemPromptRepository):
        """Initialize the service with a system prompt repository.

        Args:
            system_prompt_repository: Repository for SystemPrompt data access
        """
        self.repository = system_prompt_repository

    def get_prompt(self, prompt_id: int) -> SystemPrompt:
        """Get a system prompt by ID.

        Args:
            prompt_id: ID of the prompt to retrieve

        Returns:
            SystemPrompt: The requested system prompt

        Raises:
            ResourceNotFoundError: If prompt with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting system prompt with ID {prompt_id}")
        return self.repository.get_by_id(prompt_id)

    def get_prompt_by_label(self, label: str) -> Optional[SystemPrompt]:
        """Get a system prompt by unique label.

        Args:
            label: Unique label of the prompt to retrieve

        Returns:
            SystemPrompt or None: The requested prompt or None if not found

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting system prompt with label '{label}'")
        return self.repository.get_by_label(label)

    def get_all_prompts(self) -> List[SystemPrompt]:
        """Get all system prompts.

        Returns:
            List[SystemPrompt]: List of all system prompts

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting all system prompts")
        return self.repository.get_all()

    def search_prompts(self, query: str) -> List[SystemPrompt]:
        """Search for system prompts by label or content.

        Args:
            query: Search string to look for in prompt label or content

        Returns:
            List[SystemPrompt]: List of matching prompts

        Raises:
            ValidationError: If search query is too short
            DatabaseError: If a database error occurs
        """
        logger.info(f"Searching system prompts with query '{query}'")
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        return self.repository.search(query)

    def get_default_prompt(self) -> Optional[SystemPrompt]:
        """Get the default system prompt if one exists.

        Returns:
            SystemPrompt or None: The default prompt if it exists, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting default system prompt")
        return self.repository.get_default_prompt()

    def create_prompt(self, label: str, content: str) -> SystemPrompt:
        """Create a new system prompt.

        Args:
            label: Unique identifier for the prompt
            content: The prompt text content

        Returns:
            SystemPrompt: The created prompt

        Raises:
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Validate input
        self._validate_prompt_data(label, content)

        # Check if prompt with this label already exists
        existing = self.repository.get_by_label(label)
        if existing:
            raise ValidationError(f"System prompt with label '{label}' already exists")

        logger.info(f"Creating system prompt with label '{label}'")
        return self.repository.create(label=label, content=content)

    def update_prompt(
        self,
        prompt_id: int,
        label: Optional[str] = None,
        content: Optional[str] = None,
    ) -> SystemPrompt:
        """Update an existing system prompt.

        Args:
            prompt_id: ID of the prompt to update
            label: New label for the prompt (optional)
            content: New content (optional)

        Returns:
            SystemPrompt: The updated prompt

        Raises:
            ResourceNotFoundError: If prompt with the given ID is not found
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Get current prompt to ensure it exists
        prompt = self.repository.get_by_id(prompt_id)

        # Prepare update data
        update_data = {}

        if label is not None and label != prompt.label:
            # Validate new label
            if not label or len(label.strip()) < 2:
                raise ValidationError(
                    "System prompt label must be at least 2 characters"
                )

            # Check if the new label is already in use by another prompt
            existing = self.repository.get_by_label(label)
            if existing and existing.id != prompt_id:
                raise ValidationError(
                    f"System prompt with label '{label}' already exists"
                )
            update_data["label"] = label

        if content is not None:
            # Validate new content
            if not content or len(content.strip()) < 1:
                raise ValidationError("System prompt content cannot be empty")
            update_data["content"] = content

        if not update_data:
            # Nothing to update
            return prompt

        logger.info(f"Updating system prompt with ID {prompt_id}")
        return self.repository.update(prompt_id, **update_data)

    def delete_prompt(self, prompt_id: int) -> None:
        """Delete a system prompt.

        Args:
            prompt_id: ID of the prompt to delete

        Raises:
            ResourceNotFoundError: If prompt with the given ID is not found
            BusinessRuleError: If the prompt cannot be deleted due to constraints
            DatabaseError: If a database error occurs
        """
        # Get current prompt to ensure it exists
        prompt = self.repository.get_by_id(prompt_id)

        # Check if there are any chat sessions with this prompt
        if hasattr(prompt, "chat_sessions"):
            chat_sessions_count = prompt.chat_sessions.count()
            if chat_sessions_count > 0:
                raise BusinessRuleError(
                    "Cannot delete system prompt that is used in chat sessions",
                    details={"prompt_id": prompt_id},
                )

        # Check if this prompt is set as the default in application settings
        if hasattr(prompt, "default_in_settings") and prompt.default_in_settings:
            raise BusinessRuleError(
                "Cannot delete system prompt that is set as default in application settings",
                details={"prompt_id": prompt_id},
            )

        logger.info(f"Deleting system prompt with ID {prompt_id}")
        self.repository.delete(prompt_id)

    def _validate_prompt_data(self, label: str, content: str) -> None:
        """Validate system prompt data.

        Args:
            label: Prompt label to validate
            content: Prompt content to validate

        Raises:
            ValidationError: If validation fails
        """
        errors: Dict[str, str] = {}

        # Label validation
        if not label:
            errors["label"] = "System prompt label is required"
        elif len(label.strip()) < 2:
            errors["label"] = "System prompt label must be at least 2 characters"

        # Content validation
        if not content:
            errors["content"] = "System prompt content is required"
        elif len(content.strip()) < 1:
            errors["content"] = "System prompt content cannot be empty"

        if errors:
            raise ValidationError("System prompt validation failed", details=errors)
