"""API namespaces for resource endpoints."""

from datetime import datetime

from flask import request

from app.utils.exceptions import (
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)


def model_to_dict(obj):
    """Convert SQLAlchemy model instance to a dictionary.

    Args:
        obj: SQLAlchemy model instance

    Returns:
        dict: Dictionary representation of the model
    """
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]

    # Use the model's built-in to_dict method if available
    if hasattr(obj, "to_dict"):
        result = obj.to_dict()
        # Convert datetime objects to ISO format strings for JSON serialization
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    # Fallback for non-model objects
    return obj


def create_response(data=None, meta=None, success=True, error=None):
    """Create a standardized response format.

    Args:
        data: The response data
        meta: Additional metadata (e.g., pagination)
        success: Whether the request was successful
        error: Error information if success is False

    Returns:
        dict: Formatted response
    """
    # Convert SQLAlchemy models to dictionaries
    if data is not None:
        data = model_to_dict(data)

    response = {"success": success, "data": data, "meta": meta or {}, "error": error}
    return response


def handle_exception(e):
    """Handle exceptions and return appropriate responses.

    Args:
        e: The exception to handle

    Returns:
        tuple: (response_dict, status_code)
    """
    if isinstance(e, ResourceNotFoundError):
        return (
            create_response(
                success=False,
                error={
                    "code": "RESOURCE_NOT_FOUND",
                    "message": str(e),
                    "details": getattr(e, "details", None),
                },
            ),
            404,
        )

    elif isinstance(e, ValidationError):
        return (
            create_response(
                success=False,
                error={
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": getattr(e, "details", None),
                },
            ),
            400,
        )

    elif isinstance(e, BusinessRuleError):
        return (
            create_response(
                success=False,
                error={
                    "code": "BUSINESS_RULE_ERROR",
                    "message": str(e),
                    "details": getattr(e, "details", None),
                },
            ),
            400,
        )

    elif isinstance(e, DatabaseError):
        return (
            create_response(
                success=False,
                error={
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred",
                    "details": str(e) if request.is_debug else None,
                },
            ),
            500,
        )

    else:
        # Unexpected errors
        return (
            create_response(
                success=False,
                error={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(e) if request.is_debug else None,
                },
            ),
            500,
        )
