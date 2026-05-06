from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import CodeSubmissionRequest, CodeSubmissionResponse
from app.services.submission_service import evaluate_submission

router = APIRouter(prefix="/submission", tags=["submission"])


@router.post("/evaluate", response_model=CodeSubmissionResponse)
async def submit_answer(body: CodeSubmissionRequest, db: Session = Depends(get_db)):
    try:
        return evaluate_submission(body.exam_id, body.question_number, body.code, db, student_name=body.student_name, dry_run=body.dry_run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
