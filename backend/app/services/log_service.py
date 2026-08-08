"""Persistencia dos logs de requisicao."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models import RequestLog


def record(
    db: Session,
    *,
    endpoint: str,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    model: Optional[str] = None,
    status_code: int = 200,
    duration_ms: float = 0.0,
    usage: Optional[dict] = None,
    ip_address: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Grava uma linha de log; nunca deixa uma falha de log quebrar a request."""
    usage = usage or {}
    try:
        db.add(
            RequestLog(
                user_id=user_id,
                api_key_id=api_key_id,
                endpoint=endpoint,
                model=model,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                ip_address=ip_address,
                error=error,
            )
        )
        db.commit()
    except Exception as exc:  # pragma: no cover
        db.rollback()
        logger.error("Falha ao gravar log de requisicao: %s", exc)
