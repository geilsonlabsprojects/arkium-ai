"""Endpoints publicos de saude e identidade da plataforma."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import settings
from app.db.session import get_db
from app.services import settings_service
from app.services.ollama_service import ollama_service

router = APIRouter(tags=["Sistema"])


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    """Health check usado por scripts, monitores e load balancers."""
    try:
        settings_service.get_all(db)
        database = "online"
    except Exception:  # pragma: no cover
        database = "offline"
    return {
        "status": "ok",
        "version": __version__,
        "database": database,
        "ollama": "online" if await ollama_service.is_online() else "offline",
    }


@router.get("/api/platform")
def platform(db: Session = Depends(get_db)) -> dict:
    """Identidade visual da plataforma (consumida pelo frontend antes do login)."""
    values = settings_service.get_all(db)
    return {
        "name": values.get("platform_name", settings.PLATFORM_NAME),
        "description": values.get("platform_description", settings.PLATFORM_DESCRIPTION),
        "logo": values.get("platform_logo", settings.PLATFORM_LOGO_URL),
        "version": __version__,
    }
