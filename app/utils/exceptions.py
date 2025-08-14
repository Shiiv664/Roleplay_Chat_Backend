"""Custom exception classes for the application."""


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message, details=None):
        """Initialize the base application error.

        Args:
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(AppError):
    """Exception raised for database operation errors."""

    pass


class ValidationError(AppError):
    """Exception raised for data validation errors."""

    def __init__(self, error_code, message, details=None):
        """Initialize validation error with error code.
        
        Args:
            error_code: Error code for the validation error
            message: Human-readable error message
            details: Optional dictionary of additional error details
        """
        self.error_code = error_code
        super().__init__(message, details)
        
    def __str__(self):
        return f"{self.error_code}: {self.message}"


class ResourceNotFoundError(AppError):
    """Exception raised when a requested resource is not found."""

    pass


class ExternalAPIError(AppError):
    """Exception raised for errors when interacting with external APIs."""

    pass


class BusinessRuleError(AppError):
    """Exception raised for business rule violations."""

    pass


class ProcessingError(AppError):
    """Exception raised for processing errors during data manipulation."""

    pass
