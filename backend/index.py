from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from backend.src.database import init_db
from backend.src.routes import projects, uploads, generation, files, status
from backend.src.utils.error_handler import (
    validation_exception_handler, sqlalchemy_exception_handler, generic_exception_handler
)
import asyncio
import os
import shutil
from backend.src.utils.file_store import STORAGE_ROOT
from backend.src.services.keep_alive import get_keep_alive_url, get_interval_seconds, run_keep_alive
from backend.src.utils.logger import get_logger

logger = get_logger("backend.startup")

load_dotenv()

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="AI-Powered CSA Test Case Generator",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(uploads.router)
app.include_router(generation.router)
app.include_router(files.router)
app.include_router(status.router)


@app.on_event("startup")
async def on_startup():
    init_db()
    logger.info(
        "Startup: cwd=%s storage=%s db=%s soffice=%s",
        os.getcwd(), os.path.abspath(STORAGE_ROOT), os.path.abspath("app.db"),
        shutil.which("soffice") or shutil.which("libreoffice"),
    )
    keep_alive_url = get_keep_alive_url()
    if keep_alive_url:
        app.state.keep_alive_task = asyncio.create_task(
            run_keep_alive(keep_alive_url, get_interval_seconds())
        )


@app.on_event("shutdown")
async def on_shutdown():
    task = getattr(app.state, "keep_alive_task", None)
    if task:
        task.cancel()


@app.get("/health")
def health_check():
    return {"status": "ok"}
