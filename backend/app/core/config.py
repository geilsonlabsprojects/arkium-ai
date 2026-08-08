"""Configuracao central da aplicacao.

Todas as opcoes vem de variaveis de ambiente / arquivo `.env` (pydantic-settings).
Nada de valores sensiveis embutidos no codigo: o projeto roda igual em Windows,
Linux, macOS ou em um servidor, apenas trocando o `.env`.
"""

from __future__ import annotations

import secrets as _secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/ -> raiz do projeto
BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent

INSECURE_SECRETS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "troque-esta-chave-por-uma-string-aleatoria-longa",
}


class Settings(BaseSettings):
    """Modelo tipado com todas as variaveis de ambiente suportadas."""

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------- identidade
    PLATFORM_NAME: str = "Arkium AI"
    PLATFORM_DESCRIPTION: str = "Plataforma local de IA compativel com a OpenAI"
    PLATFORM_LOGO_URL: str = "/logo.svg"

    # ---------------------------------------------------------------- servidor
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_PORT: int = 5173
    DEBUG: bool = False
    WORKERS: int = 1
    # Confiar em X-Forwarded-For (habilite APENAS atras de um proxy reverso seu)
    TRUST_PROXY: bool = False

    # ------------------------------------------------------------------ banco
    DATABASE_URL: str = "sqlite:///./data/arkium.db"
    DB_ECHO: bool = False

    # ------------------------------------------------------------- seguranca
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    MIN_PASSWORD_LENGTH: int = 8
    # Registro publico de novas contas (o primeiro usuario sempre pode ser criado)
    ALLOW_REGISTRATION: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ------------------------------------------------------------------ admin
    ADMIN_EMAIL: str = "admin@arkium.ai"
    ADMIN_PASSWORD: str = ""
    ADMIN_NAME: str = "Administrador"

    # ----------------------------------------------------------------- ollama
    OLLAMA_HOSTS: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_CONNECT_TIMEOUT: float = 5.0
    OLLAMA_HEALTH_TTL: float = 10.0
    OLLAMA_MAX_RETRIES: int = 2
    OLLAMA_ALLOW_MANAGEMENT: bool = True  # permite pull/delete de modelos pelo painel

    # ------------------------------------------------------------- inferencia
    DEFAULT_MODEL: str = "llama3.2"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2048

    # ------------------------------------------------------------ rate limit
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # -------------------------------------------------------------------- logs
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_JSON: bool = False
    LOG_MAX_BYTES: int = 5 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5
    LOG_REQUEST_BODY: bool = False  # nunca logue corpo em producao

    # ------------------------------------------------------------- validadores
    @field_validator("LOG_LEVEL")
    @classmethod
    def _valid_level(cls, value: str) -> str:
        level = value.upper().strip()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            return "INFO"
        return level

    @field_validator("PORT", "FRONTEND_PORT")
    @classmethod
    def _valid_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("Porta deve estar entre 1 e 65535")
        return value

    # ---------------------------------------------------------------- helpers
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS_ORIGINS em lista. `*` libera todas as origens (nao recomendado)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_allow_all(self) -> bool:
        return "*" in self.cors_origins_list

    @property
    def ollama_hosts_list(self) -> List[str]:
        """Lista de servidores Ollama (o primeiro e o primario)."""
        hosts = [h.strip().rstrip("/") for h in self.OLLAMA_HOSTS.split(",") if h.strip()]
        return hosts or ["http://localhost:11434"]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    def secret_key_is_insecure(self) -> bool:
        return self.SECRET_KEY.strip().lower() in INSECURE_SECRETS or len(self.SECRET_KEY) < 32

    def warnings(self) -> List[str]:
        """Alertas de configuracao mostrados no boot (nunca expoem segredos)."""
        issues: List[str] = []
        if self.secret_key_is_insecure():
            issues.append(
                "SECRET_KEY ausente ou fraca: uma chave temporaria foi gerada em memoria. "
                "Defina SECRET_KEY no .env (python scripts/gen_secret.py) - sem isso todas as "
                "sessoes caem a cada reinicio."
            )
        if self.cors_allow_all:
            issues.append("CORS_ORIGINS=* aceita qualquer origem. Restrinja em producao.")
        if self.DEBUG:
            issues.append("DEBUG=true: nao use em producao.")
        if self.HOST == "0.0.0.0" and self.cors_allow_all:  # noqa: S104
            issues.append("API exposta em 0.0.0.0 com CORS aberto: revise a exposicao de rede.")
        return issues


@lru_cache
def get_settings() -> Settings:
    """Instancia unica (cacheada) das configuracoes."""
    cfg = Settings()
    if cfg.secret_key_is_insecure():
        # Nunca falha o boot, mas nao usa uma chave previsivel.
        cfg.SECRET_KEY = _secrets.token_urlsafe(48)
    return cfg


settings = get_settings()
