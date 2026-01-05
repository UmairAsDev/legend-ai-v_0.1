from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class SessionConfig(BaseModel):
    """Configuration for the dictation session."""

    note_style: Literal["focused", "comprehensive", "categorized"] = Field(
        default="comprehensive", description="Style of the clinical note to generate"
    )
    include_icd_codes: bool = Field(
        default=True, description="Whether to include ICD codes in the output"
    )
    include_cpt_codes: bool = Field(
        default=True, description="Whether to include CPT codes in the output"
    )
    max_session_duration: int = Field(
        default=1800,  # 30 minutes
        ge=60,
        le=3600,
        description="Maximum session duration in seconds",
    )


class SessionStartRequest(BaseModel):
    """Request model for starting a dictation session."""

    patient_data: Dict[str, Any] = Field(
        ..., description="Patient context data for the clinical note"
    )
    config: Optional[SessionConfig] = Field(
        default=None, description="Optional session configuration"
    )

    @field_validator("patient_data")
    @classmethod
    def validate_patient_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that patient_data is not empty."""
        if not v:
            raise ValueError("patient_data cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "patient_data": {
                    "patient_id": "12345",
                    "name": "John Doe",
                    "age": 45,
                    "gender": "M",
                },
                "config": {
                    "note_style": "comprehensive",
                    "include_icd_codes": True,
                    "include_cpt_codes": True,
                },
            }
        }
