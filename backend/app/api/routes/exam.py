from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.exam_service import process_exam_upload

router = APIRouter(prefix="/exam", tags=["exam"])


@router.post("/upload")
async def upload_exam(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie PDF ou DOCX.")
    file_bytes = await file.read()
    try:
        return process_exam_upload(file_bytes, file.filename)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
