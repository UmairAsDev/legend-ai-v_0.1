from fastapi import APIRouter
from workflow.bot import main








router  = APIRouter(prefix="/api/v1")

@router.post("/bot")
async def bot(patient_data: dict):
    try:
        if not patient_data:
            return {"error": "No patient data provided"}
    except Exception as e:
        return {"error": str(e)}
    return await main(patient_data)







