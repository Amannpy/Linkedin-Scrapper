"""
Rate limiting to prevent detection and respect server resources
"""
import asyncio
import time
import logging
from typing import Dict, Optional
from collections import deque
from datetime import datetime, timedelta

from config.settings import config
from middleware.error_handler import RateLimitException

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with time windows

    Prevents exceeding rate limits by tracking requests over time.
    """

    def __init__(
            self,
            requests_per_minute: Optional[int] = None,
            requests_per_hour: Optional[int] = None
    ):
        self.requests_per_minute = requests_per_minute or config.requests_per_minute
        self.requests_per_hour = requests_per_hour or config.requests_per_hour

        # Track request timestamps
        self.minute_requests: deque = deque()
        self.hour_requests: deque = deque()

        # Statistics
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0

        logger.info(
            f"Rate limiter initialized: "
            f"{self.requests_per_minute}/min, {self.requests_per_hour}/hour"
        )

    async def acquire(self, weight: int = 1):
        """
        Acquire permission to make a request

        Args:
            weight: Number of requests this operation counts as

        Raises:
            RateLimitException: If rate limit cannot be satisfied
        """
        current_time = time.time()

        # Clean old requests from tracking
        self._clean_old_requests(current_time)

        # Check if we need to wait
        wait_time = self._calculate_wait_time(current_time, weight)

        if wait_time > 0:
            self.rate_limit_hits += 1
            logger.warning(
                f"Rate limit reached. Waiting {wait_time:.2f}s... "
                f"(Requests: {len(self.minute_requests)}/min, "
                f"{len(self.hour_requests)}/hour)"
            )

            await asyncio.sleep(wait_time)
            self.total_wait_time += wait_time
            current_time = time.time()

        # Record request
        for _ in range(weight):
            self.minute_requests.append(current_time)
            self.hour_requests.append(current_time)

        self.total_requests += weight

    def _clean_old_requests(self, current_time: float):
        """Remove requests outside time windows"""
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Clean minute window
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()

        # Clean hour window
        while self.hour_requests and self.hour_requests[0] < hour_ago:
            self.hour_requests.popleft()

    def _calculate_wait_time(self, current_time: float, weight: int) -> float:
        """Calculate how long to wait before making request"""
        wait_times = []

        # Check minute limit
        if len(self.minute_requests) + weight > self.requests_per_minute:
            # Calculate when the oldest request will expire
            oldest = self.minute_requests[0]
            minute_wait = 60 - (current_time - oldest) + 0.1  # Add small buffer
            wait_times.append(minute_wait)

        # Check hour limit
        if len(self.hour_requests) + weight > self.requests_per_hour:
            oldest = self.hour_requests[0]
            hour_wait = 3600 - (current_time - oldest) + 0.1
            wait_times.append(hour_wait)

        return max(wait_times) if wait_times else 0

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        return {
            'total_requests': self.total_requests,
            'total_wait_time': round(self.total_wait_time, 2),
            'rate_limit_hits': self.rate_limit_hits,
            'current_minute_requests': len(self.minute_requests),
            'current_hour_requests': len(self.hour_requests),
            'minute_limit': self.requests_per_minute,
            'hour_limit': self.requests_per_hour,
        }

    def reset(self):
        """Reset rate limiter"""
        self.minute_requests.clear()
        self.hour_requests.clear()
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0
        logger.info("Rate limiter reset")


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on server responses

    Automatically adjusts rate when detecting throttling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_requests_per_minute = self.requests_per_minute
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.backoff_multiplier = 1.0

    async def acquire(self, weight: int = 1):
        """Acquire with current backoff multiplier"""
        # Apply backoff
        adjusted_rpm = int(self.base_requests_per_minute / self.backoff_multiplier)
        self.requests_per_minute = max(adjusted_rpm, 1)  # At least 1 request/min

        await super().acquire(weight)

    def record_success(self):
        """Record successful request"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0

        # Gradually reduce backoff on consecutive successes
        if self.consecutive_successes >= 10 and self.backoff_multiplier > 1.0:
            self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
            logger.info(f"Rate limiter: Reducing backoff to {self.backoff_multiplier:.2f}x")

    def record_failure(self):
        """Record failed/throttled request"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        # Increase backoff on failures
        if self.consecutive_failures >= 3:
            self.backoff_multiplier = min(5.0, self.backoff_multiplier * 1.5)
            logger.warning(f"Rate limiter: Increasing backoff to {self.backoff_multiplier:.2f}x")

    def get_stats(self) -> Dict:
        """Get extended statistics"""
        stats = super().get_stats()
        stats.update({
            'backoff_multiplier': round(self.backoff_multiplier, 2),
            'adjusted_rpm': self.requests_per_minute,
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
        })
        return stats


class RequestBudget:
    """
    Manage request budget over a time period

    Useful for scraping campaigns with daily/weekly limits.
    """

    def __init__(self, total_requests: int, time_period_hours: int = 24):
        self.total_budget = total_requests
        self.remaining_budget = total_requests
        self.time_period_hours = time_period_hours
        self.start_time = datetime.now()
        self.reset_time = self.start_time + timedelta(hours=time_period_hours)

    def consume(self, count: int = 1) -> bool:
        """
        Consume from budget

        Args:
            count: Number of requests to consume

        Returns:
            bool: True if budget available, False otherwise
        """
        # Check if we need to reset
        if datetime.now() >= self.reset_time:
            self.reset()

        if self.remaining_budget >= count:
            self.remaining_budget -= count
            return True

        logger.warning(
            f"Request budget exhausted. "
            f"{self.remaining_budget}/{self.total_budget} remaining. "
            f"Resets at {self.reset_time}"
        )
        return False

    def reset(self):
        """Reset budget"""
        self.remaining_budget = self.total_budget
        self.start_time = datetime.now()
        self.reset_time = self.start_time + timedelta(hours=self.time_period_hours)
        logger.info(f"Request budget reset to {self.total_budget}")

    def get_info(self) -> Dict:
        """Get budget information"""
        return {
            'total_budget': self.total_budget,
            'remaining': self.remaining_budget,
            'used': self.total_budget - self.remaining_budget,
            'usage_percent': round(
                ((self.total_budget - self.remaining_budget) / self.total_budget) * 100, 2
            ),
            'resets_at': self.reset_time.isoformat(),
            'time_remaining': str(self.reset_time - datetime.now()),
        }


# Global rate limiter instance
rate_limiter = AdaptiveRateLimiter()


# Decorator for rate-limited functions
def rate_limited(weight: int = 1):
    """
    Decorator to apply rate limiting to async functions

    Args:
        weight: Number of requests this operation counts as
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            await rate_limiter.acquire(weight)
            try:
                result = await func(*args, **kwargs)
                rate_limiter.record_success()
                return result
            except Exception as e:
                # Check if it's a rate limit error
                if 'rate limit' in str(e).lower() or '429' in str(e):
                    rate_limiter.record_failure()
                raise

        return wrapper

    return decorator