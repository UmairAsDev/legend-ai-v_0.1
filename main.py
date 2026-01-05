import os
from controller.route.app import router as app_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limiter import RateLimiter, RateLimitMiddleware
from middleware.error_handler import ErrorHandlerMiddleware, global_exception_handler
from monitoring.logger import configure_logging, get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
configure_logging(log_level=os.getenv("LOG_LEVEL", "INFO"), log_file="logs/app.log")
logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="Legend Voice Agent API",
    description="Production-ready voice-to-clinical-note API with comprehensive monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add routers
app.include_router(app_router)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - last added is executed first)
# 1. Error handling (outermost)
app.middleware("http")(ErrorHandlerMiddleware())

# 2. Logging
app.middleware("http")(LoggingMiddleware())

# 3. Rate limiting
rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
rate_limiter = RateLimiter(requests_per_minute=rate_limit_per_minute)
app.middleware("http")(RateLimitMiddleware(rate_limiter))

# Note: Authentication middleware is optional - uncomment if needed
# from middleware.auth import AuthMiddleware
# api_keys = os.getenv("API_KEYS", "").split(",")
# if api_keys and api_keys[0]:  # Only add if API keys are configured
#     app.middleware("http")(AuthMiddleware(api_keys))

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

logger.info("Legend Voice Agent API started successfully")


def main():
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
