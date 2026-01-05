from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from monitoring.logger import get_logger

logger = get_logger()

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthMiddleware:
    """Middleware for API key authentication."""

    def __init__(self, api_keys: list[str]):
        """
        Initialize auth middleware.

        Args:
            api_keys: List of valid API keys
        """
        self.api_keys = set(api_keys)
        logger.info(f"Auth middleware initialized with {len(self.api_keys)} API keys")

    async def __call__(self, request: Request, call_next):
        """Process request with authentication."""

        # Skip auth for health check and metrics endpoints
        if request.url.path in [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(f"Missing API key for request to {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Provide X-API-Key header.",
            )

        if api_key not in self.api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
            )

        # API key is valid, proceed
        logger.debug(f"Authenticated request to {request.url.path}")
        return await call_next(request)


def get_api_key_dependency(api_key: Optional[str] = None) -> str:
    """
    Dependency for API key validation in route handlers.

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    from config.settings import settings

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key
