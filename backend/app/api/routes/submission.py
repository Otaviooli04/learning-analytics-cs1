from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.submission_service import evaluate_submission

router = APIRouter(prefix="/submission", tags=["submission"])


class SubmissionRequest(BaseModel):
    question_type: str
    payload: dict


@router.post("/evaluate")
async def submit_answer(body: SubmissionRequest):
    try:
        return evaluate_submission(body.question_type, body.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
