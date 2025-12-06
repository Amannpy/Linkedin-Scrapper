"""
Centralized error handling and custom exceptions
"""
import logging
from typing import Optional, Callable, Any
from functools import wraps
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


# Custom Exceptions
class LinkedInScraperException(Exception):
    """Base exception for LinkedIn scraper"""
    pass


class LoginException(LinkedInScraperException):
    """Raised when login fails"""
    pass


class AuthenticationException(LinkedInScraperException):
    """Raised when authentication is required"""
    pass


class RateLimitException(LinkedInScraperException):
    """Raised when rate limit is exceeded"""
    pass


class CaptchaException(LinkedInScraperException):
    """Raised when CAPTCHA is detected"""
    pass


class ElementNotFoundException(LinkedInScraperException):
    """Raised when element is not found"""
    pass


class TimeoutException(LinkedInScraperException):
    """Raised when operation times out"""
    pass


class NetworkException(LinkedInScraperException):
    """Raised on network errors"""
    pass


class ValidationException(LinkedInScraperException):
    """Raised on validation errors"""
    pass


class DataExtractionException(LinkedInScraperException):
    """Raised when data extraction fails"""
    pass


# Error Handler Class
class ErrorHandler:
    """Centralized error handling"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.error_count = 0
        self.error_log = []

    def log_error(
            self,
            error: Exception,
            context: Optional[str] = None,
            severity: str = "ERROR"
    ):
        """Log error with context"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'severity': severity,
            'traceback': traceback.format_exc()
        }

        self.error_log.append(error_info)
        self.error_count += 1

        # Log to logger
        log_message = f"{severity} - {context or 'Unknown context'}: {error}"
        if severity == "CRITICAL":
            logger.critical(log_message)
        elif severity == "ERROR":
            logger.error(log_message)
        elif severity == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Write to file if specified
        if self.log_file:
            self._write_to_file(error_info)

    def _write_to_file(self, error_info: dict):
        """Write error to log file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'=' * 80}\n")
                for key, value in error_info.items():
                    f.write(f"{key}: {value}\n")
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")

    def get_error_stats(self) -> dict:
        """Get error statistics"""
        error_types = {}
        for error in self.error_log:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            'total_errors': self.error_count,
            'error_types': error_types,
            'recent_errors': self.error_log[-10:]  # Last 10 errors
        }

    def clear_errors(self):
        """Clear error log"""
        self.error_log = []
        self.error_count = 0


# Global error handler instance
error_handler = ErrorHandler(log_file="scraper_errors.log")


# Decorator for error handling
def handle_errors(
        operation_name: str = "Unknown operation",
        raise_on_error: bool = False,
        default_return: Any = None
):
    """Decorator to handle errors in functions"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except CaptchaException as e:
                error_handler.log_error(e, f"{operation_name} - CAPTCHA", "CRITICAL")
                if raise_on_error:
                    raise
                return default_return
            except RateLimitException as e:
                error_handler.log_error(e, f"{operation_name} - Rate Limit", "WARNING")
                if raise_on_error:
                    raise
                return default_return
            except TimeoutException as e:
                error_handler.log_error(e, f"{operation_name} - Timeout", "WARNING")
                if raise_on_error:
                    raise
                return default_return
            except NetworkException as e:
                error_handler.log_error(e, f"{operation_name} - Network", "ERROR")
                if raise_on_error:
                    raise
                return default_return
            except ElementNotFoundException as e:
                error_handler.log_error(e, f"{operation_name} - Element", "WARNING")
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                error_handler.log_error(e, operation_name, "ERROR")
                if raise_on_error:
                    raise
                return default_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, operation_name, "ERROR")
                if raise_on_error:
                    raise
                return default_return

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Context manager for error handling
class ErrorContext:
    """Context manager for error handling"""

    def __init__(self, operation_name: str, suppress: bool = False):
        self.operation_name = operation_name
        self.suppress = suppress

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            error_handler.log_error(
                exc_val,
                self.operation_name,
                "ERROR"
            )
            return self.suppress  # Suppress exception if True
        return False


# Utility functions
def is_recoverable_error(error: Exception) -> bool:
    """Check if error is recoverable"""
    recoverable_types = (
        NetworkException,
        TimeoutException,
        ElementNotFoundException,
    )
    return isinstance(error, recoverable_types)


def should_retry(error: Exception, attempt: int, max_attempts: int) -> bool:
    """Determine if operation should be retried"""
    if attempt >= max_attempts:
        return False

    # Don't retry on certain errors
    non_retryable = (
        LoginException,
        AuthenticationException,
        ValidationException,
        CaptchaException,
    )

    if isinstance(error, non_retryable):
        return False

    return is_recoverable_error(error)
