from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Learning Analytics Project")

app.include_router(router)
