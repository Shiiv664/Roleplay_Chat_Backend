# Phase 3 Part 3 Implementation Roadmap: Repository Implementation & Testing

This roadmap provides implementation guidance for the repository layer of the Roleplay Chat Web App. Following the implementation of database models in Part 1, this part focuses on building a robust data access layer through the repository pattern.

**Status Legend:**
- [ ] Not started
- [🔄] In progress
- [✓] Completed

## Introduction to the Repository Pattern

The repository pattern creates an abstraction layer between the database and the application's business logic. It provides a clean API for data access and encapsulates the data storage implementation details, making the codebase more maintainable and testable.

### Benefits of the Repository Pattern

1. **Separation of Concerns**: Isolates data access logic from business logic
2. **Testability**: Enables easier unit testing through dependency injection
3. **Consistency**: Provides uniform data access patterns across the application
4. **Maintainability**: Centralizes data access code, reducing duplication
5. **Flexibility**: Allows for changing the underlying data access implementation without affecting the rest of the application

## Core Principles for Repository Implementation

1. **Single Responsibility**: Each repository handles one domain entity
2. **Explicit Interface**: Repositories expose clear, well-defined methods
3. **Proper Error Handling**: Convert database exceptions to application-specific exceptions
4. **Transaction Management**: Support explicit transaction boundaries
5. **Performance Optimization**: Implement efficient queries and strategies
6. **Testability**: Design with unit testing in mind

## Base Repository Implementation

### Create Base Repository Class

The base repository will implement common CRUD operations that apply to all entities.

1. **Define BaseRepository Abstract Class**
   - [✓] Create `base_repository.py` with abstract interface
   - [✓] Implement session management (SQLAlchemy)
   - [✓] Define common CRUD operations signature
   - [✓] Add typing support for strict type checking

```python
# app/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.base import Base
from app.utils.exceptions import DatabaseError, ResourceNotFoundError, ValidationError

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations for all repositories."""

    def __init__(self, session: Session):
        self.session = session
        self.model_class: Type[T] = self._get_model_class()

    @abstractmethod
    def _get_model_class(self) -> Type[T]:
        """Return the SQLAlchemy model class."""
        pass

    def get_by_id(self, entity_id: int) -> T:
        """Get entity by ID."""
        try:
            entity = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()

            if not entity:
                raise ResourceNotFoundError(
                    f"{self.model_class.__name__} with ID {entity_id} not found"
                )

            return entity
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving {self.model_class.__name__}")

    def get_all(self) -> List[T]:
        """Get all entities."""
        try:
            return self.session.query(self.model_class).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving all {self.model_class.__name__}s")

    def create(self, **kwargs) -> T:
        """Create a new entity."""
        try:
            entity = self.model_class(**kwargs)
            self.session.add(entity)
            self.session.flush()  # Flush to get the ID without committing
            return entity
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ValidationError(f"A {self.model_class.__name__} with these details already exists")
            self._handle_db_exception(e, f"Error creating {self.model_class.__name__}")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error creating {self.model_class.__name__}")

    def update(self, entity_id: int, **kwargs) -> T:
        """Update an existing entity."""
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
                raise ValidationError(f"Update would create a duplicate {self.model_class.__name__}")
            self._handle_db_exception(e, f"Error updating {self.model_class.__name__}")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error updating {self.model_class.__name__}")

    def delete(self, entity_id: int) -> None:
        """Delete an entity by ID."""
        try:
            entity = self.get_by_id(entity_id)
            self.session.delete(entity)
            self.session.flush()
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error deleting {self.model_class.__name__}")

    def _handle_db_exception(self, exception: SQLAlchemyError, message: str) -> None:
        """Handle database exceptions and convert to application exceptions."""
        error_message = f"{message}: {str(exception)}"

        # Log the error with more details
        import logging
        logger = logging.getLogger(__name__)
        logger.error(error_message, exc_info=True)

        # Raise appropriate application exception
        raise DatabaseError(error_message)
```

2. **Implement Transaction Management**
   - [✓] Add transaction context management
   - [✓] Implement transaction retry logic following `transaction_management_strategy.md`
   - [✓] Add proper rollback handling

```python
# Additional methods for BaseRepository

@contextmanager
def transaction(self):
    """Transaction context manager."""
    try:
        yield
        self.session.commit()
    except Exception:
        self.session.rollback()
        raise

def with_retry(self, func, *args, max_retries=3, **kwargs):
    """Execute a function with retry logic for transient errors."""
    from sqlalchemy.exc import DBAPIError, OperationalError
    import time
    import random

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
            backoff = (2 ** retries) * 0.1
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
```

## Entity-Specific Repositories

Implement specific repositories for each model, extending the base repository.

### 1. Character Repository

1. **Implement CharacterRepository**
   - [✓] Create `character_repository.py`
   - [✓] Implement entity-specific query methods
   - [✓] Add domain-specific operations

```python
# app/repositories/character_repository.py
from typing import List, Optional
from sqlalchemy import or_

from app.models.character import Character
from app.repositories.base_repository import BaseRepository

class CharacterRepository(BaseRepository[Character]):
    """Repository for Character entity."""

    def _get_model_class(self):
        return Character

    def get_by_label(self, label: str) -> Optional[Character]:
        """Get character by unique label."""
        try:
            character = self.session.query(Character).filter(
                Character.label == label
            ).first()

            return character
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving character by label '{label}'")

    def search(self, query: str) -> List[Character]:
        """Search characters by name or description."""
        try:
            return self.session.query(Character).filter(
                or_(
                    Character.name.ilike(f"%{query}%"),
                    Character.description.ilike(f"%{query}%")
                )
            ).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error searching characters with query '{query}'")
```

### 2. UserProfile Repository

1. **Implement UserProfileRepository**
   - [ ] Create `user_profile_repository.py`
   - [ ] Implement entity-specific query methods

```python
# app/repositories/user_profile_repository.py
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_profile import UserProfile
from app.repositories.base_repository import BaseRepository

class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for UserProfile entity."""

    def _get_model_class(self):
        return UserProfile

    def get_by_label(self, label: str) -> Optional[UserProfile]:
        """Get user profile by unique label."""
        try:
            profile = self.session.query(UserProfile).filter(
                UserProfile.label == label
            ).first()

            return profile
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving user profile by label '{label}'")

    def get_default_profile(self) -> Optional[UserProfile]:
        """Get the default user profile if it exists."""
        try:
            return self.session.query(UserProfile).filter(
                UserProfile.is_default == True
            ).first()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving default user profile")
```

### 3. AIModel Repository

1. **Implement AIModelRepository**
   - [ ] Create `ai_model_repository.py`
   - [ ] Implement entity-specific query methods

```python
# app/repositories/ai_model_repository.py
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError

from app.models.ai_model import AIModel
from app.repositories.base_repository import BaseRepository

class AIModelRepository(BaseRepository[AIModel]):
    """Repository for AIModel entity."""

    def _get_model_class(self):
        return AIModel

    def get_by_model_id(self, model_id: str) -> Optional[AIModel]:
        """Get AI model by unique model ID."""
        try:
            model = self.session.query(AIModel).filter(
                AIModel.model_id == model_id
            ).first()

            return model
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving AI model by model_id '{model_id}'")

    def get_active_models(self) -> List[AIModel]:
        """Get all active AI models."""
        try:
            return self.session.query(AIModel).filter(
                AIModel.is_active == True
            ).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving active AI models")
```

### 4. SystemPrompt Repository

1. **Implement SystemPromptRepository**
   - [ ] Create `system_prompt_repository.py`
   - [ ] Implement entity-specific query methods

```python
# app/repositories/system_prompt_repository.py
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from app.models.system_prompt import SystemPrompt
from app.repositories.base_repository import BaseRepository

class SystemPromptRepository(BaseRepository[SystemPrompt]):
    """Repository for SystemPrompt entity."""

    def _get_model_class(self):
        return SystemPrompt

    def get_by_label(self, label: str) -> Optional[SystemPrompt]:
        """Get system prompt by unique label."""
        try:
            prompt = self.session.query(SystemPrompt).filter(
                SystemPrompt.label == label
            ).first()

            return prompt
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving system prompt by label '{label}'")

    def get_default_prompt(self) -> Optional[SystemPrompt]:
        """Get the default system prompt if it exists."""
        try:
            return self.session.query(SystemPrompt).filter(
                SystemPrompt.is_default == True
            ).first()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving default system prompt")
```

### 5. ChatSession Repository

1. **Implement ChatSessionRepository**
   - [ ] Create `chat_session_repository.py`
   - [ ] Implement entity-specific query methods
   - [ ] Add relationship-based operations

```python
# app/repositories/chat_session_repository.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.chat_session import ChatSession
from app.repositories.base_repository import BaseRepository

class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession entity."""

    def _get_model_class(self):
        return ChatSession

    def get_by_id_with_relations(self, session_id: int) -> Optional[ChatSession]:
        """Get chat session by ID with related entities preloaded."""
        try:
            session = self.session.query(ChatSession).options(
                joinedload(ChatSession.character),
                joinedload(ChatSession.user_profile),
                joinedload(ChatSession.ai_model),
                joinedload(ChatSession.system_prompt)
            ).filter(
                ChatSession.id == session_id
            ).first()

            if not session:
                raise ResourceNotFoundError(f"ChatSession with ID {session_id} not found")

            return session
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving chat session with ID {session_id}")

    def get_sessions_by_character_id(self, character_id: int) -> List[ChatSession]:
        """Get all chat sessions for a character."""
        try:
            return self.session.query(ChatSession).filter(
                ChatSession.character_id == character_id
            ).order_by(
                ChatSession.updated_at.desc()
            ).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving chat sessions for character ID {character_id}")

    def get_sessions_by_user_profile_id(self, profile_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user profile."""
        try:
            return self.session.query(ChatSession).filter(
                ChatSession.user_profile_id == profile_id
            ).order_by(
                ChatSession.updated_at.desc()
            ).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving chat sessions for profile ID {profile_id}")

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently updated chat sessions."""
        try:
            return self.session.query(ChatSession).order_by(
                ChatSession.updated_at.desc()
            ).limit(limit).all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving recent chat sessions")

    def update_session_timestamp(self, session_id: int) -> None:
        """Update the updated_at timestamp for a chat session."""
        try:
            session = self.get_by_id(session_id)
            session.updated_at = datetime.utcnow()
            self.session.flush()
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, f"Error updating timestamp for chat session ID {session_id}")
```

### 6. Message Repository

1. **Implement MessageRepository**
   - [ ] Create `message_repository.py`
   - [ ] Implement entity-specific query methods with performance optimizations
   - [ ] Add pagination support

```python
# app/repositories/message_repository.py
from typing import Dict, List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from app.models.message import Message
from app.repositories.base_repository import BaseRepository

class MessageRepository(BaseRepository[Message]):
    """Repository for Message entity."""

    def _get_model_class(self):
        return Message

    def get_by_chat_session_id(self, session_id: int, limit: Optional[int] = None,
                               offset: Optional[int] = None) -> List[Message]:
        """Get messages for a chat session with pagination support."""
        try:
            query = self.session.query(Message).filter(
                Message.chat_session_id == session_id
            ).order_by(Message.created_at)

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving messages for chat session ID {session_id}")

    def get_paged_messages(self, session_id: int, page: int = 1,
                          page_size: int = 50) -> Tuple[List[Message], Dict]:
        """Get paginated messages for a chat session with metadata."""
        try:
            # Get total count
            total_count = self.session.query(Message).filter(
                Message.chat_session_id == session_id
            ).count()

            # Calculate pagination
            total_pages = (total_count + page_size - 1) // page_size
            offset = (page - 1) * page_size

            # Get messages
            messages = self.session.query(Message).filter(
                Message.chat_session_id == session_id
            ).order_by(
                Message.created_at.desc()
            ).offset(offset).limit(page_size).all()

            # Pagination metadata
            pagination = {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }

            return messages, pagination
        except SQLAlchemyError as e:
            self._handle_db_exception(e, f"Error retrieving paged messages for chat session ID {session_id}")

    def create_bulk(self, messages_data: List[Dict]) -> List[Message]:
        """Create multiple messages in a single operation."""
        try:
            message_objects = [Message(**data) for data in messages_data]
            self.session.add_all(message_objects)
            self.session.flush()
            return message_objects
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, "Error creating bulk messages")
```

### 7. ApplicationSettings Repository

1. **Implement ApplicationSettingsRepository**
   - [ ] Create `application_settings_repository.py`
   - [ ] Implement singleton pattern
   - [ ] Add optimization for frequent access

```python
# app/repositories/application_settings_repository.py
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from app.models.application_settings import ApplicationSettings
from app.repositories.base_repository import BaseRepository

class ApplicationSettingsRepository(BaseRepository[ApplicationSettings]):
    """Repository for ApplicationSettings entity."""

    def _get_model_class(self):
        return ApplicationSettings

    def get_settings(self) -> Optional[ApplicationSettings]:
        """Get the application settings (singleton)."""
        try:
            # Settings should be a singleton, so get the first record
            settings = self.session.query(ApplicationSettings).first()
            return settings
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving application settings")

    def save_settings(self, **kwargs) -> ApplicationSettings:
        """Save application settings, creating or updating as needed."""
        try:
            settings = self.get_settings()

            if settings:
                # Update existing settings
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
            else:
                # Create new settings
                settings = ApplicationSettings(**kwargs)
                self.session.add(settings)

            self.session.flush()
            return settings
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, "Error saving application settings")
```

## Repository Registry

Implement a registry for dependency injection and ease of use.

1. **Create RepositoryRegistry**
   - [ ] Create `repository_registry.py`
   - [ ] Implement registry pattern

```python
# app/repositories/repository_registry.py
from sqlalchemy.orm import Session

from app.repositories.character_repository import CharacterRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.ai_model_repository import AIModelRepository
from app.repositories.system_prompt_repository import SystemPromptRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.application_settings_repository import ApplicationSettingsRepository

class RepositoryRegistry:
    """Registry of repositories for dependency injection."""

    def __init__(self, session: Session):
        self.session = session

        # Initialize repositories
        self._character_repo = None
        self._user_profile_repo = None
        self._ai_model_repo = None
        self._system_prompt_repo = None
        self._chat_session_repo = None
        self._message_repo = None
        self._app_settings_repo = None

    @property
    def character_repository(self) -> CharacterRepository:
        """Get or create character repository."""
        if self._character_repo is None:
            self._character_repo = CharacterRepository(self.session)
        return self._character_repo

    @property
    def user_profile_repository(self) -> UserProfileRepository:
        """Get or create user profile repository."""
        if self._user_profile_repo is None:
            self._user_profile_repo = UserProfileRepository(self.session)
        return self._user_profile_repo

    @property
    def ai_model_repository(self) -> AIModelRepository:
        """Get or create AI model repository."""
        if self._ai_model_repo is None:
            self._ai_model_repo = AIModelRepository(self.session)
        return self._ai_model_repo

    @property
    def system_prompt_repository(self) -> SystemPromptRepository:
        """Get or create system prompt repository."""
        if self._system_prompt_repo is None:
            self._system_prompt_repo = SystemPromptRepository(self.session)
        return self._system_prompt_repo

    @property
    def chat_session_repository(self) -> ChatSessionRepository:
        """Get or create chat session repository."""
        if self._chat_session_repo is None:
            self._chat_session_repo = ChatSessionRepository(self.session)
        return self._chat_session_repo

    @property
    def message_repository(self) -> MessageRepository:
        """Get or create message repository."""
        if self._message_repo is None:
            self._message_repo = MessageRepository(self.session)
        return self._message_repo

    @property
    def application_settings_repository(self) -> ApplicationSettingsRepository:
        """Get or create application settings repository."""
        if self._app_settings_repo is None:
            self._app_settings_repo = ApplicationSettingsRepository(self.session)
        return self._app_settings_repo
```

## Testing Repositories

Implement comprehensive tests for repository implementations, following the testing_strategy.md guidelines.

### 1. Base Repository Tests

1. **Create BaseRepositoryTests**
   - [✓] Create test fixtures
   - [✓] Test common CRUD operations
   - [✓] Test error handling

```python
# tests/repositories/test_base_repository.py
import pytest
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from unittest.mock import MagicMock, patch

from app.models.character import Character
from app.repositories.character_repository import CharacterRepository
from app.utils.exceptions import DatabaseError, ResourceNotFoundError, ValidationError

class TestBaseRepository:
    """Test base repository functionality using CharacterRepository as an example."""

    @pytest.fixture
    def character_data(self):
        """Sample character data for testing."""
        return {
            "label": "test_character",
            "name": "Test Character",
            "description": "A character for testing"
        }

    def test_get_by_id_success(self, db_session, character_data):
        """Test successful retrieval by ID."""
        # Create character
        repo = CharacterRepository(db_session)
        character = repo.create(**character_data)
        db_session.commit()

        # Test get_by_id
        retrieved = repo.get_by_id(character.id)
        assert retrieved is not None
        assert retrieved.id == character.id
        assert retrieved.label == character_data["label"]
        assert retrieved.name == character_data["name"]

    def test_get_by_id_not_found(self, db_session):
        """Test retrieval of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.get_by_id(999)  # Non-existent ID

    def test_create_success(self, db_session, character_data):
        """Test successful entity creation."""
        repo = CharacterRepository(db_session)
        character = repo.create(**character_data)
        db_session.commit()

        assert character is not None
        assert character.id is not None
        assert character.label == character_data["label"]
        assert character.name == character_data["name"]

        # Verify it was saved to the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character is not None

    def test_create_duplicate(self, db_session, character_data):
        """Test creation with duplicate unique field."""
        repo = CharacterRepository(db_session)

        # Create first character
        character = repo.create(**character_data)
        db_session.commit()

        # Try to create another with the same label
        with pytest.raises(ValidationError):
            repo.create(**character_data)

    def test_update_success(self, db_session, character_data):
        """Test successful entity update."""
        repo = CharacterRepository(db_session)

        # Create character
        character = repo.create(**character_data)
        db_session.commit()

        # Update character
        updated = repo.update(character.id, name="Updated Name")
        db_session.commit()

        assert updated.name == "Updated Name"
        assert updated.label == character_data["label"]  # Unchanged

        # Verify it was updated in the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character.name == "Updated Name"

    def test_update_not_found(self, db_session):
        """Test update of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.update(999, name="Updated Name")  # Non-existent ID

    def test_delete_success(self, db_session, character_data):
        """Test successful entity deletion."""
        repo = CharacterRepository(db_session)

        # Create character
        character = repo.create(**character_data)
        db_session.commit()

        # Delete character
        repo.delete(character.id)
        db_session.commit()

        # Verify it was deleted from the database
        db_character = db_session.query(Character).filter_by(id=character.id).first()
        assert db_character is None

    def test_delete_not_found(self, db_session):
        """Test deletion of non-existent entity."""
        repo = CharacterRepository(db_session)

        with pytest.raises(ResourceNotFoundError):
            repo.delete(999)  # Non-existent ID

    def test_get_all(self, db_session):
        """Test getting all entities."""
        repo = CharacterRepository(db_session)

        # Create multiple characters
        repo.create(label="char1", name="Character 1")
        repo.create(label="char2", name="Character 2")
        repo.create(label="char3", name="Character 3")
        db_session.commit()

        # Get all characters
        characters = repo.get_all()

        assert len(characters) >= 3

    def test_database_error_handling(self, db_session):
        """Test handling of database errors."""
        repo = CharacterRepository(db_session)

        # Mock session.query to raise SQLAlchemyError
        with patch.object(db_session, 'query', side_effect=SQLAlchemyError("Test error")):
            with pytest.raises(DatabaseError):
                repo.get_all()
```

### 2. Entity-Specific Repository Tests

1. **Create Entity-Specific Repository Tests**
   - [✓] Test specific query methods
   - [✓] Test domain-specific operations

```python
# tests/repositories/test_character_repository.py
import pytest

from app.repositories.character_repository import CharacterRepository

class TestCharacterRepository:
    """Test character-specific repository functionality."""

    @pytest.fixture
    def create_characters(self, db_session):
        """Create sample characters for testing."""
        repo = CharacterRepository(db_session)

        characters = [
            repo.create(label="char1", name="Character 1", description="First test character"),
            repo.create(label="char2", name="Character 2", description="Second test character"),
            repo.create(label="char3", name="Character 3", description="Third test character with special keywords")
        ]

        db_session.commit()
        return characters

    def test_get_by_label(self, db_session, create_characters):
        """Test retrieving a character by label."""
        repo = CharacterRepository(db_session)

        character = repo.get_by_label("char2")

        assert character is not None
        assert character.label == "char2"
        assert character.name == "Character 2"

    def test_get_by_label_not_found(self, db_session):
        """Test retrieving a non-existent character by label."""
        repo = CharacterRepository(db_session)

        character = repo.get_by_label("non_existent")

        assert character is None

    def test_search(self, db_session, create_characters):
        """Test searching characters by name or description."""
        repo = CharacterRepository(db_session)

        # Search by name
        results = repo.search("Character 1")
        assert len(results) == 1
        assert results[0].name == "Character 1"

        # Search by description
        results = repo.search("special keywords")
        assert len(results) == 1
        assert results[0].name == "Character 3"

        # Search with multiple matches
        results = repo.search("test character")
        assert len(results) == 3

        # Search with no matches
        results = repo.search("no matches")
        assert len(results) == 0
```

### 3. Transaction Management Tests

1. **Test Transaction Management**
   - [✓] Test transaction context manager
   - [✓] Test retry logic
   - [✓] Test rollback on error

```python
# tests/repositories/test_transaction_management.py
import pytest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError

from app.repositories.character_repository import CharacterRepository

class TestTransactionManagement:
    """Test transaction management features."""

    def test_transaction_commit(self, db_session):
        """Test successful transaction commit."""
        repo = CharacterRepository(db_session)

        with repo.transaction():
            character = repo.create(label="test_transaction", name="Transaction Test")

        # After successful commit, character should exist in DB
        db_character = repo.get_by_label("test_transaction")
        assert db_character is not None
        assert db_character.name == "Transaction Test"

    def test_transaction_rollback_on_error(self, db_session):
        """Test transaction rollback on error."""
        repo = CharacterRepository(db_session)

        # Should cause rollback
        try:
            with repo.transaction():
                repo.create(label="rollback_test", name="Rollback Test")
                raise ValueError("Test error to trigger rollback")
        except ValueError:
            pass

        # After rollback, character should not exist in DB
        db_character = repo.get_by_label("rollback_test")
        assert db_character is None

    def test_retry_logic(self, db_session):
        """Test retry logic for transient errors."""
        repo = CharacterRepository(db_session)

        # Mock function that fails with OperationalError twice then succeeds
        mock_create_counter = [0]
        def mock_create():
            mock_create_counter[0] += 1
            if mock_create_counter[0] <= 2:
                raise OperationalError("statement", {}, Exception("Test error"))
            return repo.create(label="retry_test", name="Retry Test")

        # Should retry and eventually succeed
        character = repo.with_retry(mock_create, max_retries=3)

        assert character is not None
        assert character.label == "retry_test"
        assert mock_create_counter[0] == 3  # Called 3 times (2 failures + 1 success)

        # Verify character was created
        db_character = repo.get_by_label("retry_test")
        assert db_character is not None

    def test_retry_logic_max_retries_exceeded(self, db_session):
        """Test retry logic when max retries is exceeded."""
        repo = CharacterRepository(db_session)

        # Mock function that always fails with OperationalError
        def mock_create():
            raise OperationalError("statement", {}, Exception("Test error"))

        # Should retry and eventually fail
        with pytest.raises(OperationalError):
            repo.with_retry(mock_create, max_retries=2)
```

### 4. Performance Testing for Repositories

1. **Create Performance Tests**
   - [ ] Test bulk operations
   - [ ] Test query optimization
   - [ ] Test for N+1 problem

```python
# tests/repositories/test_repository_performance.py
import pytest
import time

from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository

class TestRepositoryPerformance:
    """Test repository performance aspects."""

    @pytest.fixture
    def setup_chat_session_with_messages(self, db_session):
        """Create a chat session with many messages for performance testing."""
        # Create dependencies
        from app.models.character import Character
        from app.models.user_profile import UserProfile
        from app.models.ai_model import AIModel
        from app.models.system_prompt import SystemPrompt
        from app.models.chat_session import ChatSession

        character = Character(label="perf_char", name="Performance Test Character")
        profile = UserProfile(label="perf_user", name="Performance Test User")
        ai_model = AIModel(label="perf_model", name="Performance Model", model_id="perf-test-model")
        prompt = SystemPrompt(label="perf_prompt", content="Performance test prompt")

        db_session.add_all([character, profile, ai_model, prompt])
        db_session.flush()

        # Create chat session
        session = ChatSession(
            title="Performance Test Session",
            character_id=character.id,
            user_profile_id=profile.id,
            ai_model_id=ai_model.id,
            system_prompt_id=prompt.id
        )
        db_session.add(session)
        db_session.flush()

        return session

    def test_message_bulk_create_performance(self, db_session, setup_chat_session_with_messages):
        """Test bulk message creation performance."""
        repo = MessageRepository(db_session)
        session_id = setup_chat_session_with_messages.id

        # Prepare 100 message data objects
        message_data = [
            {
                "chat_session_id": session_id,
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Test message content {i}",
                "sequence": i
            }
            for i in range(100)
        ]

        # Measure performance of bulk create
        start_time = time.time()
        messages = repo.create_bulk(message_data)
        db_session.commit()
        end_time = time.time()

        # Verify results
        assert len(messages) == 100

        # Check performance
        execution_time = end_time - start_time
        assert execution_time < 0.5, f"Bulk create took {execution_time:.2f}s, expected < 0.5s"

    def test_message_pagination_performance(self, db_session, setup_chat_session_with_messages):
        """Test message pagination performance."""
        # Add 200 messages first
        message_repo = MessageRepository(db_session)
        session_id = setup_chat_session_with_messages.id

        message_data = [
            {
                "chat_session_id": session_id,
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Pagination test message {i}",
                "sequence": i
            }
            for i in range(200)
        ]

        message_repo.create_bulk(message_data)
        db_session.commit()

        # Test pagination performance
        start_time = time.time()
        messages, pagination = message_repo.get_paged_messages(session_id, page=2, page_size=50)
        end_time = time.time()

        # Verify results
        assert len(messages) == 50
        assert pagination["total_count"] == 200
        assert pagination["current_page"] == 2

        # Check performance
        execution_time = end_time - start_time
        assert execution_time < 0.1, f"Pagination query took {execution_time:.2f}s, expected < 0.1s"

    def test_eager_loading_performance(self, db_session, setup_chat_session_with_messages):
        """Test eager loading vs. lazy loading performance."""
        session_repo = ChatSessionRepository(db_session)
        session_id = setup_chat_session_with_messages.id

        # Test with lazy loading
        start_time = time.time()
        session = session_repo.get_by_id(session_id)
        # Access relationships to trigger lazy loading
        _ = session.character.name
        _ = session.user_profile.name
        _ = session.ai_model.name
        _ = session.system_prompt.content
        lazy_time = time.time() - start_time

        # Test with eager loading
        start_time = time.time()
        session = session_repo.get_by_id_with_relations(session_id)
        # Access relationships (should already be loaded)
        _ = session.character.name
        _ = session.user_profile.name
        _ = session.ai_model.name
        _ = session.system_prompt.content
        eager_time = time.time() - start_time

        # Eager loading should be faster than lazy loading
        # when accessing multiple relationships
        assert eager_time < lazy_time, (
            f"Eager loading ({eager_time:.4f}s) should be faster than "
            f"lazy loading ({lazy_time:.4f}s)"
        )
```

## Performance Optimization

Apply performance optimizations to repositories based on performance_optimization_strategy.md.

### 1. Indexing Strategy

We will not do this for now.

### 2. Query Optimization Techniques

We will not do this for now.

### 3. Caching Strategy

- [ ] Implement in-memory caching for frequently accessed data
- [ ] Add cache invalidation on updates

```python
# Add caching to the ApplicationSettingsRepository
from functools import lru_cache

class ApplicationSettingsRepository(BaseRepository[ApplicationSettings]):
    def __init__(self, session: Session):
        super().__init__(session)
        # Create a method-specific cache that's bound to this instance
        self._get_settings = lru_cache(maxsize=1)(self._get_settings_impl)

    def _get_model_class(self):
        return ApplicationSettings

    def _get_settings_impl(self) -> Optional[ApplicationSettings]:
        """Internal implementation to be cached."""
        try:
            return self.session.query(ApplicationSettings).first()
        except SQLAlchemyError as e:
            self._handle_db_exception(e, "Error retrieving application settings")

    def get_settings(self) -> Optional[ApplicationSettings]:
        """Get the application settings with caching."""
        return self._get_settings()

    def save_settings(self, **kwargs) -> ApplicationSettings:
        """Save application settings and invalidate cache."""
        try:
            settings = self._get_settings()

            if settings:
                # Update existing settings
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
            else:
                # Create new settings
                settings = ApplicationSettings(**kwargs)
                self.session.add(settings)

            self.session.flush()

            # Invalidate cache
            self._get_settings.cache_clear()

            return settings
        except SQLAlchemyError as e:
            self.session.rollback()
            self._handle_db_exception(e, "Error saving application settings")
```

## Implementation Checklist

Follow this checklist to ensure comprehensive repository implementation:

1. **Base Repository**
   - [✓] Implement CRUD operations
   - [✓] Add proper error handling
   - [✓] Implement transaction management
   - [✓] Add retry logic for transient errors

2. **Entity-Specific Repositories**
   - [✓] Character repository
   - [✓] UserProfile repository
   - [✓] AIModel repository
   - [✓] SystemPrompt repository
   - [ ] ChatSession repository
   - [ ] Message repository
   - [ ] ApplicationSettings repository

3. **Repository Registry**
   - [ ] Implement registry pattern
   - [ ] Add lazy initialization

4. **Testing**
   - [✓] Unit tests for base repository
   - [✓] Unit tests for entity-specific repositories (Character, UserProfile, AIModel, SystemPrompt)
   - [✓] Transaction management tests
   - [ ] Performance tests

5. **Performance Optimization**
   We will not do this for now.

## Success Criteria

The repository implementation will be considered successful when:

1. All repositories are implemented with proper error handling
2. Unit tests cover at least 90% of repository code
3. Transaction management is properly implemented and tested
4. Integration with the error handling strategy is complete
5. Repository registry provides a clean API for service layer

## Project Structure

```
/app
  /repositories
    __init__.py
    base_repository.py
    repository_registry.py
    character_repository.py
    user_profile_repository.py
    ai_model_repository.py
    system_prompt_repository.py
    chat_session_repository.py
    message_repository.py
    application_settings_repository.py

/tests
  /repositories
    __init__.py
    test_base_repository.py
    test_character_repository.py
    test_user_profile_repository.py
    test_ai_model_repository.py
    test_system_prompt_repository.py
    test_chat_session_repository.py
    test_message_repository.py
    test_application_settings_repository.py
    test_transaction_management.py
    test_repository_performance.py
```

## Implementation Order

For smooth implementation and dependency management, follow this order:

1. Base repository with common functionality
2. Simple repositories: Character, UserProfile, AIModel, SystemPrompt
3. Repositories with relationships: ChatSession, Message
4. Specialized repositories: ApplicationSettings
5. Repository registry for dependency injection
6. Unit tests for each repository
7. Performance optimizations and tests

This implementation roadmap provides a complete guide for developing the repository layer of the Roleplay Chat Web App. By following these guidelines, the application will have a robust data access layer that supports the business logic while maintaining proper separation of concerns and testability.
