"""Main application entry point."""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from app.config import get_config
from app.utils.exceptions import (
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Add is_debug property to request context
    @app.before_request
    def before_request():
        request.is_debug = app.debug

    # Initialize database
    from app.utils.db import init_db

    init_db(app)

    # Initialize API
    from app.api import init_app as init_api

    init_api(app)

    # Configure static file serving for uploads
    UPLOAD_FOLDER = Path("uploads")
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        """Serve uploaded files."""
        try:
            return send_from_directory(str(UPLOAD_FOLDER), filename)
        except FileNotFoundError:
            return "File not found", 404
        except Exception as e:
            app.logger.error(f"Error serving uploaded file {filename}: {e}")
            return "Internal server error", 500

    # Global error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        response = {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": getattr(e, "details", None),
            },
        }
        return jsonify(response), 400

    @app.errorhandler(ResourceNotFoundError)
    def handle_not_found_error(e):
        response = {
            "success": False,
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": str(e),
                "details": getattr(e, "details", None),
            },
        }
        return jsonify(response), 404

    @app.errorhandler(BusinessRuleError)
    def handle_business_rule_error(e):
        response = {
            "success": False,
            "error": {
                "code": "BUSINESS_RULE_ERROR",
                "message": str(e),
                "details": getattr(e, "details", None),
            },
        }
        return jsonify(response), 400

    @app.errorhandler(DatabaseError)
    def handle_database_error(e):
        response = {
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": str(e) if app.debug else None,
            },
        }
        return jsonify(response), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        response = {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(e) if app.debug else None,
            },
        }
        return jsonify(response), 500

    # Root route
    @app.route("/")
    def index():
        """Index route for the application."""
        return jsonify(
            {
                "app": "LLM Roleplay Chat Client API",
                "version": "1.0.0",
                "api_docs": "/api/v1/docs",
            }
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
