# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Database
```bash
# Initialize database
python scripts/db_init.py --sample-data

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run the application
PYTHONPATH=. poetry run python ./app.py
poetry run flask run --host=0.0.0.0 --port=8000
```

### Code Quality and Testing
```bash
# Format code
poetry run black .
poetry run isort .

# Lint and type check
poetry run flake8
poetry run mypy app

# Run tests
poetry run pytest
poetry run pytest -v
poetry run pytest tests/models/test_character.py
poetry run pytest tests/models/test_character.py::test_character_initialization
poetry run pytest --cov=app --cov-report=html
```

## Architecture Overview

### Layer Architecture
The application follows a clean layered architecture:

- **API Layer** (`app/api/`): Flask-RESTX endpoints with namespaces for each resource
- **Service Layer** (`app/services/`): Business logic and validation
- **Repository Layer** (`app/repositories/`): Data access with BaseRepository pattern
- **Model Layer** (`app/models/`): SQLAlchemy models with Base and TimestampMixin

### Key Patterns
- **Repository Pattern**: All data access goes through repositories that inherit from BaseRepository
- **Service Pattern**: Business logic is encapsulated in service classes
- **Global Error Handling**: Centralized exception handling via Flask error handlers
- **Custom Exception Hierarchy**: ValidationError, ResourceNotFoundError, DatabaseError, etc.

### Database Architecture
- SQLAlchemy ORM with Alembic migrations
- Base model with to_dict/from_dict methods
- TimestampMixin for created_at/updated_at fields
- Generic BaseRepository with CRUD operations

### API Structure
- Flask-RESTX with automatic OpenAPI documentation at `/api/v1/docs`
- Consistent response format with success/error fields
- Namespaced endpoints (characters, user-profiles, ai-models, etc.)

## Development Guidelines

Follow these principles when modifying or adding code:
- Maintain modular structure with clear separation of concerns
- Follow Python PEP 8 style guide
- Write testable code with appropriate error handling
- Ensure security by validating input and using parameterized queries
- Maintain consistency in coding style and architecture
- Reference the testing_strategy.md file so we make sure to always test every new code properly and update the test scripts when necessary
- Reference the error_handling_strategy.md file so we make sure to always handle errors properly

## Development Approach

The development of this project follows a flexible approach:
1. I work independently and do not require formal milestones, deliverables, or strict timelines
2. Focus is on quality code and iterative development
3. Roadmaps are helpful as general guidance but not as rigid constraints, except when technical descriptions are provided
4. Adaptability and creative problem-solving are prioritized over bureaucratic processes
