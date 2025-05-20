"""Base repository implementation providing common data access functionality."""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generic, List, Type, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.base import Base
from app.utils.exceptions import DatabaseError, ResourceNotFoundError, ValidationError

# Type variable that is bound to Base
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations for all repositories."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.model_class: Type[T] = self._get_model_class()

    @abstractmethod
    def _get_model_class(self) -> Type[T]:
        """Return the SQLAlchemy model class.

        This method must be implemented by subclasses to specify which
        model the repository is responsible for.

        Returns:
            SQLAlchemy model class
        """
        pass

    def get_by_id(self, entity_id: int) -> T:
        """Get entity by ID.

        Args:
            entity_id: The primary key of the entity

        Returns:
            Entity instance

        Raises:
            ResourceNotFoundError: If entity with given ID is not found
            DatabaseError: If a database error occurs
        """
        try:
            entity = (
                self.session.query(self.model_class)
                .filter(self.model_class.id == entity_id)
                .first()
            )

            if not entity:
                raise ResourceNotFoundError(
                    f"{self.model_class.__name__} with ID {entity_id} not found"
                )

            return entity
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving {self.model_class.__name__}"
            )

    def get_all(self) -> List[T]:
        """Get all entities.

        Returns:
            List of all entities

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.session.query(self.model_class).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(
                e, f"Error retrieving all {self.model_class.__name__}s"
            )

    def create(self, **kwargs) -> T:
        """Create a new entity.

        Args:
            **kwargs: Entity attributes

        Returns:
            Created entity

        Raises:
            ValidationError: If creation violates constraints
            DatabaseError: If a database error occurs
        """
        try:
            entity = self.model_class(**kwargs)
            self.session.add(entity)
            self.session.flush()  # Flush to get the ID without committing
            return entity
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ValidationError(
                    f"A {self.model_class.__name__} with these details already exists"
                )
            self._handle_db_exception(e, f"Error creating {self.model_class.__name__}")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error creating {self.model_class.__name__}")

    def update(self, entity_id: int, **kwargs) -> T:
        """Update an existing entity.

        Args:
            entity_id: The primary key of the entity
            **kwargs: Entity attributes to update

        Returns:
            Updated entity

        Raises:
            ResourceNotFoundError: If entity with given ID is not found
            ValidationError: If update violates constraints
            DatabaseError: If a database error occurs
        """
        try:
            entity = self.get_by_id(entity_id)

            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            self.session.flush()
            return entity
        except ResourceNotFoundError:
            raise
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ValidationError(
                    f"Update would create a duplicate {self.model_class.__name__}"
                )
            self._handle_db_exception(e, f"Error updating {self.model_class.__name__}")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error updating {self.model_class.__name__}")

    def delete(self, entity_id: int) -> None:
        """Delete an entity by ID.

        Args:
            entity_id: The primary key of the entity

        Raises:
            ResourceNotFoundError: If entity with given ID is not found
            DatabaseError: If a database error occurs
        """
        try:
            entity = self.get_by_id(entity_id)
            self.session.delete(entity)
            self.session.flush()
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error deleting {self.model_class.__name__}")

    @contextmanager
    def transaction(self):
        """Transaction context manager.

        Usage:
            with repository.transaction():
                # operations within transaction
        """
        try:
            yield
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def with_retry(self, func, *args, max_retries=3, **kwargs):
        """Execute a function with retry logic for transient errors.

        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function

        Raises:
            Exception: Re-raises the exception if all retries fail
        """
        import logging
        import random
        import time

        from sqlalchemy.exc import DBAPIError, OperationalError

        logger = logging.getLogger(__name__)
        retry_on = (DBAPIError, OperationalError)
        retries = 0

        while True:
            try:
                with self.transaction():
                    return func(*args, **kwargs)
            except retry_on as e:
                retries += 1
                if retries > max_retries:
                    raise

                # Exponential backoff with jitter
                backoff = (2**retries) * 0.1
                jitter = random.uniform(0, 0.1)
                time.sleep(backoff + jitter)

                # Log retry attempt
                logger.warning(
                    f"Retrying operation after error: {str(e)} "
                    f"(attempt {retries}/{max_retries})"
                )
            except Exception:
                # Non-retryable exceptions are re-raised immediately
                raise

    def _handle_db_exception(self, exception: SQLAlchemyError, message: str) -> None:
        """Handle database exceptions and convert to application exceptions.

        Args:
            exception: SQLAlchemy exception
            message: Error message

        Raises:
            DatabaseError: Converted application-specific exception
        """
        error_message = f"{message}: {str(exception)}"

        # Log the error with more details
        import logging

        logger = logging.getLogger(__name__)
        logger.error(error_message, exc_info=True)

        # Raise appropriate application exception
        raise DatabaseError(error_message)
