"""API layer exposing HTTP endpoints for the application."""

from flask import Blueprint
from flask_restx import Api

# Create a Blueprint for the API
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

# Initialize the Flask-RESTX API
api = Api(
    api_bp,
    version="1.0",
    title="Roleplay Chat API",
    description="API for the Roleplay Chat Web App",
    doc="/docs",
    default="Roleplay Chat",
    default_label="Roleplay Chat Web App API",
)

# Import and register namespaces
from app.api.namespaces.ai_models import api as ai_models_ns
from app.api.namespaces.characters import api as characters_ns
from app.api.namespaces.chat_sessions import api as chat_sessions_ns
from app.api.namespaces.messages import api as messages_ns
from app.api.namespaces.settings import api as settings_ns
from app.api.namespaces.system_prompts import api as system_prompts_ns
from app.api.namespaces.user_profiles import api as user_profiles_ns

# Add namespaces to the API
api.add_namespace(characters_ns, path="/characters")
api.add_namespace(user_profiles_ns, path="/user-profiles")
api.add_namespace(ai_models_ns, path="/ai-models")
api.add_namespace(system_prompts_ns, path="/system-prompts")
api.add_namespace(chat_sessions_ns, path="/chat-sessions")
api.add_namespace(messages_ns, path="/messages")
api.add_namespace(settings_ns, path="/settings")


def init_app(app):
    """Initialize the API with the Flask app."""
    app.register_blueprint(api_bp)


# Custom error handler to ensure all errors have success=False
@api.errorhandler
def default_error_handler(error):
    """Default error handler for all API errors."""
    return {
        "success": False,
        "error": {
            "code": getattr(error, "error_code", "UNKNOWN_ERROR"),
            "message": str(error.description),
            "details": getattr(error, "errors", {}),
        },
    }, getattr(error, "code", 500)
