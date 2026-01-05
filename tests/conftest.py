import pytest


# Shared test fixtures
@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {"patient_id": "12345", "name": "John Doe", "age": 45, "gender": "M"}


@pytest.fixture
def sample_clinical_note():
    """Sample clinical note for testing."""
    return {
        "past_medical_history": "<p>Hypertension, Type 2 Diabetes</p>",
        "allergies": "<p>Penicillin</p>",
        "current_medication": "<p>Metformin 500mg BID</p>",
        "assessment_and_plan": "<p><strong>Hypertension</strong>: Continue current medication</p>",
        "icd_codes": [{"code": "I10", "description": "Essential hypertension"}],
        "cpt_codes": [{"code": "99213", "description": "Office visit"}],
    }
