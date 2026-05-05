from pydantic import BaseModel
from typing import List, Optional, Literal


class TestCase(BaseModel):
    input: str
    expected_output: str


class TestResult(BaseModel):
    input: str
    expected_output: str
    actual_output: str
    passed: bool


class StructureCheck(BaseModel):
    compliant: bool
    missing_required: List[str] = []
    found_forbidden: List[str] = []


class DiagnosisResult(BaseModel):
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str


class CodeQuestion(BaseModel):
    number: str
    type: Literal["code"] = "code"
    statement: str
    required_structures: List[str] = []
    forbidden_structures: List[str] = []
    requires_loop: bool = False


class ExamStructure(BaseModel):
    questions: List[CodeQuestion]


class ExamUploadResponse(BaseModel):
    raw_text: str
    structure: ExamStructure


class CodeSubmissionRequest(BaseModel):
    exam_id: int
    question_number: str
    code: str


class CodeSubmissionResponse(BaseModel):
    question_number: str
    compile_error: str = ""
    warnings: str = ""
    test_results: List[TestResult] = []
    all_tests_passed: Optional[bool] = None
    structure_check: Optional[StructureCheck] = None
    diagnosis: DiagnosisResult


class TestCaseAddRequest(BaseModel):
    test_cases: List[TestCase]


class QuestionResponse(BaseModel):
    id: int
    number: str
    statement: str
    required_structures: List[str]
    forbidden_structures: List[str]
    requires_loop: bool
    test_case_count: int


class ExamResponse(BaseModel):
    id: int
    filename: str
    questions: List[QuestionResponse]


class SubmissionResult(BaseModel):
    id: int
    code: str
    all_tests_passed: Optional[bool]
    compile_error: str
    diagnosis: DiagnosisResult
    submitted_at: str


class ErrorCount(BaseModel):
    error_category: str
    count: int


class QuestionResults(BaseModel):
    question_number: str
    statement: str
    total_submissions: int
    passed_count: int
    error_distribution: List[ErrorCount]
    submissions: List[SubmissionResult]


class ExamResultsResponse(BaseModel):
    exam_id: int
    filename: str
    questions: List[QuestionResults]


class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    dominant_error: str
    representative_submission_id: Optional[int]
    representative_code: Optional[str]


class ScatterPoint(BaseModel):
    submission_id: int
    x: float
    y: float
    cluster_id: int


class ClusteringResponse(BaseModel):
    question_number: str
    total_submissions: int
    clusters: List[ClusterInfo]
    scatter: List[ScatterPoint]
    strategy: str
    silhouette_score: Optional[float] = None


class ClusterInsight(BaseModel):
    cluster_id: int
    size: int
    dominant_error: str
    insight: str


class InsightsResponse(BaseModel):
    question_number: str
    insights: List[ClusterInsight]
