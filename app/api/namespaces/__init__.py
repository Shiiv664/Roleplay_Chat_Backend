"""API namespaces for resource endpoints."""

from flask import request

from app.utils.exceptions import (
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)


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
