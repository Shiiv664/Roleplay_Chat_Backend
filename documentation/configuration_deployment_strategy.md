# Configuration & Deployment Strategy

This document outlines the approach for managing configuration and deployment of the Roleplay Chat Web App. It provides guidelines for organizing configuration parameters, managing environment-specific settings, and handling sensitive information.

## Core Principles

1. **Separation of Concerns**: Keep code separate from configuration
2. **Environment Awareness**: Support different environments (development, testing, production)
3. **Security**: Protect sensitive information like API keys and credentials
4. **Simplicity**: Keep configuration easy to understand and modify
5. **Robustness**: Provide sensible defaults and handle missing configuration gracefully

## Configuration Management

### Environment Variables vs. Configuration Files

The application will use a hybrid approach:

#### Environment Variables

Use environment variables for:
- Settings that vary between environments
- Sensitive information (API keys, credentials)
- Settings that might need to be changed without code deployment

Accessing environment variables:
```python
import os

# Getting environment variables with defaults
database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
log_level = os.getenv("LOG_LEVEL", "INFO")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")  # No default for required secrets

# Convert string values to appropriate types
debug_mode = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
max_messages = int(os.getenv("MAX_MESSAGES", "100"))
```

#### Configuration Files

Use configuration files for:
- Default values and base configurations
- Non-sensitive, application-specific settings
- Complex configuration structures

Example configuration file (`config.py`):
```python
import os
from typing import Dict, Any

class BaseConfig:
    """Base configuration with shared settings."""
    # Application settings
    APP_NAME = "Roleplay Chat"
    DEFAULT_PAGE_SIZE = 50
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # API settings
    OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Default models
    DEFAULT_AI_MODELS = [
        {"id": "anthropic/claude-3-opus-20240229", "name": "Claude 3 Opus"},
        {"id": "anthropic/claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
        {"id": "anthropic/claude-3-haiku-20240307", "name": "Claude 3 Haiku"}
    ]

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    DATABASE_URL = "sqlite:///:memory:"

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Select configuration based on environment
config_classes = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

def get_config() -> BaseConfig:
    """Return the appropriate configuration based on the environment."""
    env = os.getenv("FLASK_ENV", "development")
    return config_classes.get(env, DevelopmentConfig)()
```

### Configuration Hierarchy and Precedence

The configuration system will follow this precedence order (highest priority first):

1. Environment variables
2. Environment-specific configuration class
3. Base configuration class defaults

### Loading Configuration

Create a function to load and validate configuration:

```python
def load_config():
    """Load and validate application configuration."""
    config = get_config()
    
    # Validate required settings
    required_settings = ["OPENROUTER_API_KEY"]
    missing = [setting for setting in required_settings if not getattr(config, setting)]
    
    if missing:
        raise ValueError(f"Missing required configuration settings: {', '.join(missing)}")
    
    return config
```

## Secret Management

### Development Environment

For local development, use `.env` files to store sensitive information:

```
# .env file for development
OPENROUTER_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
```

Important safeguards:
1. **Add `.env` to `.gitignore`** to prevent committing secrets
2. Provide an `env.example` template in the repository:
   ```
   # env.example - Template for .env file (DO NOT add real values here)
   OPENROUTER_API_KEY=
   DATABASE_URL=sqlite:///app.db
   FLASK_ENV=development
   ```

Loading `.env` files:
```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now environment variables are accessible via os.getenv()
api_key = os.getenv("OPENROUTER_API_KEY")
```

### Production Environment

For future production deployment:
- Store secrets as environment variables in your hosting platform
- Consider using a dedicated secrets management service if complexity grows

## Application Initialization

Create a clear initialization function for the application:

```python
def create_app(test_config=None):
    """Create and configure the Flask application."""
    from flask import Flask
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if test_config:
        # Use test configuration if provided
        app.config.from_mapping(test_config)
    else:
        # Load regular configuration
        config = load_config()
        app.config.from_object(config)
    
    # Initialize database
    from .models import init_db
    init_db(app)
    
    # Register blueprints
    from .api import register_blueprints
    register_blueprints(app)
    
    # Configure logging
    from .utils.logging import configure_logging
    configure_logging(app)
    
    return app
```

## Deployment Strategy

While the Roleplay Chat Web App is initially intended as a local application, this section outlines a forward-looking deployment strategy.

### Local Deployment

For local development and usage:

1. **Installation Script**:
   ```bash
   #!/bin/bash
   # setup.sh - Local installation script
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -e .
   
   # Set up initial database
   flask db upgrade
   flask seed  # Custom command to seed initial data
   
   echo "Setup complete. Run 'flask run' to start the application."
   ```

2. **Run Script**:
   ```bash
   #!/bin/bash
   # run.sh - Local run script
   
   source venv/bin/activate
   flask run
   ```

### Future Production Deployment Considerations

If the application expands beyond local usage:

1. **Containerization**:
   - Create Dockerfile and docker-compose.yml for containerized deployment
   - Separate services (web, database) into different containers
   - Use environment variables for configuration

2. **Database**:
   - Transition from SQLite to PostgreSQL for production
   - Implement backup strategy
   - Consider read replicas for scaling

3. **Hosting Options**:
   - Platform-as-a-Service (PaaS): Heroku, Render, Fly.io
   - Container orchestration: Kubernetes, AWS ECS
   - Virtual machines: AWS EC2, DigitalOcean Droplets

4. **CI/CD Pipeline**:
   - Set up automated testing and deployment
   - Implement environment promotion (dev → staging → production)
   - Automate database migrations

## Configuration Management Tools

### For Local Development

1. **python-dotenv**: Load environment variables from .env files
   ```bash
   pip install python-dotenv
   ```

2. **Flask configuration system**: Built-in support for different configurations
   ```python
   app.config.from_object('config.DevelopmentConfig')
   ```

### For Future Expansion

If the application grows beyond local usage, consider these tools:

1. **Consul or etcd**: For distributed configuration management
2. **HashiCorp Vault**: For advanced secrets management
3. **AWS Parameter Store/Secrets Manager**: For AWS deployments

## Configuration Validation

Implement validation for critical configuration parameters:

```python
def validate_config(app):
    """Validate application configuration."""
    # Check required settings
    required_settings = ["OPENROUTER_API_KEY", "DATABASE_URL"]
    missing = [setting for setting in required_settings if not app.config.get(setting)]
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    # Validate specific settings
    if app.config.get("MAX_MESSAGE_LENGTH", 0) <= 0:
        raise ValueError("MAX_MESSAGE_LENGTH must be a positive integer")
    
    # Test external connections if appropriate
    if not app.config.get("TESTING"):
        # Test database connection
        from .models import db
        try:
            db.engine.connect()
        except Exception as e:
            raise ValueError(f"Database connection failed: {str(e)}")
```

## Environment-Specific Behaviors

Configure your application to adapt to different environments:

```python
def configure_app_for_environment(app):
    """Configure environment-specific behaviors."""
    env = app.config.get("ENV", "development")
    
    if env == "development":
        # Development-specific setup
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        
        # Enable interactive debugger
        app.debug = True
        
        # Use development-specific logging
        configure_dev_logging(app)
        
    elif env == "testing":
        # Testing-specific setup
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["TESTING"] = True
        
    elif env == "production":
        # Production-specific setup
        configure_prod_logging(app)
        
        # Set up production error handling
        register_error_handlers(app)
```

## Best Practices

1. **Never Hardcode Secrets**: Always use environment variables or secure storage
2. **Use Descriptive Names**: Configuration variables should have clear, descriptive names
3. **Document Configuration**: Maintain documentation of all configuration parameters
4. **Provide Defaults**: Have sensible defaults for optional configuration
5. **Validate Early**: Validate configuration at startup to fail fast
6. **Version Configuration**: Track configuration changes alongside code
7. **Separate Configuration Types**: Keep secrets, environment settings, and app settings separate

## Conclusion

This configuration and deployment strategy provides a foundation for managing the Roleplay Chat Web App's settings across different environments. Starting with a simple, file-based approach for local development, it outlines a path for growth if the application expands beyond its initial scope.

By following these guidelines, the application will maintain a clear separation between code and configuration, handle sensitive information securely, and adapt to different environments while remaining easy to deploy and manage.