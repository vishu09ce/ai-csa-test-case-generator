from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = [f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in errors]
    return JSONResponse(
        status_code=422,
        content={"detail": " | ".join(messages)}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again."}
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )
