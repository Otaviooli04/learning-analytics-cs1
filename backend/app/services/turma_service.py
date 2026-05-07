from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orm import Turma


def create_turma(nome: str, codigo: str, db: Session, professor_id: int | None = None) -> Turma:
    turma = Turma(nome=nome, codigo=codigo, created_at=datetime.utcnow(), professor_id=professor_id)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


def list_turmas(db: Session, professor_id: int | None = None) -> list:
    q = db.query(Turma)
    if professor_id is not None:
        q = q.filter(Turma.professor_id == professor_id)
    turmas = q.order_by(Turma.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "nome": t.nome,
            "codigo": t.codigo,
            "created_at": t.created_at.isoformat(),
            "exam_count": len(t.exams),
        }
        for t in turmas
    ]


def get_turma_detail(turma_id: int, db: Session, professor_id: int | None = None) -> dict | None:
    q = db.query(Turma).filter(Turma.id == turma_id)
    if professor_id is not None:
        q = q.filter(Turma.professor_id == professor_id)
    turma = q.first()
    if not turma:
        return None
    exams = []
    for exam in turma.exams:
        submission_count = sum(len(q2.submissions) for q2 in exam.questions)
        exams.append({
            "id": exam.id,
            "filename": exam.filename,
            "created_at": exam.created_at.isoformat(),
            "question_count": len(exam.questions),
            "submission_count": submission_count,
        })
    return {
        "id": turma.id,
        "nome": turma.nome,
        "codigo": turma.codigo,
        "created_at": turma.created_at.isoformat(),
        "exams": exams,
    }
