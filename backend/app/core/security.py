"""Primitivas de seguranca: JWT, API keys e hashing de senha.

O hashing de senha vive em `app.core.passwords` (reexportado aqui para manter
compatibilidade com imports existentes).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.passwords import hash_password, needs_rehash, verify_password

__all__ = [
    "hash_password",
    "verify_password",
    "needs_rehash",
    "create_access_token",
    "create_scoped_token",
    "decode_token",
    "decode_access_token",
    "generate_api_key",
    "hash_api_key",
    "mask_secret",
    "API_KEY_PREFIX",
]

API_KEY_PREFIX = "ark-"
SCOPE_ACCESS = "access"
SCOPE_PASSWORD_RESET = "password_reset"


def _encode(subject: str, scope: str, minutes: int, extra: Optional[dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "scope": scope,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=minutes),
        "jti": uuid.uuid4().hex,
        "iss": "arkium",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, extra: Optional[dict[str, Any]] = None) -> str:
    """JWT de sessao do painel (scope=access)."""
    return _encode(subject, SCOPE_ACCESS, settings.ACCESS_TOKEN_EXPIRE_MINUTES, extra)


def create_scoped_token(subject: str, scope: str, minutes: int) -> str:
    """JWT de uso unico/limitado (ex.: reset de senha)."""
    return _encode(subject, scope, minutes)


def decode_token(token: str, expected_scope: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Decodifica e valida um JWT.

    Retorna None se invalido, expirado ou se o `scope` nao for o esperado.
    Validar o escopo e essencial: sem isso um token de reset de senha
    funcionaria como token de sessao.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
    except JWTError:
        return None
    if expected_scope is not None and payload.get("scope") != expected_scope:
        return None
    return payload


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Atalho para tokens de sessao."""
    return decode_token(token, SCOPE_ACCESS)


def generate_api_key() -> tuple[str, str, str]:
    """Gera uma API key.

    Retorna (chave_em_texto_puro, hash_para_o_banco, prefixo_visivel).
    A chave em texto puro so aparece uma vez, no momento da criacao.
    """
    raw = API_KEY_PREFIX + secrets.token_urlsafe(36)
    return raw, hash_api_key(raw), raw[:12]


def hash_api_key(raw: str) -> str:
    """HMAC-SHA256 da API key.

    Usar HMAC com a SECRET_KEY (em vez de SHA-256 puro) impede ataques de
    dicionario/rainbow caso o banco vaze, e mantem busca por igualdade.
    """
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()


def legacy_hash_api_key(raw: str) -> str:
    """Hash usado na versao 1.x (SHA-256 puro) - aceito para nao invalidar chaves."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mask_secret(value: Optional[str], keep: int = 6) -> str:
    """Mascara um segredo para exibicao/log (nunca logamos o valor completo)."""
    if not value:
        return ""
    return value[:keep] + "..." if len(value) > keep else "..."
