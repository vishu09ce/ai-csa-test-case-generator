from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.src.database import init_db
import os

app = FastAPI(
    title="AI-Powered CSA Test Case Generator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}
