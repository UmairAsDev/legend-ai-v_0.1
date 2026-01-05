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
from monitoring.metrics_collector import metrics_collector
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
    Get application metrics including token usage and performance stats.

    Returns comprehensive metrics for monitoring and cost tracking.
    """
    metrics = metrics_collector.get_metrics()

    return MetricsResponse(
        total_requests=metrics["total_requests"],
        total_tokens_stt=metrics["total_tokens_stt"],
        total_tokens_llm_input=metrics["total_tokens_llm_input"],
        total_tokens_llm_output=metrics["total_tokens_llm_output"],
        average_latency_ms=metrics["average_latency_ms"],
        error_rate=metrics["error_rate"],
        uptime_seconds=metrics["uptime_seconds"],
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
        # Increment active sessions
        metrics_collector.increment_active_sessions()

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

        # Record successful request
        latency_ms = (time.time() - start_time) * 1000
        metrics_collector.record_request(success=True, latency_ms=latency_ms)

        logger.info(f"Clinical note generated successfully in {latency_ms:.2f}ms")

        return ClinicalNoteResponse(
            **result, session_id=session_id, transcript_length=0
        )

    except ValidationException as e:
        # Record failed request
        latency_ms = (time.time() - start_time) * 1000
        metrics_collector.record_request(success=False, latency_ms=latency_ms)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        # Record failed request
        latency_ms = (time.time() - start_time) * 1000
        metrics_collector.record_request(success=False, latency_ms=latency_ms)

        logger.error(f"Error generating clinical note: {str(e)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the clinical note",
        )

    finally:
        # Decrement active sessions
        metrics_collector.decrement_active_sessions()
