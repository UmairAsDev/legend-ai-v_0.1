import time
from fastapi import Request, HTTPException, status
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple
from monitoring.logger import get_logger

logger = get_logger()


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per client
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds

        # Store: {client_id: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

        logger.info(f"Rate limiter initialized: {requests_per_minute} requests/minute")

    def _clean_old_requests(self, client_id: str, current_time: float):
        """Remove requests outside the time window."""
        cutoff_time = current_time - self.window_size
        self.requests[client_id] = [
            (ts, count) for ts, count in self.requests[client_id] if ts > cutoff_time
        ]

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for client.

        Args:
            client_id: Client identifier (API key or IP)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        with self.lock:
            current_time = time.time()

            # Clean old requests
            self._clean_old_requests(client_id, current_time)

            # Count requests in current window
            total_requests = sum(count for _, count in self.requests[client_id])

            if total_requests >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for client {client_id[:8]}... "
                    f"({total_requests}/{self.requests_per_minute})"
                )
                return False, 0

            # Add current request
            self.requests[client_id].append((current_time, 1))

            remaining = self.requests_per_minute - total_requests - 1
            return True, remaining

    def get_retry_after(self, client_id: str) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            client_id: Client identifier

        Returns:
            Seconds until reset
        """
        with self.lock:
            if not self.requests[client_id]:
                return 0

            oldest_request = min(ts for ts, _ in self.requests[client_id])
            current_time = time.time()
            retry_after = int(self.window_size - (current_time - oldest_request))

            return max(0, retry_after)


class RateLimitMiddleware:
    """Middleware for rate limiting."""

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize rate limit middleware.

        Args:
            rate_limiter: RateLimiter instance
        """
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""

        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Use API key as client ID, fallback to IP
        client_id = request.headers.get("X-API-Key")
        if not client_id and request.client:
            client_id = request.client.host
        if not client_id:
            client_id = "unknown"

        # Check rate limit
        is_allowed, remaining = self.rate_limiter.is_allowed(client_id)

        if not is_allowed:
            retry_after = self.rate_limiter.get_retry_after(client_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(
            self.rate_limiter.requests_per_minute
        )
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
