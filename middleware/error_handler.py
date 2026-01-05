from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from monitoring.logger import get_logger
from utils.validators import ValidationException

logger = get_logger()


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.

    Args:
        request: FastAPI request
        exc: Exception that was raised

    Returns:
        JSONResponse with error details
    """
    # Log the error with full context
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
    )

    # Determine status code and error message
    if isinstance(exc, ValidationException):
        status_code = status.HTTP_400_BAD_REQUEST
        error_message = str(exc)
        error_code = "VALIDATION_ERROR"
    elif isinstance(exc, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        error_message = str(exc)
        error_code = "VALUE_ERROR"
    elif isinstance(exc, TimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        error_message = "Request timeout"
        error_code = "TIMEOUT_ERROR"
    else:
        # Generic server error - don't expose internal details
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_message = "An internal server error occurred"
        error_code = "INTERNAL_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


class ErrorHandlerMiddleware:
    """Middleware for consistent error handling."""

    async def __call__(self, request: Request, call_next):
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await global_exception_handler(request, exc)
