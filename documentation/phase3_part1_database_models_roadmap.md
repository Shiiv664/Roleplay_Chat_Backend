# Phase 3 Part 1 Implementation Roadmap: Database Models & Setup

This roadmap provides implementation guidance for the database models and initial SQLAlchemy setup for the Roleplay Chat Web App. It is the first part of the Phase 3 implementation, focusing on building the foundation of the data layer.

**Status Legend:**
- [ ] Not started
- [🔄] In progress
- [✓] Completed

## Database Setup with SQLAlchemy ORM

### Database Technology Stack

1. **ORM Framework**
   - **SQLAlchemy** (version >= 2.0)
   - Leverage modern SQLAlchemy 2.x features and typing support
   - Use the explicit SQL syntax introduced in 2.0 (vs. legacy query style)

2. **Database Engine**
   - **Development & Testing**: SQLite
     - Development connection string: `sqlite:///./app.db`
     - Testing connection string: `sqlite:///:memory:` for in-memory testing
   - **Production Recommendation**: PostgreSQL (for future scalability)

3. **Migration Tool**
   - **Alembic** (latest stable version)
   - Configure via `alembic.ini` and `env.py`
   - Auto-generate migrations with manual review and editing
   - Follow the database schema evolution strategy outlined in `database_schema_evolution_strategy.md`

### Implementation Steps

1. **Create Base SQLAlchemy Configuration**
   - [✓] Set up SQLAlchemy engine connection to SQLite
   - [✓] Configure Base declarative class
   - [✓] Implement session management utilities
   - [✓] Add Alembic integration for migrations

2. **Implement Database Initialization Script**
   - [✓] Create script to initialize database if not exists
   - [✓] Set up initial migration
   - [✓] Add database version tracking
   - [ ] Create script for generating sample data


## SQLAlchemy Models Implementation

Follow the structure defined in `technical_architecture.md` under "SQLAlchemy ORM Models" section and implement the data model based on the schema defined in `database_schema.sql`.

### Implementation Order

Implement models in this dependency order:

1. **Base Model (models/base.py)**
   - [✓] Define `Base` class from SQLAlchemy declarative base
   - [✓] Set up common model mixin with timestamps if needed
   - [✓] Configure metadata

2. **Independent Entity Models**
   - [✓] Character model (models/character.py)
   - [✓] UserProfile model (models/user_profile.py)
   - [✓] AIModel model (models/ai_model.py)
   - [✓] SystemPrompt model (models/system_prompt.py)

3. **Dependent Entity Models**
   - [✓] ChatSession model (models/chat_session.py) - references characters, profiles, models, prompts
   - [✓] Message model (models/message.py) - references chat sessions
   - [✓] ApplicationSettings model (models/application_settings.py) - references default entities

### Model Implementation Details

For each model:
- [ ] Define table name and columns with appropriate types following the definitions in `database_schema.sql`
- [ ] Add constraints (unique, non-null, etc.) as specified in `database_schema.sql`
- [ ] Implement relationships between models according to foreign key relationships in `database_schema.sql`
- [ ] Add any model-specific methods
- [ ] Set up validation at the SQLAlchemy model level

## Project Setup with Poetry

Use Poetry for dependency management, virtual environments, and packaging as specified in `dependencies_management_strategy.md`.

### Poetry Setup

1. **Initialize Project with Poetry**
   - [✓] Ensure Poetry is installed (`pip install poetry` or follow the [official installation instructions](https://python-poetry.org/docs/#installation))
   - [✓] Run `poetry init` to create initial pyproject.toml (if not already exists)
   - [✓] Configure basic project information (name, version, description, author)

2. **Configure Core Dependencies**
   - [✓] Add SQLAlchemy: `poetry add sqlalchemy>=2.0.0`
   - [✓] Add Alembic: `poetry add alembic`
   - [✓] Add other core dependencies:
     ```bash
     poetry add flask>=3.0.0 pydantic>=2.0.0 structlog python-dotenv requests
     ```

3. **Configure Development Dependencies**
   - [✓] Add code quality tools:
     ```bash
     poetry add --group dev black isort flake8 flake8-bugbear flake8-comprehensions flake8-docstrings mypy pre-commit
     ```

4. **Set Up Virtual Environment**
   - [ ] Configure Poetry to create a virtual environment in the project directory: `poetry config virtualenvs.in-project true`
   - [ ] Initialize virtual environment: `poetry install`
   - [ ] Document environment activation: `poetry shell` or `poetry run [command]`

5. **Configure pyproject.toml**
   - [✓] Add tool configurations for code formatting and linting tools:
     ```toml
     [tool.black]
     line-length = 88
     target-version = ["py310"]
     include = '\.pyi?$'
     
     [tool.isort]
     profile = "black"
     line_length = 88
     multi_line_output = 3
     
     [tool.mypy]
     python_version = "3.10"
     disallow_untyped_defs = true
     disallow_incomplete_defs = true
     check_untyped_defs = true
     disallow_untyped_decorators = true
     no_implicit_optional = true
     strict_optional = true
     warn_redundant_casts = true
     warn_return_any = true
     warn_unused_ignores = true
     
     ```

6. **Create Project Structure**
   - [✓] Set up initial directory structure:
     ```bash
     mkdir -p app/{models,repositories,services,api,utils} scripts alembic
     ```

## Code Quality Tools Setup

Implement code quality tools to ensure consistent code style and quality:

1. **Configure Pre-commit Hooks**
   - [✓] Create `.pre-commit-config.yaml` file for local git hooks:
     ```yaml
     repos:
     - repo: local
       hooks:
       - id: trailing-whitespace
         name: Trim trailing whitespace
         entry: poetry run trailing-whitespace-fixer
         language: system
         types: [text]
       
       - id: end-of-file-fixer
         name: Fix end of files
         entry: poetry run end-of-file-fixer
         language: system
         types: [text]
       
       - id: black
         name: black
         entry: poetry run black
         language: system
         types: [python]
       
       - id: isort
         name: isort
         entry: poetry run isort
         language: system
         types: [python]
       
       - id: flake8
         name: flake8
         entry: poetry run flake8
         language: system
         types: [python]
     ```
   - [✓] Install required tools for hooks: `poetry add --group dev pre-commit black isort flake8 flake8-bugbear flake8-comprehensions flake8-docstrings`
   - [ ] Install pre-commit hooks: `poetry run pre-commit install`

2. **Configure Flake8**
   - [✓] Create `.flake8` configuration file:
     ```ini
     [flake8]
     max-line-length = 88
     extend-ignore = E203
     exclude = .git,__pycache__,dist,build,.venv,alembic
     ```

3. **Type Checking with MyPy**
   - [ ] Create basic stubs and type definitions
   - [ ] Add type hints to all model classes
   - [ ] Implement type checking in CI workflow for future integration

## Project Structure

The implementation should follow this organizational pattern:

```
/models
  base.py
  character.py
  user_profile.py
  ...

/tests
  /models
    test_base.py
    test_character.py
    ...
  
/scripts
  db_init.py
  generate_test_data.py
  
/alembic
  env.py
  versions/
```

This Part 1 roadmap focuses on building the data model foundation and project setup needed before implementing repositories, services, and API endpoints in subsequent roadmap parts.

## Getting Started Checklist

1. **Environment Setup**
   - [✓] Install Python 3.10 or higher
   - [✓] Install Poetry
   - [✓] Clone repository
   - [ ] Run `poetry install`
   - [ ] Activate virtual environment with `poetry shell`

2. **Initial Development**
   - [✓] Create SQLAlchemy Base configuration
   - [✓] Implement first model (likely the base model)
   - [ ] Run initial migration with Alembic
   - [ ] Verify model creation in SQLite database

3. **Documentation**
   - [ ] Document setup process in README.md
   - [ ] Create API documentation templates
   - [ ] Document data model relationships