"""Service for UserProfile entity operations."""

import logging
from typing import Dict, List, Optional

from app.models.user_profile import UserProfile
from app.repositories.user_profile_repository import UserProfileRepository
from app.services.file_upload_service import FileUploadService
from app.utils.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for managing UserProfile entities.

    This service implements business logic and validation for UserProfile entities,
    using the UserProfileRepository for data access.
    """

    def __init__(self, user_profile_repository: UserProfileRepository):
        """Initialize the service with a user profile repository.

        Args:
            user_profile_repository: Repository for UserProfile data access
        """
        self.repository = user_profile_repository

    def get_profile(self, profile_id: int) -> UserProfile:
        """Get a user profile by ID.

        Args:
            profile_id: ID of the profile to retrieve

        Returns:
            UserProfile: The requested user profile

        Raises:
            ResourceNotFoundError: If profile with the given ID is not found
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting user profile with ID {profile_id}")
        return self.repository.get_by_id(profile_id)

    def get_profile_by_label(self, label: str) -> Optional[UserProfile]:
        """Get a user profile by unique label.

        Args:
            label: Unique label of the profile to retrieve

        Returns:
            UserProfile or None: The requested profile or None if not found

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info(f"Getting user profile with label '{label}'")
        return self.repository.get_by_label(label)

    def get_all_profiles(self) -> List[UserProfile]:
        """Get all user profiles.

        Returns:
            List[UserProfile]: List of all user profiles

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting all user profiles")
        return self.repository.get_all()

    def search_profiles(self, query: str) -> List[UserProfile]:
        """Search for profiles by name or description.

        Args:
            query: Search string to look for in profile name or description

        Returns:
            List[UserProfile]: List of matching profiles

        Raises:
            ValidationError: If search query is too short
            DatabaseError: If a database error occurs
        """
        logger.info(f"Searching user profiles with query '{query}'")
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")
        return self.repository.search(query)

    def get_profiles_by_name(self, name: str) -> List[UserProfile]:
        """Find profiles by name.

        Args:
            name: Name to search for

        Returns:
            List[UserProfile]: List of matching profiles

        Raises:
            ValidationError: If name is too short
            DatabaseError: If a database error occurs
        """
        logger.info(f"Finding user profiles by name '{name}'")
        if not name or len(name.strip()) < 2:
            raise ValidationError("Name search query must be at least 2 characters")
        return self.repository.get_by_name(name)

    def get_default_profile(self) -> Optional[UserProfile]:
        """Get the default user profile if one exists.

        Returns:
            UserProfile or None: The default profile if it exists, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        logger.info("Getting default user profile")
        return self.repository.get_default_profile()

    def create_profile(
        self,
        label: str,
        name: str,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> UserProfile:
        """Create a new user profile.

        Args:
            label: Unique identifier for the profile
            name: Display name of the profile
            avatar_image: Path or URL to profile's avatar image (optional)
            description: Detailed description of the profile (optional)

        Returns:
            UserProfile: The created profile

        Raises:
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Validate input
        self._validate_profile_data(label, name, avatar_image, description)

        # Check if profile with this label already exists
        existing = self.repository.get_by_label(label)
        if existing:
            raise ValidationError(f"User profile with label '{label}' already exists")

        logger.info(f"Creating user profile with label '{label}'")
        return self.repository.create(
            label=label, name=name, avatar_image=avatar_image, description=description
        )

    def update_profile(
        self,
        profile_id: int,
        label: Optional[str] = None,
        name: Optional[str] = None,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> UserProfile:
        """Update an existing user profile.

        Args:
            profile_id: ID of the profile to update
            label: New label for the profile (optional)
            name: New name for the profile (optional)
            avatar_image: New avatar image path/URL (optional)
            description: New description (optional)

        Returns:
            UserProfile: The updated profile

        Raises:
            ResourceNotFoundError: If profile with the given ID is not found
            ValidationError: If validation fails
            DatabaseError: If a database error occurs
        """
        # Get current profile to ensure it exists
        profile = self.repository.get_by_id(profile_id)

        # Prepare update data
        update_data = {}

        if label is not None and label != profile.label:
            # Validate new label
            if not label or len(label.strip()) < 2:
                raise ValidationError(
                    "User profile label must be at least 2 characters"
                )

            # Check if the new label is already in use by another profile
            existing = self.repository.get_by_label(label)
            if existing and existing.id != profile_id:
                raise ValidationError(
                    f"User profile with label '{label}' already exists"
                )
            update_data["label"] = label

        if name is not None:
            # Validate new name
            if not name or len(name.strip()) < 1:
                raise ValidationError("User profile name cannot be empty")
            update_data["name"] = name

        if avatar_image is not None:
            # If updating avatar, delete the old one first
            if profile.avatar_image and avatar_image != profile.avatar_image:
                file_service = FileUploadService()
                file_service.delete_avatar_image(profile.avatar_image)
                logger.info(f"Deleted old avatar file: {profile.avatar_image}")
            update_data["avatar_image"] = avatar_image

        if description is not None:
            update_data["description"] = description

        if not update_data:
            # Nothing to update
            return profile

        logger.info(f"Updating user profile with ID {profile_id}")
        return self.repository.update(profile_id, **update_data)

    def delete_profile(self, profile_id: int) -> None:
        """Delete a user profile.

        Args:
            profile_id: ID of the profile to delete

        Raises:
            ResourceNotFoundError: If profile with the given ID is not found
            BusinessRuleError: If the profile cannot be deleted due to constraints
            DatabaseError: If a database error occurs
        """
        # Get current profile to ensure it exists
        profile = self.repository.get_by_id(profile_id)

        # Check if there are any chat sessions with this profile
        if hasattr(profile, "chat_sessions"):
            chat_sessions_count = profile.chat_sessions.count()
            if chat_sessions_count > 0:
                raise BusinessRuleError(
                    "Cannot delete user profile that is used in chat sessions",
                    details={"profile_id": profile_id},
                )

        # Check if this profile is set as the default in application settings
        if hasattr(profile, "default_in_settings") and profile.default_in_settings:
            raise BusinessRuleError(
                "Cannot delete user profile that is set as default in application settings",
                details={"profile_id": profile_id},
            )

        # Delete avatar file if it exists
        if profile.avatar_image:
            file_service = FileUploadService()
            file_service.delete_avatar_image(profile.avatar_image)
            logger.info(f"Deleted avatar file: {profile.avatar_image}")

        logger.info(f"Deleting user profile with ID {profile_id}")
        self.repository.delete(profile_id)

    def _validate_profile_data(
        self,
        label: str,
        name: str,
        avatar_image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Validate user profile data.

        Args:
            label: Profile label to validate
            name: Profile name to validate
            avatar_image: Profile avatar image to validate (optional)
            description: Profile description to validate (optional)

        Raises:
            ValidationError: If validation fails
        """
        errors: Dict[str, str] = {}

        # Label validation
        if not label:
            errors["label"] = "User profile label is required"
        elif len(label.strip()) < 2:
            errors["label"] = "User profile label must be at least 2 characters"

        # Name validation
        if not name:
            errors["name"] = "User profile name is required"
        elif len(name.strip()) < 1:
            errors["name"] = "User profile name cannot be empty"

        # Avatar image validation (optional)
        if avatar_image is not None and not isinstance(avatar_image, str):
            errors["avatar_image"] = "Avatar image must be a string"

        # Description validation (optional)
        if description is not None and not isinstance(description, str):
            errors["description"] = "Description must be a string"

        if errors:
            raise ValidationError("User profile validation failed", details=errors)
