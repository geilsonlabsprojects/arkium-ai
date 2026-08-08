"""Logging estruturado: console + arquivo rotativo, com request id e redacao."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import BASE_DIR, settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | rid=%(request_id)s | %(message)s"

# Padroes de segredo que nunca podem ir para o log
_REDACTIONS = [
    (re.compile(r"(ark-[A-Za-z0-9_\-]{6})[A-Za-z0-9_\-]+"), r"\1***"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"), r"\1***"),
    (re.compile(r"(?i)(\"?(?:password|secret|token|api[_-]?key)\"?\s*[:=]\s*\"?)([^\s\",}]+)"), r"\1***"),
]


def redact(message: str) -> str:
    """Remove senhas, tokens e API keys de qualquer texto antes de gravar."""
    for pattern, replacement in _REDACTIONS:
        message = pattern.sub(replacement, message)
    return message


class ContextFilter(logging.Filter):
    """Injeta o request id corrente e aplica redacao."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        return True


class JsonFormatter(logging.Formatter):
    """Formata cada linha como JSON (util para ferramentas de observabilidade)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": redact(record.getMessage()),
            "module": record.module,
        }
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def log_dir() -> Path:
    directory = Path(settings.LOG_DIR)
    if not directory.is_absolute():
        directory = BASE_DIR / directory
    return directory


def setup_logging() -> logging.Logger:
    """Inicializa handlers globais e devolve o logger da aplicacao."""
    directory = log_dir()
    formatter: logging.Formatter = JsonFormatter() if settings.LOG_JSON else logging.Formatter(_TEXT_FORMAT)

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.addFilter(ContextFilter())
    root.addHandler(console)

    try:
        directory.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            directory / "arkium.log",
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        root.addHandler(file_handler)
    except OSError as exc:  # pragma: no cover - disco cheio / permissao
        root.warning("Log em arquivo desativado (%s): %s", directory, exc)

    # Menos ruido do uvicorn: o middleware da app ja registra cada requisicao
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger("arkium")


logger = logging.getLogger("arkium")
