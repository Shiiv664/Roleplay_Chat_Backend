"""Repository implementation for UserProfile model."""

from typing import List, Optional, Type

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_profile import UserProfile
from app.repositories.base_repository import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for UserProfile entity."""

    def _get_model_class(self) -> Type[UserProfile]:
        """Return the SQLAlchemy model class.

        Returns:
            UserProfile: The UserProfile model class
        """
        return UserProfile

    def get_by_label(self, label: str) -> Optional[UserProfile]:
        """Get user profile by unique label.

        Args:
            label: The unique label of the user profile

        Returns:
            UserProfile or None: The user profile if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            profile = (
                self.session.query(UserProfile)
                .filter(UserProfile.label == label)
                .first()
            )
            return profile
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving user profile by label '{label}'"
            )

    def get_by_name(self, name: str) -> List[UserProfile]:
        """Find user profiles by name.

        Args:
            name: The name to search for

        Returns:
            List[UserProfile]: List of matching user profiles

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(UserProfile)
                .filter(UserProfile.name.ilike(f"%{name}%"))
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error finding user profiles by name '{name}'"
            )

    def search(self, query: str) -> List[UserProfile]:
        """Search user profiles by name or description.

        Args:
            query: The search string to look for in profile name or description

        Returns:
            List[UserProfile]: List of matching user profiles

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(UserProfile)
                .filter(
                    or_(
                        UserProfile.name.ilike(f"%{query}%"),
                        UserProfile.description.ilike(f"%{query}%"),
                    )
                )
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error searching user profiles with query '{query}'"
            )

    def get_default_profile(self) -> Optional[UserProfile]:
        """Get the default user profile if it exists.

        This method queries the application_settings to find the default user profile.

        Returns:
            UserProfile or None: The default user profile if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Join with ApplicationSettings to get the default user profile
            from app.models.application_settings import ApplicationSettings

            profile = (
                self.session.query(UserProfile)
                .join(
                    ApplicationSettings,
                    ApplicationSettings.default_user_profile_id == UserProfile.id,
                )
                .first()
            )

            return profile
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving default user profile")
