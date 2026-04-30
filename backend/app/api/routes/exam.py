from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.orm import Exam, Question
from app.models.schemas import ExamResponse, QuestionResponse, TestCaseAddRequest, ExamResultsResponse
from app.services.exam_service import process_exam_upload, add_test_cases, get_exam_results

router = APIRouter(prefix="/exam", tags=["exam"])


@router.post("/upload", response_model=ExamResponse)
async def upload_exam(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie PDF ou DOCX.")
    file_bytes = await file.read()
    try:
        exam = process_exam_upload(file_bytes, file.filename, db)
        return _exam_to_response(exam)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")
    return _exam_to_response(exam)


@router.post("/{exam_id}/questions/{question_number}/testcases")
def add_question_testcases(
    exam_id: int,
    question_number: str,
    body: TestCaseAddRequest,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(
        Question.exam_id == exam_id,
        Question.number == question_number,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    count = add_test_cases(question.id, [tc.model_dump() for tc in body.test_cases], db)
    return {"added": count, "question_number": question_number}


@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
def get_results(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")
    return get_exam_results(exam)


def _exam_to_response(exam: Exam) -> ExamResponse:
    return ExamResponse(
        id=exam.id,
        filename=exam.filename,
        questions=[
            QuestionResponse(
                id=q.id,
                number=q.number,
                statement=q.statement,
                required_structures=q.required_structures or [],
                forbidden_structures=q.forbidden_structures or [],
                requires_loop=q.requires_loop,
                test_case_count=len(q.test_cases),
            )
            for q in exam.questions
        ],
    )
