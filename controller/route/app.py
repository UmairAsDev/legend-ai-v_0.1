import time
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional

from controller.schemas.request_models import SessionStartRequest
from controller.schemas.response_models import (
    ClinicalNoteResponse,
    ErrorResponse,
    HealthCheckResponse,
    MetricsResponse,
)
from monitoring.logger import get_logger
from utils.validators import validate_patient_data, ValidationException

logger = get_logger()

router = APIRouter(prefix="/api/v1")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@router.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service status.

    Returns service health and status of external dependencies.
    """
    from config.settings import settings

    services_status = {
        "api": "healthy",
        "deepgram": "unknown",  # Could add actual health checks
        "aws_bedrock": "unknown",
    }

    # Check if required config is present
    try:
        if not settings.deepgram_api_key:
            services_status["deepgram"] = "not_configured"
        else:
            services_status["deepgram"] = "configured"

        if not settings.model_id:
            services_status["aws_bedrock"] = "not_configured"
        else:
            services_status["aws_bedrock"] = "configured"
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        services_status["api"] = "degraded"

    overall_status = (
        "healthy"
        if all(
            s in ["healthy", "configured", "unknown"] for s in services_status.values()
        )
        else "degraded"
    )

    return HealthCheckResponse(status=overall_status, services=services_status)


@router.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get application metrics information.

    Note: This API uses Pipecat's native OpenTelemetry tracing for comprehensive metrics.
    Token usage, latency, and performance data are exported to your configured OTLP endpoint.

    Returns basic service information. For detailed metrics, query your OpenTelemetry backend.
    """
    import time
    import os

    # Return basic service info since Pipecat handles detailed metrics via OpenTelemetry
    otel_enabled = os.getenv("OTEL_TRACING_ENABLED", "false").lower() == "true"
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    return MetricsResponse(
        total_requests=0,  # Tracked by Pipecat/OpenTelemetry
        total_tokens_stt=0,  # Tracked by Pipecat/OpenTelemetry
        total_tokens_llm_input=0,  # Tracked by Pipecat/OpenTelemetry
        total_tokens_llm_output=0,  # Tracked by Pipecat/OpenTelemetry
        average_latency_ms=0.0,  # Tracked by Pipecat/OpenTelemetry
        error_rate=0.0,  # Tracked by Pipecat/OpenTelemetry
        uptime_seconds=0,  # Service-level metric
    )


@router.post(
    "/bot",
    response_model=ClinicalNoteResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Clinical Notes"],
)
async def create_clinical_note(
    request: SessionStartRequest, api_key: Optional[str] = Depends(api_key_header)
):
    """
    Generate a clinical note from voice dictation.

    This endpoint processes patient data and generates a structured clinical note
    using voice-to-text transcription and LLM processing.

    Metrics are automatically tracked by Pipecat's OpenTelemetry integration.

    Args:
        request: Session start request with patient data and configuration
        api_key: API key for authentication (from X-API-Key header)

    Returns:
        Generated clinical note with structured sections and codes

    Raises:
        HTTPException: If validation fails or processing errors occur
    """
    start_time = time.time()
    session_id = None

    try:
        # Validate patient data
        try:
            validated_data = validate_patient_data(request.patient_data)
        except ValidationException as e:
            logger.warning(f"Patient data validation failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        logger.info(f"Starting clinical note generation session")

        # TODO: Integrate with actual pipecat workflow
        # For now, this is a placeholder that would call the actual bot
        # The bot function needs to be refactored to work with FastAPI

        # Placeholder response - replace with actual bot integration
        result = {
            "past_medical_history": "",
            "allergies": "",
            "current_medication": "",
            "review_of_system": "",
            "history_of_present_illness": "",
            "examination": "",
            "assessment_and_plan": "",
            "procedure": "",
            "icd_codes": [],
            "cpt_codes": [],
        }

        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"Clinical note generated successfully in {latency_ms:.2f}ms")

        return ClinicalNoteResponse(
            **result, session_id=session_id, transcript_length=0
        )

    except ValidationException as e:
        latency_ms = (time.time() - start_time) * 1000
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Error generating clinical note: {str(e)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the clinical note",
        )
