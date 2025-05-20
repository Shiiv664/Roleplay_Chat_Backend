"""Repository implementation for AIModel model."""

from typing import List, Optional, Type

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app.models.ai_model import AIModel
from app.repositories.base_repository import BaseRepository


class AIModelRepository(BaseRepository[AIModel]):
    """Repository for AIModel entity."""

    def _get_model_class(self) -> Type[AIModel]:
        """Return the SQLAlchemy model class.

        Returns:
            AIModel: The AIModel model class
        """
        return AIModel

    def get_by_label(self, label: str) -> Optional[AIModel]:
        """Get AI model by unique label.

        Args:
            label: The unique label of the AI model

        Returns:
            AIModel or None: The AI model if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            model = self.session.query(AIModel).filter(AIModel.label == label).first()
            return model
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving AI model by label '{label}'"
            )

    def search(self, query: str) -> List[AIModel]:
        """Search AI models by label or description.

        Args:
            query: The search string to look for in model label or description

        Returns:
            List[AIModel]: List of matching AI models

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return (
                self.session.query(AIModel)
                .filter(
                    or_(
                        AIModel.label.ilike(f"%{query}%"),
                        AIModel.description.ilike(f"%{query}%"),
                    )
                )
                .all()
            )
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error searching AI models with query '{query}'"
            )
