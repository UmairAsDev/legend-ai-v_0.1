from typing import Dict, Any, List
from pydantic import ValidationError
from monitoring.logger import get_logger

logger = get_logger()


class ValidationException(Exception):
    """Custom validation exception."""

    pass


def validate_patient_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate patient data structure.

    Args:
        patient_data: Patient data dictionary

    Returns:
        Validated patient data

    Raises:
        ValidationException: If validation fails
    """
    if not isinstance(patient_data, dict):
        raise ValidationException("patient_data must be a dictionary")

    if not patient_data:
        raise ValidationException("patient_data cannot be empty")

    # Log sanitized version
    logger.debug(f"Validating patient data with {len(patient_data)} fields")

    return patient_data


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text input.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        ValidationException: If validation fails
    """
    if not isinstance(text, str):
        raise ValidationException("Input must be a string")

    # Remove null bytes
    text = text.replace("\x00", "")

    # Trim to max length
    if len(text) > max_length:
        logger.warning(
            f"Input text truncated from {len(text)} to {max_length} characters"
        )
        text = text[:max_length]

    return text


def validate_transcript(transcript: str) -> bool:
    """
    Validate transcript content.

    Args:
        transcript: Transcript text

    Returns:
        True if valid, False otherwise
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript received")
        return False

    # Check minimum length (at least 10 characters for meaningful content)
    if len(transcript.strip()) < 10:
        logger.warning(f"Transcript too short: {len(transcript)} characters")
        return False

    return True


def validate_clinical_note_response(response: Dict[str, Any]) -> bool:
    """
    Validate LLM response for clinical note.

    Args:
        response: LLM response dictionary

    Returns:
        True if valid, False otherwise
    """
    # Check for error response
    if "error" in response:
        logger.warning(f"LLM returned error response: {response.get('error')}")
        return False

    # Check for at least one populated field
    required_fields = [
        "past_medical_history",
        "allergies",
        "current_medication",
        "review_of_system",
        "history_of_present_illness",
        "examination",
        "assessment_and_plan",
        "procedure",
    ]

    has_content = any(
        response.get(field) and response.get(field).strip() for field in required_fields
    )

    if not has_content:
        logger.warning("Clinical note response has no populated fields")
        return False

    return True


def extract_json_from_response(text: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response text.

    Args:
        text: Response text that may contain JSON

    Returns:
        Extracted JSON dictionary

    Raises:
        ValidationException: If JSON extraction fails
    """
    import json
    import re

    # Try to find JSON in the response
    # Look for content between curly braces
    json_match = re.search(r"\{.*\}", text, re.DOTALL)

    if not json_match:
        raise ValidationException("No JSON found in response")

    try:
        json_str = json_match.group(0)
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        raise ValidationException(f"Invalid JSON in response: {str(e)}")
