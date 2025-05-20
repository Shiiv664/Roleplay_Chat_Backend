"""Test fixtures and configuration for pytest."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.ai_model import AIModel
from app.models.application_settings import ApplicationSettings
from app.models.base import Base
from app.models.character import Character
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.models.system_prompt import SystemPrompt
from app.models.user_profile import UserProfile


@pytest.fixture(scope="session")
def db_engine():
    """Create a SQLAlchemy engine connected to an in-memory SQLite database.

    Returns:
        Engine: SQLAlchemy engine instance.
    """
    # Enable foreign key support in SQLite
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable foreign key constraints
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a SQLAlchemy session for testing.

    Args:
        db_engine: SQLAlchemy engine fixture.

    Returns:
        Session: SQLAlchemy session for database operations.
    """
    SessionFactory = sessionmaker(bind=db_engine)
    session = SessionFactory()

    yield session

    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


# Factory fixtures for creating test data
@pytest.fixture
def create_character():
    """Factory function to create a Character instance for testing.

    Returns:
        Callable: Factory function that creates a Character instance.
    """

    def _create_character(
        label="test_character",
        name="Test Character",
        description="A test character description",
        avatar_image=None,
    ):
        return Character(
            label=label, name=name, description=description, avatar_image=avatar_image
        )

    return _create_character


@pytest.fixture
def create_user_profile():
    """Factory function to create a UserProfile instance for testing.

    Returns:
        Callable: Factory function that creates a UserProfile instance.
    """

    def _create_user_profile(
        label="test_profile",
        name="Test User",
        description="A test user profile",
        avatar_image=None,
    ):
        return UserProfile(
            label=label, name=name, description=description, avatar_image=avatar_image
        )

    return _create_user_profile


@pytest.fixture
def create_ai_model():
    """Factory function to create an AIModel instance for testing.

    Returns:
        Callable: Factory function that creates an AIModel instance.
    """

    def _create_ai_model(
        label="test_model",
        description="A test AI model",
    ):
        return AIModel(
            label=label,
            description=description,
        )

    return _create_ai_model


@pytest.fixture
def create_system_prompt():
    """Factory function to create a SystemPrompt instance for testing.

    Returns:
        Callable: Factory function that creates a SystemPrompt instance.
    """

    def _create_system_prompt(
        label="test_prompt",
        content="This is a test system prompt content",
    ):
        return SystemPrompt(label=label, content=content)

    return _create_system_prompt


# Dependent entity fixtures that require session for foreign keys
@pytest.fixture
def create_chat_session(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
):
    """Factory function to create a ChatSession instance for testing.

    Args:
        db_session: SQLAlchemy session fixture.
        create_character: Character factory fixture.
        create_user_profile: UserProfile factory fixture.
        create_ai_model: AIModel factory fixture.
        create_system_prompt: SystemPrompt factory fixture.

    Returns:
        Callable: Factory function that creates a ChatSession instance.
    """

    def _create_chat_session(
        character=None,
        user_profile=None,
        ai_model=None,
        system_prompt=None,
    ):
        # Create and add parent entities if not provided
        if not character:
            character = create_character()
            db_session.add(character)

        if not user_profile:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_profile_{time.time()}"
            user_profile = create_user_profile(label=unique_label)
            db_session.add(user_profile)

        if not ai_model:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_model_{time.time()}"
            ai_model = create_ai_model(label=unique_label)
            db_session.add(ai_model)

        if not system_prompt:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_prompt_{time.time()}"
            system_prompt = create_system_prompt(label=unique_label)
            db_session.add(system_prompt)

        db_session.flush()  # Ensure IDs are generated

        return ChatSession(
            character_id=character.id,
            user_profile_id=user_profile.id,
            ai_model_id=ai_model.id,
            system_prompt_id=system_prompt.id,
        )

    return _create_chat_session


@pytest.fixture
def create_message(db_session, create_chat_session):
    """Factory function to create a Message instance for testing.

    Args:
        db_session: SQLAlchemy session fixture.
        create_chat_session: ChatSession factory fixture.

    Returns:
        Callable: Factory function that creates a Message instance.
    """

    def _create_message(content="Test message content", role="user", chat_session=None):
        # Create and add chat session if not provided
        if not chat_session:
            chat_session = create_chat_session()
            db_session.add(chat_session)
            db_session.flush()  # Ensure ID is generated

        return Message(content=content, role=role, chat_session_id=chat_session.id)

    return _create_message


@pytest.fixture
def create_application_settings(
    db_session,
    create_character,
    create_user_profile,
    create_ai_model,
    create_system_prompt,
):
    """Factory function to create an ApplicationSettings instance for testing.

    Args:
        db_session: SQLAlchemy session fixture.
        create_character: Character factory fixture.
        create_user_profile: UserProfile factory fixture.
        create_ai_model: AIModel factory fixture.
        create_system_prompt: SystemPrompt factory fixture.

    Returns:
        Callable: Factory function that creates an ApplicationSettings instance.
    """

    def _create_application_settings(
        default_character=None,
        default_user_profile=None,
        default_ai_model=None,
        default_system_prompt=None,
    ):
        # Create and add parent entities if not provided
        if not default_character:
            default_character = create_character()
            db_session.add(default_character)

        if not default_user_profile:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_profile_{time.time()}"
            default_user_profile = create_user_profile(label=unique_label)
            db_session.add(default_user_profile)

        if not default_ai_model:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_model_{time.time()}"
            default_ai_model = create_ai_model(label=unique_label)
            db_session.add(default_ai_model)

        if not default_system_prompt:
            # Create with a unique label based on current time
            import time

            unique_label = f"test_prompt_{time.time()}"
            default_system_prompt = create_system_prompt(label=unique_label)
            db_session.add(default_system_prompt)

        db_session.flush()  # Ensure IDs are generated

        return ApplicationSettings(
            default_character_id=default_character.id,
            default_user_profile_id=default_user_profile.id,
            default_ai_model_id=default_ai_model.id,
            default_system_prompt_id=default_system_prompt.id,
        )

    return _create_application_settings


@pytest.fixture
def app():
    """Create a Flask application for testing.

    Returns:
        Flask: Flask application configured for testing.
    """
    # Create a Flask app manually for testing
    from flask import Flask

    from app.api import api_bp

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "localhost.localdomain"

    # Register the API blueprint
    app.register_blueprint(api_bp)

    return app


@pytest.fixture
def client(app):
    """Create a Flask test client.

    Args:
        app: Flask application fixture.

    Returns:
        FlaskClient: Flask test client for making requests.
    """
    with app.test_client() as client:
        with app.app_context():
            yield client
