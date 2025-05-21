# LLM Roleplay Chat Client

A roleplay chat client application that allows users to have conversations with AI characters using various LLM models.

## Features

- Create and customize AI characters with unique personalities
- Manage user profiles for different conversation contexts
- Support for multiple AI models (OpenAI GPT, Claude, Llama, etc.)
- System prompt templates for consistent character behavior
- Conversation history and management
- SQLAlchemy ORM for database interaction

## Technology Stack

- **Backend**: Python with SQLAlchemy ORM
- **Database**: SQLite (development), PostgreSQL (production recommended)
- **Dependency Management**: Poetry
- **Migration Tool**: Alembic
- **Code Quality**: Black, isort, flake8, mypy

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Poetry (dependency management)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd llm_roleplay_chat_client_V3
   ```

2. Install dependencies with Poetry:
   ```bash
   # Configure Poetry to create virtual environment in project directory
   poetry config virtualenvs.in-project true

   # Install dependencies
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Initialize the database:
   ```bash
   # Create database without sample data
   python scripts/db_init.py

   # Create database with sample data (recommended for development)
   python scripts/db_init.py --sample-data
   ```

5. Install pre-commit hooks (for development):
   ```bash
   poetry run pre-commit install
   ```

6. Run the server:
   ```bash
   # Method 1: Using Python directly
   poetry run python app.py

   # Method 2: Using Flask CLI
   export FLASK_APP=app.py  # On Windows: set FLASK_APP=app.py
   export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
   poetry run flask run

   # Method 3: Using Flask CLI with host/port options
   poetry run flask run --host=0.0.0.0 --port=8000
   ```

   The server will be available at:
   - Default URL: http://127.0.0.1:5000/ (Method 2)
   - Custom URL: http://127.0.0.1:8000/ (Method 3 example)
   - Network accessible: http://0.0.0.0:8000/ (Method 3 example)

### Development Workflow

1. Run migrations:
   ```bash
   # Generate migration (after model changes)
   alembic revision --autogenerate -m "description"

   # Apply migrations
   alembic upgrade head
   ```

2. Code quality checks:
   ```bash
   # Run formatters
   poetry run black .
   poetry run isort .

   # Run linters
   poetry run flake8

   # Run type checking
   poetry run mypy app
   ```

3. Running tests:
   ```bash
   # Run all tests
   poetry run pytest

   # Run tests with verbose output
   poetry run pytest -v

   # Run tests for a specific module
   poetry run pytest tests/models/test_character.py

   # Run a specific test
   poetry run pytest tests/models/test_character.py::test_character_initialization

   # Run tests with coverage report
   poetry run pytest --cov=app

   # Run tests with coverage report and generate HTML report
   poetry run pytest --cov=app --cov-report=html
   ```

## Project Structure

```
app/
  ├── api/                # API endpoints
  ├── models/             # SQLAlchemy models
  │   ├── base.py         # Base model configuration
  │   ├── character.py    # Character model
  │   ├── user_profile.py # User profile model
  │   └── ...
  ├── repositories/       # Data access layer
  ├── services/           # Business logic
  └── utils/              # Utility functions
      └── db.py           # Database connection

alembic/                  # Database migrations
  └── versions/           # Migration versions

scripts/                  # Utility scripts
  ├── db_init.py          # Database initialization
  └── generate_test_data.py # Sample data generation

tests/                    # Test suite
  ├── models/             # Model tests
  ├── repositories/       # Repository tests
  └── ...
```

## Documentation

Additional documentation is available in the `documentation/` directory:

- [Technical Architecture](documentation/technical_architecture.md)
- [Database Schema](documentation/database_schema.sql)
- [Global Roadmap](documentation/global_roadmap.md)
- [Testing Strategy](documentation/testing_strategy.md)
- [Phase 3 Database Testing Roadmap](documentation/phase3_part2_database_testing_roadmap.md)

### API Documentation

- **API Documentation UI**: When the server is running, access the interactive Swagger UI at:
  - http://localhost:5000/api/v1/docs

- **OpenAPI Export**: Generate an OpenAPI specification file for frontend integration:
  - [OpenAPI Export Usage Guide](documentation/api/openapi_usage.md) (includes instructions for generating client code)
  - Use the script at `scripts/export_openapi.py` to export a specification file
