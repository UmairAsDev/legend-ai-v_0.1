from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ICDCode(BaseModel):
    """ICD code model."""

    code: str = Field(..., description="ICD code")
    description: str = Field(..., description="Code description")


class CPTCode(BaseModel):
    """CPT code model."""

    code: str = Field(..., description="CPT code")
    description: str = Field(..., description="Code description")


class ClinicalNoteResponse(BaseModel):
    """Response model for generated clinical note."""

    past_medical_history: str = Field(default="", description="Past medical history")
    allergies: str = Field(default="", description="Allergies")
    current_medication: str = Field(default="", description="Current medications")
    review_of_system: str = Field(default="", description="Review of systems")
    history_of_present_illness: str = Field(
        default="", description="History of present illness"
    )
    examination: str = Field(default="", description="Physical examination")
    assessment_and_plan: str = Field(default="", description="Assessment and plan")
    procedure: str = Field(default="", description="Procedures performed")
    icd_codes: List[ICDCode] = Field(default_factory=list, description="ICD codes")
    cpt_codes: List[CPTCode] = Field(default_factory=list, description="CPT codes")

    # Metadata
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    generated_at: Optional[datetime] = Field(
        default=None, description="Generation timestamp"
    )
    transcript_length: Optional[int] = Field(
        default=None, description="Length of transcript in characters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "past_medical_history": "<p>Hypertension, Type 2 Diabetes</p>",
                "allergies": "<p>Penicillin</p>",
                "current_medication": "<p>Metformin 500mg BID, Lisinopril 10mg daily</p>",
                "assessment_and_plan": "<p><strong><u>Hypertension</u></strong>: Continue current medication</p>",
                "icd_codes": [{"code": "I10", "description": "Essential hypertension"}],
                "cpt_codes": [{"code": "99213", "description": "Office visit"}],
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(
        default=None, description="Error code for categorization"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid patient data format",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2026-01-05T16:00:00Z",
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Status of individual services")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "services": {"deepgram": "healthy", "aws_bedrock": "healthy"},
                "timestamp": "2026-01-05T16:00:00Z",
            }
        }


class MetricsResponse(BaseModel):
    """Metrics response for monitoring."""

    total_requests: int = Field(default=0, description="Total requests processed")
    total_tokens_stt: int = Field(default=0, description="Total STT tokens used")
    total_tokens_llm_input: int = Field(default=0, description="Total LLM input tokens")
    total_tokens_llm_output: int = Field(
        default=0, description="Total LLM output tokens"
    )
    average_latency_ms: float = Field(
        default=0.0, description="Average request latency in milliseconds"
    )
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    uptime_seconds: int = Field(default=0, description="Service uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "total_requests": 150,
                "total_tokens_stt": 45000,
                "total_tokens_llm_input": 12000,
                "total_tokens_llm_output": 8000,
                "average_latency_ms": 2500.5,
                "error_rate": 1.2,
                "uptime_seconds": 86400,
            }
        }
