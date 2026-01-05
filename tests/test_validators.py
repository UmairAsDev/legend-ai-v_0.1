import pytest
from utils.validators import (
    validate_patient_data,
    validate_transcript,
    validate_clinical_note_response,
    sanitize_input,
    ValidationException,
)


def test_validate_patient_data_valid():
    """Test patient data validation with valid data."""
    data = {"patient_id": "123", "name": "John Doe"}
    result = validate_patient_data(data)
    assert result == data


def test_validate_patient_data_empty():
    """Test patient data validation with empty data."""
    with pytest.raises(ValidationException):
        validate_patient_data({})


def test_validate_patient_data_invalid_type():
    """Test patient data validation with invalid type."""
    with pytest.raises(ValidationException):
        validate_patient_data("not a dict")


def test_validate_transcript_valid():
    """Test transcript validation with valid transcript."""
    assert validate_transcript(
        "This is a valid medical transcript with sufficient length"
    )


def test_validate_transcript_empty():
    """Test transcript validation with empty transcript."""
    assert not validate_transcript("")
    assert not validate_transcript("   ")


def test_validate_transcript_too_short():
    """Test transcript validation with too short transcript."""
    assert not validate_transcript("short")


def test_sanitize_input_valid():
    """Test input sanitization with valid input."""
    result = sanitize_input("Normal text input")
    assert result == "Normal text input"


def test_sanitize_input_with_null_bytes():
    """Test input sanitization removes null bytes."""
    result = sanitize_input("Text\x00with\x00nulls")
    assert "\x00" not in result


def test_sanitize_input_max_length():
    """Test input sanitization truncates long input."""
    long_text = "a" * 15000
    result = sanitize_input(long_text, max_length=10000)
    assert len(result) == 10000


def test_validate_clinical_note_response_valid():
    """Test clinical note response validation with valid response."""
    response = {
        "past_medical_history": "Hypertension",
        "allergies": "None",
        "assessment_and_plan": "Continue current treatment",
    }
    assert validate_clinical_note_response(response)


def test_validate_clinical_note_response_error():
    """Test clinical note response validation with error response."""
    response = {"error": "Insufficient content"}
    assert not validate_clinical_note_response(response)


def test_validate_clinical_note_response_empty():
    """Test clinical note response validation with empty fields."""
    response = {"past_medical_history": "", "allergies": "", "assessment_and_plan": ""}
    assert not validate_clinical_note_response(response)
