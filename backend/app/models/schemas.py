from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal


class ProfessorCreate(BaseModel):
    email: str
    nome: str = ""
    senha: str


class ProfessorResponse(BaseModel):
    id: int
    email: str
    nome: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    professor: ProfessorResponse


class TurmaCreate(BaseModel):
    nome: str
    codigo: str


class ExamSummary(BaseModel):
    id: int
    filename: str
    created_at: str
    question_count: int
    submission_count: int


class TurmaResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    created_at: str
    exam_count: int


class TurmaDetailResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    created_at: str
    exams: List[ExamSummary]


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
    matricula: Optional[str] = None
    dry_run: bool = False


class BulkSubmissionItem(BaseModel):
    matricula: str
    question: Optional[str]
    file: str
    status: str
    message: str


class BulkSubmissionResponse(BaseModel):
    total: int
    processed: int
    errors: int
    items: List[BulkSubmissionItem]


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


class TestCaseResponse(BaseModel):
    id: int
    input: str
    expected_output: str


class TestCaseUpdateRequest(BaseModel):
    input: str
    expected_output: str


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
    created_at: str
    turma_id: Optional[int] = None
    turma_nome: Optional[str] = None
    questions: List[QuestionResponse]


class SubmissionResult(BaseModel):
    id: int
    code: str
    all_tests_passed: Optional[bool]
    compile_error: str
    diagnosis: DiagnosisResult
    submitted_at: str
    matricula: Optional[str] = None
    test_results: List[TestResult] = []


class QuestionSubmissionsResponse(BaseModel):
    question_number: str
    statement: str
    submissions: List[SubmissionResult]


class StudentQuestionStatus(BaseModel):
    question_number: str
    submission_id: Optional[int]
    passed: Optional[bool]
    error_category: Optional[str]


class StudentSummary(BaseModel):
    matricula: str
    questions: List[StudentQuestionStatus]
    answered_count: int
    passed_count: int
    total_questions: int


class ExamStudentsResponse(BaseModel):
    question_numbers: List[str]
    students: List[StudentSummary]


class StudentSubmissionDetail(BaseModel):
    question_number: str
    statement: str
    submission_id: Optional[int]
    code: Optional[str]
    all_tests_passed: Optional[bool]
    compile_error: str
    error_category: str
    pedagogical_diagnosis: str
    actionable_feedback: str
    submitted_at: Optional[str]
    test_results: List[TestResult]


class StudentDetailResponse(BaseModel):
    matricula: str
    total_questions: int
    passed_count: int
    answered_count: int
    submissions: List[StudentSubmissionDetail]


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


class ExamAnalytics(BaseModel):
    id: int
    filename: str
    created_at: str
    pass_rate: Optional[float]
    total_submissoes: int
    total_alunos: int


class TurmaAnalyticsResponse(BaseModel):
    turma_id: int
    total_alunos: int
    aproveitamento_medio: Optional[float]
    total_submissoes: int
    provas: List[ExamAnalytics]
    top_erros: List[ErrorCount]
