"""Repository implementation for Character model."""

from typing import List, Optional, Type

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app.models.character import Character
from app.repositories.base_repository import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    """Repository for Character entity."""

    def _get_model_class(self) -> Type[Character]:
        """Return the SQLAlchemy model class.

        Returns:
            Character: The Character model class
        """
        return Character

    def get_by_label(self, label: str) -> Optional[Character]:
        """Get character by unique label.

        Args:
            label: The unique label of the character

        Returns:
            Character or None: The character if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            character = (
                self.session.query(Character).filter(Character.label == label).first()
            )

            return character
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving character by label '{label}'"
            )

    def search(self, query: str) -> List[Character]:
        """Search characters by name or description.

        Args:
            query: The search string to look for in character name or description

        Returns:
            List[Character]: List of matching characters

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(Character)
                .filter(
                    or_(
                        Character.name.ilike(f"%{query}%"),
                        Character.description.ilike(f"%{query}%"),
                    )
                )
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error searching characters with query '{query}'"
            )
