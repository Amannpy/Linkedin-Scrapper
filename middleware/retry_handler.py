"""
Retry logic with exponential backoff
"""
import asyncio
import logging
from typing import Callable, Any, Optional
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from middleware.error_handler import (
    NetworkException,
    TimeoutException,
    ElementNotFoundException,
    should_retry
)

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handle retry logic for operations"""

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        exponential_base: int = 2
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.exponential_base = exponential_base
        self.attempt_counts = {}

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        operation_name: str = "Unknown",
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_attempts} for {operation_name}")

                result = await func(*args, **kwargs)

                # Success - reset attempt count
                if operation_name in self.attempt_counts:
                    del self.attempt_counts[operation_name]

                return result

            except Exception as e:
                self.attempt_counts[operation_name] = attempt

                if not should_retry(e, attempt, self.max_attempts):
                    logger.error(f"{operation_name} failed permanently: {e}")
                    raise

                if attempt < self.max_attempts:
                    wait_time = self._calculate_wait_time(attempt)
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"{operation_name} failed after {attempt} attempts: {e}")
                    raise

    def _calculate_wait_time(self, attempt: int) -> float:
        """Calculate wait time with exponential backoff"""
        wait = min(
            self.min_wait * (self.exponential_base ** (attempt - 1)),
            self.max_wait
        )
        return wait

    def get_retry_stats(self) -> dict:
        """Get retry statistics"""
        return {
            'operations_with_retries': len(self.attempt_counts),
            'retry_details': self.attempt_counts.copy()
        }


# Decorator for automatic retries
def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    operation_name: Optional[str] = None
):
    """Decorator to add retry logic to async functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            handler = RetryHandler(max_attempts, min_wait, max_wait)
            return await handler.execute_with_retry(
                func, *args, operation_name=op_name, **kwargs
            )
        return wrapper
    return decorator


# Tenacity-based retry decorators for specific scenarios
def retry_on_network_error(max_attempts: int = 3):
    """Retry on network errors"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(NetworkException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def retry_on_timeout(max_attempts: int = 2):
    """Retry on timeout errors"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(TimeoutException),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


def retry_on_element_not_found(max_attempts: int = 3):
    """Retry when element is not found"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(ElementNotFoundException),
        before_sleep=before_sleep_log(logger, logging.DEBUG)
    )


# Smart retry function that chooses strategy based on error
async def smart_retry(
    func: Callable,
    *args,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """
    Smart retry that adjusts strategy based on error type
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)

        except NetworkException as e:
            last_error = e
            wait_time = 2 ** attempt
            logger.warning(f"Network error on attempt {attempt}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

        except TimeoutException as e:
            last_error = e
            wait_time = 5 * attempt
            logger.warning(f"Timeout on attempt {attempt}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

        except ElementNotFoundException as e:
            last_error = e
            wait_time = 1 * attempt
            logger.warning(f"Element not found on attempt {attempt}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

        except Exception as e:
            # For unexpected errors, don't retry
            logger.error(f"Unexpected error: {e}")
            raise

    # If we exhausted retries, raise the last error
    if last_error:
        raise last_error


# Batch retry handler for multiple operations
class BatchRetryHandler:
    """Handle retries for batch operations"""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.failed_items = []
        self.retry_handler = RetryHandler(max_attempts)

    async def process_batch_with_retry(
        self,
        items: list,
        process_func: Callable,
        continue_on_error: bool = True
    ) -> tuple[list, list]:
        """
        Process batch of items with retry
        Returns: (successful_results, failed_items)
        """
        results = []
        failed = []

        for item in items:
            try:
                result = await self.retry_handler.execute_with_retry(
                    process_func,
                    item,
                    operation_name=f"Process {item}"
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {item} after retries: {e}")
                failed.append({'item': item, 'error': str(e)})

                if not continue_on_error:
                    raise

        return results, failed