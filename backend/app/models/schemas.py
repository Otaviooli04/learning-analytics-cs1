from pydantic import BaseModel
from typing import List, Optional, Literal


class CodeRequest(BaseModel):
    code: str


class CompileResponse(BaseModel):
    success: bool
    message: str = ""
    warnings: str = ""


class ASTResponse(BaseModel):
    success: bool
    structures: List[str] = []
    error: Optional[str] = None


class DiagnosisResult(BaseModel):
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str


class SubmissionResponse(BaseModel):
    dynamic: CompileResponse
    static: ASTResponse
    diagnosis: DiagnosisResult


class TestCase(BaseModel):
    input: str
    expected_output: str


class QuestionBase(BaseModel):
    number: str
    statement: str


class CodeQuestion(QuestionBase):
    type: Literal["code"]
    required_structures: List[str] = []
    forbidden_structures: List[str] = []
    requires_loop: bool = False
    test_cases: List[TestCase] = []


class DissertativeQuestion(QuestionBase):
    type: Literal["dissertative"]
    rubric: str = ""


class MultipleChoiceQuestion(QuestionBase):
    type: Literal["multiple_choice"]
    options: List[str] = []
    expected_answer: str = ""


class ExamStructure(BaseModel):
    questions: List[CodeQuestion | DissertativeQuestion | MultipleChoiceQuestion]


class ExamUploadResponse(BaseModel):
    raw_text: str
    structure: ExamStructure
