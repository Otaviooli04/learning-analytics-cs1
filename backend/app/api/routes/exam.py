from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.orm import Exam, Question, QuestionCluster
from app.models.schemas import (
    ClusterInfo,
    ClusteringResponse,
    ClusterInsight,
    ExamResponse,
    ExamResultsResponse,
    InsightsResponse,
    QuestionResponse,
    ScatterPoint,
    TestCaseAddRequest,
)
from app.services.exam_service import process_exam_upload, add_test_cases, get_exam_results
from app.ml.cluster import FeatureStrategy, cluster_question
from app.llm.feedback_generator import generate_cluster_insights

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


@router.post("/{exam_id}/questions/{question_number}/cluster", response_model=ClusteringResponse)
def run_clustering(
    exam_id: int,
    question_number: str,
    strategy: FeatureStrategy = Query(default=FeatureStrategy.TFIDF),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(
        Question.exam_id == exam_id,
        Question.number == question_number,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    result = cluster_question(question.id, db, strategy=strategy)
    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Submissões insuficientes para clustering (mínimo 3).",
        )

    db.refresh(question)
    clusters_db = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == question.id
    ).all()

    clusters_map = {qc.cluster_label: qc for qc in clusters_db}
    clusters_out = [
        ClusterInfo(
            cluster_id=c["cluster_id"],
            size=c["size"],
            dominant_error=c["dominant_error"],
            representative_submission_id=clusters_map[c["cluster_id"]].representative_submission_id
            if c["cluster_id"] in clusters_map else None,
            representative_code=clusters_map[c["cluster_id"]].representative.code
            if c["cluster_id"] in clusters_map and clusters_map[c["cluster_id"]].representative else None,
        )
        for c in result.clusters
    ]

    scatter_out = [ScatterPoint(**p) for p in result.scatter]

    return ClusteringResponse(
        question_number=question_number,
        total_submissions=len(result.scatter),
        clusters=clusters_out,
        scatter=scatter_out,
        strategy=result.strategy.value,
        silhouette_score=result.silhouette,
    )


@router.post("/{exam_id}/questions/{question_number}/insights", response_model=InsightsResponse)
def run_insights(exam_id: int, question_number: str, db: Session = Depends(get_db)):
    question = db.query(Question).filter(
        Question.exam_id == exam_id,
        Question.number == question_number,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    clusters_db = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == question.id
    ).all()
    if not clusters_db:
        raise HTTPException(
            status_code=422,
            detail="Nenhum cluster encontrado. Execute o clustering antes de gerar insights.",
        )

    clusters_payload = [
        {
            "cluster_id": qc.cluster_label,
            "size": qc.size,
            "dominant_error": qc.dominant_error,
            "representative_code": qc.representative.code if qc.representative else "",
        }
        for qc in clusters_db
    ]

    try:
        raw_insights = generate_cluster_insights(question.statement, clusters_payload)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return InsightsResponse(
        question_number=question_number,
        insights=[ClusterInsight(**i) for i in raw_insights],
    )


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
