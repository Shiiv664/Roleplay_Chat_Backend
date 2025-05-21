"""Service for Character entity operations."""

import logging
from typing import Dict, List, Optional

from app.models.character import Character
from app.repositories.character_repository import CharacterRepository
from app.services.file_upload_service import FileUploadService
from app.utils.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


class CharacterService:
    """Service for managing Character entities.

    This service implements business logic and validation for Character entities,
    using the CharacterRepository for data access.
    """

    def __init__(self, character_repository: CharacterRepository):
        """Initialize the service with a character repository.

        Args:
            character_repository: Repository for Character data access
        """
        self.repository = character_repository

    def get_character(self, character_id: int) -> Character:
        """Get a character by ID.

        Args:
            character_id: ID of the character to retrieve

        Returns:
            Character: The requested character entity

        Raises:
            ResourceNotFoundError: If character with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting character with ID {character_id}")
        return self.repository.get_by_id(character_id)

    def get_character_by_label(self, label: str) -> Optional[Character]:
        """Get a character by unique label.

        Args:
            label: Unique label of the character to retrieve

        Returns:
            Character or None: The requested character entity or None if not found

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting character with label '{label}'")
        return self.repository.get_by_label(label)

    def get_all_characters(self) -> List[Character]:
        """Get all characters.

        Returns:
            List[Character]: List of all character entities

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting all characters")
        return self.repository.get_all()

    def search_characters(self, query: str) -> List[Character]:
        """Search for characters by name or description.

        Args:
            query: Search string to look for in character name or description

        Returns:
            List[Character]: List of matching character entities

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info(f"Searching characters with query '{query}'")
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        return self.repository.search(query)

    def create_character(
        self,
        label: str,
        name: str,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Character:
        """Create a new character.

        Args:
            label: Unique identifier for the character
            name: Display name of the character
            avatar_image: Path or URL to character's avatar image (optional)
            description: Detailed description of the character (optional)

        Returns:
            Character: The created character entity

        Raises:
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Validate input
        self._validate_character_data(label, name, avatar_image, description)

        # Check if character with this label already exists
        existing = self.repository.get_by_label(label)
        if existing:
            raise ValidationError(f"Character with label '{label}' already exists")

        logger.info(f"Creating character with label '{label}'")
        return self.repository.create(
            label=label, name=name, avatar_image=avatar_image, description=description
        )

    def update_character(
        self,
        character_id: int,
        label: Optional[str] = None,
        name: Optional[str] = None,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Character:
        """Update an existing character.

        Args:
            character_id: ID of the character to update
            label: New label for the character (optional)
            name: New name for the character (optional)
            avatar_image: New avatar image path/URL (optional)
            description: New description (optional)

        Returns:
            Character: The updated character entity

        Raises:
            ResourceNotFoundError: If character with the given ID is not found
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Get current character to ensure it exists
        character = self.repository.get_by_id(character_id)

        # Prepare update data
        update_data = {}

        if label is not None and label != character.label:
            # Validate new label
            if not label or len(label.strip()) < 2:
                raise ValidationError("Character label must be at least 2 characters")

            # Check if the new label is already in use by another character
            existing = self.repository.get_by_label(label)
            if existing and existing.id != character_id:
                raise ValidationError(f"Character with label '{label}' already exists")
            update_data["label"] = label

        if name is not None:
            # Validate new name
            if not name or len(name.strip()) < 1:
                raise ValidationError("Character name cannot be empty")
            update_data["name"] = name

        if avatar_image is not None:
            update_data["avatar_image"] = avatar_image

        if description is not None:
            update_data["description"] = description

        if not update_data:
            # Nothing to update
            return character

        logger.info(f"Updating character with ID {character_id}")
        return self.repository.update(character_id, **update_data)

    def delete_character(self, character_id: int) -> None:
        """Delete a character.

        Args:
            character_id: ID of the character to delete

        Raises:
            ResourceNotFoundError: If character with the given ID is not found
            BusinessRuleError: If the character cannot be deleted due to constraints
            DatabaseError: If a database error occurs
        """
        # Get current character to ensure it exists
        character = self.repository.get_by_id(character_id)

        # Check if there are any chat sessions with this character
        # We can check the relationship if it's loaded, otherwise this would
        # be checked by the database constraint
        if hasattr(character, "chat_sessions"):
            # For SQLAlchemy dynamic relationships, we need to call count()
            chat_sessions_count = character.chat_sessions.count()

            if chat_sessions_count > 0:
                raise BusinessRuleError(
                    "Cannot delete character that is used in chat sessions",
                    details={"character_id": character_id},
                )

        logger.info(f"Deleting character with ID {character_id}")
        self.repository.delete(character_id)

    def _validate_character_data(
        self,
        label: str,
        name: str,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Validate character data.

        Args:
            label: Character label to validate
            name: Character name to validate
            avatar_image: Character avatar image to validate (optional)
            description: Character description to validate (optional)

        Raises:
            ValidationError: If validation fails
        """
        errors: Dict[str, str] = {}

        # Label validation
        if not label:
            errors["label"] = "Character label is required"
        elif len(label.strip()) < 2:
            errors["label"] = "Character label must be at least 2 characters"

        # Name validation
        if not name:
            errors["name"] = "Character name is required"
        elif len(name.strip()) < 1:
            errors["name"] = "Character name cannot be empty"

        # Avatar image validation (optional)
        if avatar_image is not None and not isinstance(avatar_image, str):
            errors["avatar_image"] = "Avatar image must be a string"

        # Description validation (optional)
        if description is not None and not isinstance(description, str):
            errors["description"] = "Description must be a string"

        if errors:
            raise ValidationError("Character validation failed", details=errors)
