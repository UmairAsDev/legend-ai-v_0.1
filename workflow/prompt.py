import sys
import asyncio
from pathlib import Path    
sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from loguru import logger
from config.settings import PatientModel






def prompt_with_context(patient_data: dict) -> dict:
    """Generate a system prompt for clinical transcription with context."""
    
    context_prompt = {
        "role": "system",
        "content": (
            f"""This is dictated by a doctor to a voice assistant to generate a clinical note based on this information. While dictating, there might be transcription errors (e.g., wrong medical terms, drug names, or procedures).
          Your task:
             Also Analyze the following patient data for additional context:
          {patient_data}
          1. Identify and correct any transcription mistakes in the dictation (for example, "iron olecranon" → "isotretinoin", "creatinine" → "tretinoin", "resistantectomy" → "resistant acne").
          2. Extract the clinical information and create a structured clinical note in the following JSON format:
          3. 
          {
            "past_medical_history": "",
            "allergies": "",
            "current_medication": "",
            "review_of_system": "",
            "history_of_present_illness": "",
            "examination": "",
            "assessment_and_plan": "",
            "procedure": "",
            "icdCodes": [{
              "Code": "",
              "Description": ""
            }],
            "cptCodes": [{
              "Code": "",
              "Description": ""
            }]
          }
          Rules:
          - Only include information that is explicitly stated or clearly implied in the transcript.
          - Correct transcription errors intelligently using medical context.
          - Give Correct icdCodes and cptCodes for the clinical note
          - Must Produce HTML for each sections. Use proper heading for diagnosis names bold and underlined and don't use bullet points or numbering and put them in the JSON format provided above.
          - You may find some HTML templates in the transcript, You must keep the HTML templates unchanged in the transcript and put the necessary information in those structured templates.
          Strict Rule: Do not add any headings or section titles inside the content of the JSON fields. The keys in the JSON object (e.g., "past_medical_history", "history_of_present_illness", "assessment_and_plan") already act as section identifiers. The HTML content inside each field must only include the relevant information, not an extra heading or label.
          - If atleast one of the field contains relevant data, return the JSON object with all the fields (empty or filled).
          - If no relevant or sufficient medical content exists, return:
          {
            "error": "Insufficient or unrelated content"
          }
          - Format the note dynamically based on the requested style:
            - Focused → concise, essential details only.
            - Comprehensive → detailed, narrative-style documentation.
            - Categorized → structured, bullet-like content inside each field.
          - Output must be ONLY the JSON object"""
        )
    }
    return context_prompt








