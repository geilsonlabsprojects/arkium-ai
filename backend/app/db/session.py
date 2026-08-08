"""Engine, sessao e Base declarativa do SQLAlchemy.

Trocar `DATABASE_URL` no .env (ex.: PostgreSQL) migra o projeto sem alterar
codigo. Para SQLite habilitamos WAL e chaves estrangeiras, que o SQLite
desliga por padrao - sem isso os `ON DELETE CASCADE` do schema nao funcionam.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import BASE_DIR, settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos."""


def resolve_database_url(url: str | None = None) -> str:
    """Normaliza a URL do banco (paths relativos viram absolutos)."""
    url = url or settings.DATABASE_URL
    if not url.startswith("sqlite"):
        return url
    raw_path = url.split("sqlite:///")[-1]
    if raw_path in ("", ":memory:"):
        return url
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = (BASE_DIR / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def database_file() -> Path | None:
    """Caminho do arquivo .db quando o banco e SQLite (usado por backup)."""
    url = resolve_database_url()
    if not url.startswith("sqlite:///") or url.endswith(":memory:"):
        return None
    return Path(url.replace("sqlite:///", "", 1))


def _build_engine() -> Engine:
    url = resolve_database_url()
    kwargs: dict = {"pool_pre_ping": True, "echo": settings.DB_ECHO, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = _build_engine()


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - driver level
    """Ativa integridade referencial e modo WAL no SQLite."""
    if not settings.is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI: uma sessao por requisicao, sempre fechada."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
