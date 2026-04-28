from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    CodeRequest, CompileResponse, ASTResponse, SubmissionResponse,
    ExerciseRequest, ExerciseMetadata,
)
from app.engine.dynamic_analyzer import compile_c_code
from app.engine.static_analyzer import extract_control_flow
from app.services.submission_service import evaluate_submission
from app.services.exercise_service import analyze_exercise_prompt

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "online", "system": "Learning Analytics Project"}


@router.post("/evaluate", response_model=CompileResponse)
async def evaluate_code(payload: CodeRequest):
    return compile_c_code(payload.code)


@router.post("/ast", response_model=ASTResponse)
async def analyze_ast(payload: CodeRequest):
    return extract_control_flow(payload.code)


@router.post("/submission", response_model=SubmissionResponse)
async def submit_code(payload: CodeRequest):
    return evaluate_submission(payload.code)


@router.post("/exercise", response_model=ExerciseMetadata)
async def analyze_exercise(payload: ExerciseRequest):
    try:
        return analyze_exercise_prompt(payload.prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
