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
