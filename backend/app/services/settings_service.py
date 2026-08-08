"""Leitura e escrita das configuracoes armazenadas no banco."""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.config import settings as env_settings
from app.models import Setting


def get_all(db: Session) -> Dict[str, str]:
    """Todas as configuracoes como dicionario."""
    return {s.key: s.value for s in db.query(Setting).all()}


def get_value(db: Session, key: str, default: str = "") -> str:
    """Valor de uma configuracao (com fallback)."""
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else default


def update_many(db: Session, values: Dict[str, str]) -> Dict[str, str]:
    """Atualiza/insere varias configuracoes de uma vez."""
    for key, value in values.items():
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    db.commit()
    return get_all(db)


def inference_defaults(db: Session) -> Dict[str, Any]:
    """Defaults de inferencia (banco tem prioridade sobre o .env)."""
    data = get_all(db)

    def _float(key: str, fallback: float) -> float:
        try:
            return float(data.get(key, fallback))
        except (TypeError, ValueError):
            return fallback

    def _int(key: str, fallback: int) -> int:
        try:
            return int(float(data.get(key, fallback)))
        except (TypeError, ValueError):
            return fallback

    return {
        "model": data.get("default_model") or env_settings.DEFAULT_MODEL,
        "temperature": _float("temperature", env_settings.DEFAULT_TEMPERATURE),
        "max_tokens": _int("max_tokens", env_settings.DEFAULT_MAX_TOKENS),
        "rate_limit_requests": _int("rate_limit_requests", env_settings.RATE_LIMIT_REQUESTS),
        "rate_limit_window": _int("rate_limit_window", env_settings.RATE_LIMIT_WINDOW_SECONDS),
    }
