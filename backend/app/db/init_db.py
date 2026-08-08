"""Criacao de tabelas, migracoes, configuracoes iniciais e admin."""

from __future__ import annotations

import secrets
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import BASE_DIR, settings
from app.core.logging_config import logger
from app.core.security import hash_password
from app.db.migrate import run_migrations
from app.db.session import Base, SessionLocal, engine
from app.models import ApiKey, Conversation, Message, RequestLog, Setting, User  # noqa: F401

# Defaults da tabela de configuracoes editaveis pelo painel
DEFAULT_SETTINGS: dict[str, str] = {
    "default_model": settings.DEFAULT_MODEL,
    "embedding_model": settings.DEFAULT_EMBEDDING_MODEL,
    "temperature": str(settings.DEFAULT_TEMPERATURE),
    "max_tokens": str(settings.DEFAULT_MAX_TOKENS),
    "timeout": str(settings.OLLAMA_TIMEOUT),
    "rate_limit_enabled": "true" if settings.RATE_LIMIT_ENABLED else "false",
    "rate_limit_requests": str(settings.RATE_LIMIT_REQUESTS),
    "rate_limit_window": str(settings.RATE_LIMIT_WINDOW_SECONDS),
    "platform_name": settings.PLATFORM_NAME,
    "platform_description": settings.PLATFORM_DESCRIPTION,
    "platform_logo": settings.PLATFORM_LOGO_URL,
}

CREDENTIALS_FILE = BASE_DIR / "data" / "initial-admin-password.txt"


def create_tables() -> None:
    """Cria as tabelas declaradas nos modelos (idempotente)."""
    Base.metadata.create_all(bind=engine)


def seed_settings(db: Session) -> None:
    """Insere as configuracoes padrao que ainda nao existem (nunca sobrescreve)."""
    existing = {row.key for row in db.query(Setting.key).all()}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            db.add(Setting(key=key, value=value))
    db.commit()


def _initial_admin_password() -> tuple[str, bool]:
    """Senha do admin: a do .env ou uma aleatoria forte (retorna se foi gerada)."""
    configured = (settings.ADMIN_PASSWORD or "").strip()
    if configured:
        return configured, False
    return secrets.token_urlsafe(12), True


def seed_admin(db: Session) -> None:
    """Cria o administrador inicial (idempotente).

    Sem ADMIN_PASSWORD no .env geramos uma senha aleatoria e a gravamos em
    `backend/data/initial-admin-password.txt` - nunca usamos senha padrao
    conhecida como "admin123".
    """
    email = settings.ADMIN_EMAIL.lower().strip()
    if db.query(User).filter(User.email == email).first():
        return
    if db.query(User).count() > 0:
        # Ja existe algum usuario: nao criamos um segundo admin automaticamente.
        return

    password, generated = _initial_admin_password()
    db.add(
        User(
            email=email,
            name=settings.ADMIN_NAME,
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
        )
    )
    db.commit()

    if generated:
        try:
            CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
            CREDENTIALS_FILE.write_text(
                "Arkium AI - credenciais iniciais do administrador\n"
                f"E-mail: {email}\n"
                f"Senha:  {password}\n\n"
                "Altere a senha no primeiro acesso (Perfil > Alterar senha) e apague este arquivo.\n",
                encoding="utf-8",
            )
            _restrict(CREDENTIALS_FILE)
        except OSError as exc:  # pragma: no cover
            logger.error("Nao foi possivel gravar as credenciais iniciais: %s", exc)
        logger.warning(
            "Administrador criado (%s). Senha gerada automaticamente em %s - altere no primeiro acesso.",
            email,
            CREDENTIALS_FILE,
        )
    else:
        logger.info("Administrador criado a partir do .env: %s", email)


def _restrict(path: Path) -> None:
    """Permissao 600 quando o sistema operacional suportar."""
    try:
        path.chmod(0o600)
    except (OSError, NotImplementedError):  # pragma: no cover - Windows
        pass


def init_db() -> None:
    """Ponto de entrada usado pelos instaladores e pelo startup da API."""
    create_tables()
    run_migrations(engine)
    db = SessionLocal()
    try:
        seed_settings(db)
        seed_admin(db)
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover - execucao manual
    init_db()
    print("Banco inicializado com sucesso.")
