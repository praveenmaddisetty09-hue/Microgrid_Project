"""
Custom Exception Classes for Smart Microgrid Manager Pro.

This module defines a hierarchy of domain-specific exceptions for better
error handling, debugging, and user feedback.
"""


class MicrogridError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.message = message
        self.context = context
    
    def __str__(self) -> str:
        """Return formatted error message."""
        return self.message


class ValidationError(MicrogridError):
    """Raised when input validation fails."""
    pass


class OptimizationError(MicrogridError):
    """Raised when the optimization solver fails."""
    
    STATUS_INFEASIBLE = "Infeasible"
    STATUS_UNBOUNDED = "Unbounded"
    STATUS_TIMEOUT = "Timeout"
    STATUS_ERROR = "Error"
    
    def __init__(self, message: str, status: str = None):
        super().__init__(message, status=status)
        self.status = status


class DatabaseError(MicrogridError):
    """Raised when database operations fail."""
    pass


class AuthenticationError(MicrogridError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(MicrogridError):
    """Raised when user lacks permission for an action."""
    pass


class WeatherAPIError(MicrogridError):
    """Raised when weather API operations fail."""
    pass


class ConfigurationError(MicrogridError):
    """Raised when application configuration is invalid."""
    pass


def handle_errors(default_return=None, log_errors: bool = True):
    """
    Decorator for consistent exception handling.
    """
    def decorator(func):
        import functools
        import logging
        
        logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MicrogridError:
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                return default_return
        
        return wrapper
    return decorator

