"""Service for AIModel entity operations."""

import logging
from typing import Dict, List, Optional

from app.models.ai_model import AIModel
from app.repositories.ai_model_repository import AIModelRepository
from app.utils.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


class AIModelService:
    """Service for managing AIModel entities.

    This service implements business logic and validation for AIModel entities,
    using the AIModelRepository for data access.
    """

    def __init__(self, ai_model_repository: AIModelRepository):
        """Initialize the service with an AI model repository.

        Args:
            ai_model_repository: Repository for AIModel data access
        """
        self.repository = ai_model_repository

    def get_model(self, model_id: int) -> AIModel:
        """Get an AI model by ID.

        Args:
            model_id: ID of the model to retrieve

        Returns:
            AIModel: The requested AI model

        Raises:
            ResourceNotFoundError: If model with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting AI model with ID {model_id}")
        return self.repository.get_by_id(model_id)

    def get_model_by_label(self, label: str) -> Optional[AIModel]:
        """Get an AI model by unique label.

        Args:
            label: Unique label of the model to retrieve

        Returns:
            AIModel or None: The requested model or None if not found

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting AI model with label '{label}'")
        return self.repository.get_by_label(label)

    def get_all_models(self) -> List[AIModel]:
        """Get all AI models.

        Returns:
            List[AIModel]: List of all AI models

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting all AI models")
        return self.repository.get_all()

    def search_models(self, query: str) -> List[AIModel]:
        """Search for AI models by label or description.

        Args:
            query: Search string to look for in model label or description

        Returns:
            List[AIModel]: List of matching models

        Raises:
            ValidationError: If search query is too short
            DatabaseError: If a database error occurs
        """
        logger.info(f"Searching AI models with query '{query}'")
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        return self.repository.search(query)

    def get_default_model(self) -> Optional[AIModel]:
        """Get the default AI model if one exists.

        Returns:
            AIModel or None: The default model if it exists, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting default AI model")
        return self.repository.get_default_model()

    def create_model(self, label: str, description: Optional[str] = None) -> AIModel:
        """Create a new AI model.

        Args:
            label: Unique identifier for the model
            description: Detailed description of the model (optional)

        Returns:
            AIModel: The created model

        Raises:
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Validate input
        self._validate_model_data(label, description)

        # Check if model with this label already exists
        existing = self.repository.get_by_label(label)
        if existing:
            raise ValidationError(f"AI model with label '{label}' already exists")

        logger.info(f"Creating AI model with label '{label}'")
        return self.repository.create(label=label, description=description)

    def update_model(
        self,
        model_id: int,
        label: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AIModel:
        """Update an existing AI model.

        Args:
            model_id: ID of the model to update
            label: New label for the model (optional)
            description: New description (optional)

        Returns:
            AIModel: The updated model

        Raises:
            ResourceNotFoundError: If model with the given ID is not found
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Get current model to ensure it exists
        model = self.repository.get_by_id(model_id)

        # Prepare update data
        update_data = {}

        if label is not None and label != model.label:
            # Validate new label
            if not label or len(label.strip()) < 2:
                raise ValidationError("AI model label must be at least 2 characters")

            # Check if the new label is already in use by another model
            existing = self.repository.get_by_label(label)
            if existing and existing.id != model_id:
                raise ValidationError(f"AI model with label '{label}' already exists")
            update_data["label"] = label

        if description is not None:
            update_data["description"] = description

        if not update_data:
            # Nothing to update
            return model

        logger.info(f"Updating AI model with ID {model_id}")
        return self.repository.update(model_id, **update_data)

    def delete_model(self, model_id: int) -> None:
        """Delete an AI model.

        Args:
            model_id: ID of the model to delete

        Raises:
            ResourceNotFoundError: If model with the given ID is not found
            BusinessRuleError: If the model cannot be deleted due to constraints
            DatabaseError: If a database error occurs
        """
        # Get current model to ensure it exists
        model = self.repository.get_by_id(model_id)

        # Check if there are any chat sessions with this model
        if hasattr(model, "chat_sessions"):
            chat_sessions_count = model.chat_sessions.count()
            if chat_sessions_count > 0:
                raise BusinessRuleError(
                    "Cannot delete AI model that is used in chat sessions",
                    details={"model_id": model_id},
                )

        # Check if this model is set as the default in application settings
        if hasattr(model, "default_in_settings") and model.default_in_settings:
            raise BusinessRuleError(
                "Cannot delete AI model that is set as default in application settings",
                details={"model_id": model_id},
            )

        logger.info(f"Deleting AI model with ID {model_id}")
        self.repository.delete(model_id)

    def _validate_model_data(
        self, label: str, description: Optional[str] = None
    ) -> None:
        """Validate AI model data.

        Args:
            label: Model label to validate
            description: Model description to validate (optional)

        Raises:
            ValidationError: If validation fails
        """
        errors: Dict[str, str] = {}

        # Label validation
        if not label:
            errors["label"] = "AI model label is required"
        elif len(label.strip()) < 2:
            errors["label"] = "AI model label must be at least 2 characters"

        # Description validation (optional)
        if description is not None and not isinstance(description, str):
            errors["description"] = "Description must be a string"

        if errors:
            raise ValidationError("AI model validation failed", details=errors)
