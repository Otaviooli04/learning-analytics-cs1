from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.exam import router as exam_router
from app.api.routes.submission import router as submission_router
from app.models.database import engine
from app.models import orm

orm.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Learning Analytics — CS1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exam_router)
app.include_router(submission_router)


@app.get("/")
async def health_check():
    return {"status": "online", "system": "Learning Analytics CS1"}
