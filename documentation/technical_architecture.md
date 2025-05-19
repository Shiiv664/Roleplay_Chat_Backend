# Technical Architecture Design

This document details the technical architecture for the Roleplay Chat Web App, focusing on both backend and frontend structures, state management, directory organization, and API endpoints.

## Backend Architecture

### SQLAlchemy ORM Models

The data models will be implemented using SQLAlchemy ORM, providing an object-oriented interface to the database.

#### Structure:
- `models/`
  - `base.py` - Base model class and database setup
  - `character.py` - Character model
  - `user_profile.py` - User profile model
  - `ai_model.py` - AI model model
  - `system_prompt.py` - System prompt model
  - `chat_session.py` - Chat session model
  - `message.py` - Message model
  - `application_settings.py` - Application settings model

#### Key Responsibilities:
- Define database schema through class definitions
- Define relationships between models
- Provide data validation at the model level
- Support migrations and schema changes (using Alembic)

### Repository Pattern for Data Access

The repository pattern will provide a clean abstraction for database operations, isolating SQL and ORM details.

#### Structure:
- `repositories/`
  - `base_repository.py` - Common repository operations
  - `character_repository.py` - Character table operations
  - `user_profile_repository.py` - User profile table operations
  - `ai_model_repository.py` - AI model table operations
  - `system_prompt_repository.py` - System prompt table operations
  - `chat_session_repository.py` - Chat session table operations
  - `message_repository.py` - Message table operations
  - `application_settings_repository.py` - Application settings table operations

#### Key Responsibilities:
- Implement CRUD operations for all entities
- Manage database sessions and transactions
- Handle complex queries
- Transform between domain objects and ORM models (if needed)
- Provide error handling for database operations

### Service Layer

The service layer will contain business logic, orchestrating operations between repositories and the API layer.

#### Structure:
- `services/`
  - `character_service.py` - Character-related business logic
  - `user_profile_service.py` - User profile business logic
  - `ai_model_service.py` - AI model business logic
  - `system_prompt_service.py` - System prompt business logic
  - `chat_service.py` - Chat session and messaging logic
  - `application_settings_service.py` - Settings management
  - `ai_integration_service.py` - Integration with OpenRouter API

#### Key Responsibilities:
- Business rule enforcement
- Complex operations that span multiple repositories
- Service-level validation
- Integration with external APIs (like OpenRouter)
- Events and notifications (future expansion)

### API Layer

The API layer will expose HTTP endpoints using Flask, providing a RESTful interface for the frontend.

#### Structure:
- `api/`
  - `routes/`
    - `character_routes.py` - Character API endpoints
    - `user_profile_routes.py` - User profile endpoints
    - `ai_model_routes.py` - AI model endpoints
    - `system_prompt_routes.py` - System prompt endpoints
    - `chat_routes.py` - Chat and message endpoints
    - `settings_routes.py` - Application settings endpoints
  - `middleware/` - Request processing middleware (future expansion)
  - `utils/` - API utility functions

#### Key Responsibilities:
- HTTP request handling
- Request validation
- Response formatting
- Error handling and status codes
- Authentication and authorization (future expansion)

## Frontend Architecture

### UI Components

Reusable UI components that implement the visual elements of the application.

#### Structure:
- `static/js/components/`
  - `common/` - Shared UI elements (buttons, forms, modals)
  - `character/` - Character-related components
  - `profile/` - User profile components
  - `chat/` - Chat interface components
  - `settings/` - Settings components
  - `navigation/` - Navigation and menu components

#### Key Responsibilities:
- Rendering UI elements
- Handling user interactions
- Visual styling and layout
- Component-specific state management

### API Interaction Modules

Modules that handle communication with the backend API.

#### Structure:
- `static/js/api/`
  - `character_api.js` - Character API client
  - `user_profile_api.js` - User profile API client
  - `ai_model_api.js` - AI model API client
  - `system_prompt_api.js` - System prompt API client
  - `chat_api.js` - Chat and message API client
  - `settings_api.js` - Application settings API client

#### Key Responsibilities:
- HTTP request construction
- API endpoint interaction
- Response parsing
- Error handling
- Request queuing and retries (if needed)

### Core Logic Modules

Modules that implement application logic and state management.

#### Structure:
- `static/js/core/`
  - `state/` - State management
  - `utils/` - Utility functions
  - `controllers/` - Page controllers
  - `events/` - Event handling

#### Key Responsibilities:
- Application state management
- Business logic on the frontend
- Event handling
- Data transformation and processing

## Application State Management

The application will use a simple, modular state management approach:

### Backend State:
- Database will be the source of truth
- Session state maintained through Flask sessions (if needed)
- No global application state on the backend

### Frontend State:
- Page-specific state in controllers
- Component-specific state within components
- Shared state managed through a simple state management system:
  - `static/js/core/state/store.js` - Central state management
  - Event-based state updates
  - Observers for reactive UI updates

## Directory Structure

```
/llm_roleplay_chat_client_V3/
│
├── app.py                      # Application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── models/                     # SQLAlchemy ORM models
│   ├── base.py                 # Base model and DB setup
│   ├── character.py            # Character model
│   ├── user_profile.py         # User profile model
│   ├── ai_model.py             # AI model model
│   ├── system_prompt.py        # System prompt model
│   ├── chat_session.py         # Chat session model
│   ├── message.py              # Message model
│   └── application_settings.py # Settings model
│
├── repositories/               # Repository pattern implementation
│   ├── base_repository.py      # Base repository class
│   ├── character_repository.py # Character repository
│   ├── user_profile_repository.py # User profile repository
│   └── [other repositories]
│
├── services/                   # Service Layer
│   └── [Service modules as described above]
│
├── api/                        # API Layer
│   ├── routes/
│   │   └── [Route modules as described above]
│   ├── middleware/
│   └── utils/
│
├── migrations/                 # Alembic migrations for SQLAlchemy
│
├── templates/                  # Jinja2 templates
│   ├── base.html               # Base template
│   ├── index.html              # Home page
│   ├── characters.html         # Characters page
│   ├── profiles.html           # User profiles page
│   ├── prompts.html            # System prompts page
│   ├── models.html             # AI models page
│   ├── settings.html           # Settings page
│   └── chat.html               # Chat interface
│
├── static/                     # Static assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   │   ├── components/         # UI components
│   │   ├── api/                # API clients
│   │   └── core/               # Core logic
│   └── img/                    # Images and icons
│
├── tests/                      # Test suite
│   ├── models/                 # Model tests
│   ├── repositories/           # Repository tests
│   ├── services/               # Service tests
│   └── api/                    # API tests
│
└── documentation/              # Project documentation
    ├── global_roadmap.md       # Project roadmap
    ├── database_schema.sql     # Database schema
    ├── technical_architecture.md # This document
    └── api_endpoints.md        # API documentation
```

## SQLAlchemy Implementation Details

### Model Definitions

SQLAlchemy models will be defined using the declarative base approach:

```python
# Example model definition (models/character.py)
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from .base import Base

class Character(Base):
    __tablename__ = 'character'

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    avatar_image = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="character", cascade="all, delete-orphan")
```

### Repository Pattern

The repository pattern will abstract data access operations:

```python
# Example repository implementation (repositories/base_repository.py)
class BaseRepository:
    def __init__(self, session):
        self.session = session

    def add(self, entity):
        self.session.add(entity)
        return entity

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

# Example character repository (repositories/character_repository.py)
class CharacterRepository(BaseRepository):
    def get_by_id(self, character_id):
        return self.session.query(Character).filter(Character.id == character_id).first()

    def get_all(self):
        return self.session.query(Character).all()

    def create(self, label, name, avatar_image=None, description=None):
        character = Character(
            label=label,
            name=name,
            avatar_image=avatar_image,
            description=description
        )
        return self.add(character)
```

### Database Session Management

Sessions will be managed using a context manager approach:

```python
# In utils/db.py
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from models.base import engine

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
```

## API Endpoints

### Character Endpoints
- `GET /api/characters` - List all characters
- `GET /api/characters/{id}` - Get character details
- `POST /api/characters` - Create a new character
- `PUT /api/characters/{id}` - Update a character
- `DELETE /api/characters/{id}` - Delete a character

### User Profile Endpoints
- `GET /api/profiles` - List all user profiles
- `GET /api/profiles/{id}` - Get profile details
- `POST /api/profiles` - Create a new profile
- `PUT /api/profiles/{id}` - Update a profile
- `DELETE /api/profiles/{id}` - Delete a profile

### AI Model Endpoints
- `GET /api/models` - List all AI models
- `GET /api/models/{id}` - Get model details
- `POST /api/models` - Create a new model
- `PUT /api/models/{id}` - Update a model
- `DELETE /api/models/{id}` - Delete a model

### System Prompt Endpoints
- `GET /api/prompts` - List all system prompts
- `GET /api/prompts/{id}` - Get prompt details
- `POST /api/prompts` - Create a new prompt
- `PUT /api/prompts/{id}` - Update a prompt
- `DELETE /api/prompts/{id}` - Delete a prompt

### Chat Session Endpoints
- `GET /api/sessions` - List all chat sessions
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions` - Create a new session
- `PUT /api/sessions/{id}` - Update a session
- `DELETE /api/sessions/{id}` - Delete a session
- `GET /api/sessions/character/{id}` - Get sessions for a character
- `GET /api/sessions/profile/{id}` - Get sessions for a profile

### Message Endpoints
- `GET /api/sessions/{id}/messages` - Get messages for a session
- `POST /api/sessions/{id}/messages` - Add a message to a session
- `POST /api/sessions/{id}/generate` - Generate an AI response

### Settings Endpoints
- `GET /api/settings` - Get application settings
- `PUT /api/settings` - Update application settings
