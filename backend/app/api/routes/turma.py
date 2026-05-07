from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.models.database import get_db
from app.models.orm import Professor
from app.models.schemas import TurmaCreate, TurmaDetailResponse, TurmaResponse
from app.services.turma_service import create_turma, get_turma_detail, list_turmas

router = APIRouter(prefix="/turmas", tags=["turmas"])


@router.get("", response_model=list[TurmaResponse])
def get_turmas(
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    return list_turmas(db, professor_id=professor.id)


@router.post("", response_model=TurmaDetailResponse)
def post_turma(
    body: TurmaCreate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    turma = create_turma(body.nome, body.codigo, db, professor_id=professor.id)
    return get_turma_detail(turma.id, db)


@router.get("/{turma_id}", response_model=TurmaDetailResponse)
def get_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    detail = get_turma_detail(turma_id, db, professor_id=professor.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return detail
