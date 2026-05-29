from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.auth.service import authenticate_professor, create_access_token, register_professor
from app.models.database import get_db
from app.models.orm import Professor
from app.models.schemas import ProfessorCreate, ProfessorResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: ProfessorCreate, db: Session = Depends(get_db)):
    try:
        professor = register_professor(body.email, body.nome, body.senha, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TokenResponse(
        access_token=create_access_token(professor.id),
        professor=_to_response(professor),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: ProfessorCreate, db: Session = Depends(get_db)):
    professor = authenticate_professor(body.email, body.senha, db)
    if not professor:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return TokenResponse(
        access_token=create_access_token(professor.id),
        professor=_to_response(professor),
    )


@router.get("/me", response_model=ProfessorResponse)
def me(current: Professor = Depends(get_current_professor)):
    return _to_response(current)


def _to_response(p: Professor) -> ProfessorResponse:
    return ProfessorResponse(
        id=p.id,
        email=p.email,
        nome=p.nome,
        created_at=p.created_at.isoformat(),
    )
