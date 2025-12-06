"""Middleware package"""
from .error_handler import (
    error_handler,
    ErrorHandler,
    handle_errors,
    ErrorContext,
    LinkedInScraperException,
    LoginException,
    AuthenticationException,
    RateLimitException,
    CaptchaException,
    ElementNotFoundException,
    TimeoutException,
    NetworkException,
    ValidationException,
    DataExtractionException
)
from .retry_handler import (
    RetryHandler,
    with_retry,
    retry_on_network_error,
    retry_on_timeout,
    retry_on_element_not_found,
    smart_retry,
    BatchRetryHandler
)
from .rate_limiter import (
    RateLimiter,
    AdaptiveRateLimiter,
    RequestBudget,
    rate_limiter,
    rate_limited
)

__all__ = [
    # Error handling
    'error_handler',
    'ErrorHandler',
    'handle_errors',
    'ErrorContext',
    'LinkedInScraperException',
    'LoginException',
    'AuthenticationException',
    'RateLimitException',
    'CaptchaException',
    'ElementNotFoundException',
    'TimeoutException',
    'NetworkException',
    'ValidationException',
    'DataExtractionException',
    # Retry handling
    'RetryHandler',
    'with_retry',
    'retry_on_network_error',
    'retry_on_timeout',
    'retry_on_element_not_found',
    'smart_retry',
    'BatchRetryHandler',
    # Rate limiting
    'RateLimiter',
    'AdaptiveRateLimiter',
    'RequestBudget',
    'rate_limiter',
    'rate_limited',
]
