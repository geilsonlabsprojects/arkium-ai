"""Migracoes leves e idempotentes.

O projeto usa `create_all` para tabelas novas; este modulo cuida do que o
`create_all` nao faz: adicionar colunas e indices em bancos ja existentes.
Nenhuma migracao apaga dados - atualizar o Arkium nunca perde usuarios,
chaves, conversas ou logs.
"""

from __future__ import annotations

from typing import Callable, List, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.logging_config import logger

# (tabela, coluna, DDL da coluna)
COLUMN_MIGRATIONS: List[Tuple[str, str, str]] = [
    ("api_keys", "expires_at", "DATETIME NULL"),
    ("api_keys", "scopes", "VARCHAR(255) NULL"),
    ("request_logs", "request_id", "VARCHAR(36) NULL"),
    ("request_logs", "streamed", "BOOLEAN NOT NULL DEFAULT 0"),
    ("users", "updated_at", "DATETIME NULL"),
    ("conversations", "system_prompt", "TEXT NULL"),
]

INDEX_MIGRATIONS: List[Tuple[str, str, str]] = [
    ("ix_request_logs_endpoint", "request_logs", "endpoint"),
    ("ix_request_logs_model", "request_logs", "model"),
    ("ix_conversations_updated_at", "conversations", "updated_at"),
]


def _existing_columns(engine: Engine, table: str) -> set[str]:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def run_migrations(engine: Engine) -> List[str]:
    """Aplica as migracoes pendentes e devolve a lista do que foi feito."""
    applied: List[str] = []
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    for table, column, ddl in COLUMN_MIGRATIONS:
        if table not in tables or column in _existing_columns(engine, table):
            continue
        try:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            applied.append(f"{table}.{column}")
        except Exception as exc:  # pragma: no cover - depende do dialeto
            logger.warning("Migracao ignorada (%s.%s): %s", table, column, exc)

    for name, table, column in INDEX_MIGRATIONS:
        if table not in tables or column not in _existing_columns(engine, table):
            continue
        try:
            with engine.begin() as conn:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})"))
        except Exception as exc:  # pragma: no cover
            logger.debug("Indice %s nao criado: %s", name, exc)

    if applied:
        logger.info("Migracoes aplicadas: %s", ", ".join(applied))
    return applied


_MIGRATION_CALLBACKS: List[Callable[[Engine], None]] = []
