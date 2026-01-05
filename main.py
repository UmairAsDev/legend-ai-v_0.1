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
    description="Production-ready voice-to-clinical-note API with Pipecat OpenTelemetry tracing",
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

# 3. Rate limiting (optional - can be disabled if not needed)
rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "0"))
if rate_limit_per_minute > 0:
    rate_limiter = RateLimiter(requests_per_minute=rate_limit_per_minute)
    app.middleware("http")(RateLimitMiddleware(rate_limiter))
    logger.info(f"Rate limiting enabled: {rate_limit_per_minute} requests/minute")
else:
    logger.info("Rate limiting disabled")

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

logger.info("Legend Voice Agent API started successfully")


def main():
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8001"))
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
