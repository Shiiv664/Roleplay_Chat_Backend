"""Main application entry point."""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables early
env = os.getenv("FLASK_ENV", "development")
env_file = f".env.{env}"
if Path(env_file).exists():
    load_dotenv(env_file)
else:
    load_dotenv()

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
    # In production, serve React static files
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        # Set static folder to frontend build directory
        frontend_build_path = Path("frontend_build")
        if frontend_build_path.exists():
            app = Flask(__name__, static_folder=str(frontend_build_path), static_url_path="/")
        else:
            app = Flask(__name__)
            print("Warning: frontend_build directory not found for production static files")
    else:
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
    
    # Register frontend routes AFTER API but BEFORE error handlers (production only)
    if env == "production" and Path("frontend_build").exists():
        frontend_build_path = Path("frontend_build")
        
        # Root route - serve React app
        @app.route("/")
        def serve_index():
            """Serve React app index."""
            return send_from_directory(str(frontend_build_path), "index.html")
        
        # Static assets route
        @app.route("/assets/<path:filename>")
        def serve_assets(filename):
            """Serve static assets."""
            return send_from_directory(str(frontend_build_path / "assets"), filename)
            
        # Catch-all route for SPA routing - serve index.html for any non-API routes
        @app.route("/<path:filename>")
        def serve_static_files(filename):
            """Serve static files or index.html for SPA routing."""
            # Skip API routes - they're handled by Flask-RESTX
            if filename.startswith("api/"):
                return "API endpoint not found", 404
                
            # Try to serve the specific file first
            file_path = frontend_build_path / filename
            if file_path.exists() and file_path.is_file():
                return send_from_directory(str(frontend_build_path), filename)
            
            # For any other route (SPA routes like /characters, /user-profiles), serve index.html
            return send_from_directory(str(frontend_build_path), "index.html")

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

    # Development vs Production frontend handling
    if env == "production" and Path("frontend_build").exists():
        # Routes already registered above
        pass
    else:
        # Development mode - API only
        @app.route("/")
        def index():
            """Index route for the application."""
            return jsonify(
                {
                    "app": "LLM Roleplay Chat Client API",
                    "version": "1.0.0",
                    "api_docs": "/api/v1/docs",
                    "mode": "development",
                    "frontend": "served separately on port 5173"
                }
            )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config.get("HOST", "127.0.0.1"),
        port=app.config.get("PORT", 5000),
        debug=app.config.get("DEBUG", False)
    )
