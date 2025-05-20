"""Repository implementation for SystemPrompt model."""

from typing import List, Optional, Type

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app.models.system_prompt import SystemPrompt
from app.repositories.base_repository import BaseRepository


class SystemPromptRepository(BaseRepository[SystemPrompt]):
    """Repository for SystemPrompt entity."""

    def _get_model_class(self) -> Type[SystemPrompt]:
        """Return the SQLAlchemy model class.

        Returns:
            SystemPrompt: The SystemPrompt model class
        """
        return SystemPrompt

    def get_by_label(self, label: str) -> Optional[SystemPrompt]:
        """Get system prompt by unique label.

        Args:
            label: The unique label of the system prompt

        Returns:
            SystemPrompt or None: The system prompt if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            prompt = (
                self.session.query(SystemPrompt)
                .filter(SystemPrompt.label == label)
                .first()
            )
            return prompt
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving system prompt by label '{label}'"
            )

    def search(self, query: str) -> List[SystemPrompt]:
        """Search system prompts by label or content.

        Args:
            query: The search string to look for in prompt label or content

        Returns:
            List[SystemPrompt]: List of matching system prompts

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(SystemPrompt)
                .filter(
                    or_(
                        SystemPrompt.label.ilike(f"%{query}%"),
                        SystemPrompt.content.ilike(f"%{query}%"),
                    )
                )
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error searching system prompts with query '{query}'"
            )

    def get_default_prompt(self) -> Optional[SystemPrompt]:
        """Get the default system prompt if it exists.

        This method queries the application_settings to find the default system prompt.

        Returns:
            SystemPrompt or None: The default system prompt if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Join with ApplicationSettings to get the default system prompt
            from app.models.application_settings import ApplicationSettings

            prompt = (
                self.session.query(SystemPrompt)
                .join(
                    ApplicationSettings,
                    ApplicationSettings.default_system_prompt_id == SystemPrompt.id,
                )
                .first()
            )

            return prompt
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving default system prompt")
