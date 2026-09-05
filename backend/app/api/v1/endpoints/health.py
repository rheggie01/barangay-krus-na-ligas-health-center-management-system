from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine


router = APIRouter()


@router.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "backend": "connected",
            "database": "connected",
        }

    except SQLAlchemyError:
        return {
            "status": "error",
            "backend": "connected",
            "database": "disconnected",
        }