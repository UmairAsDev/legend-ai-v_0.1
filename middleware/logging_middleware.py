import time
import uuid
from fastapi import Request
from monitoring.logger import get_logger, set_correlation_id

logger = get_logger()


class LoggingMiddleware:
    """Middleware for request/response logging with correlation IDs."""

    async def __call__(self, request: Request, call_next):
        """Process request with logging."""

        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)

        # Log request
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} latency={latency_ms:.2f}ms"
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"latency={latency_ms:.2f}ms error={str(exc)}"
            )
            raise
