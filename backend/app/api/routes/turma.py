from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import TurmaCreate, TurmaResponse, TurmaDetailResponse
from app.services.turma_service import create_turma, list_turmas, get_turma_detail

router = APIRouter(prefix="/turmas", tags=["turmas"])


@router.get("", response_model=list[TurmaResponse])
def get_turmas(db: Session = Depends(get_db)):
    return list_turmas(db)


@router.post("", response_model=TurmaDetailResponse)
def post_turma(body: TurmaCreate, db: Session = Depends(get_db)):
    turma = create_turma(body.nome, body.codigo, db)
    return get_turma_detail(turma.id, db)


@router.get("/{turma_id}", response_model=TurmaDetailResponse)
def get_turma(turma_id: int, db: Session = Depends(get_db)):
    detail = get_turma_detail(turma_id, db)
    if not detail:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return detail
