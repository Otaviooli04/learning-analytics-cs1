from pydantic import BaseModel
from typing import List, Optional


class CodeRequest(BaseModel):
    code: str


class ExerciseRequest(BaseModel):
    prompt: str


class CompileResponse(BaseModel):
    success: bool
    message: str = ""
    warnings: str = ""


class ASTResponse(BaseModel):
    success: bool
    structures: List[str] = []
    error: Optional[str] = None


class ExerciseMetadata(BaseModel):
    requires_loop: bool
    required_structures: List[str]
    forbidden_structures: List[str]


class DiagnosisResult(BaseModel):
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str


class SubmissionResponse(BaseModel):
    dynamic: CompileResponse
    static: ASTResponse
    diagnosis: DiagnosisResult
