"""Main application entry point."""

from flask import Flask

from app.config import get_config


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Register blueprints, initialize extensions, etc. will be added later

    @app.route("/")
    def index():
        """Index route for the application."""
        return "LLM Roleplay Chat Client API"

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", False))
