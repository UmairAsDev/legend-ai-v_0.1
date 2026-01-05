import sys
import uuid
from loguru import logger
from contextvars import ContextVar
from typing import Optional

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Get or create correlation ID for request tracing."""
    correlation_id = correlation_id_var.get()
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str):
    """Set correlation ID for request tracing."""
    correlation_id_var.set(correlation_id)


def sanitize_patient_data(data: dict) -> dict:
    """Sanitize patient data for logging (remove PII)."""
    sensitive_fields = {
        "name",
        "patient_name",
        "ssn",
        "social_security",
        "email",
        "phone",
        "address",
        "dob",
        "date_of_birth",
    }

    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_patient_data(value)
        else:
            sanitized[key] = value

    return sanitized


def configure_logging(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """Configure structured logging with correlation IDs."""

    # Remove default logger
    logger.remove()

    # Custom format with correlation ID
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[correlation_id]}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add console logger
    logger.add(
        sys.stderr, format=log_format, level=log_level, colorize=True, enqueue=True
    )

    # Add file logger with rotation
    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        serialize=True,  # JSON format for parsing
    )

    # Configure logger to always include correlation ID
    logger.configure(extra={"correlation_id": "no-correlation-id"})

    return logger


def get_logger():
    """Get logger with current correlation ID."""
    correlation_id = get_correlation_id()
    return logger.bind(correlation_id=correlation_id)
