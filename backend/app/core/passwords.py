"""Hash de senhas sem passlib.

Motivo tecnico: `passlib` 1.7.4 quebra com `bcrypt>=4.1` (AttributeError em
`bcrypt.__about__`), um dos erros de instalacao mais comuns deste projeto.
Aqui falamos com a biblioteca `bcrypt` diretamente e, se ela nao estiver
disponivel, caimos para PBKDF2-HMAC-SHA256 da stdlib. Hashes bcrypt antigos
continuam validos (compatibilidade retroativa com bancos ja existentes).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

try:  # pragma: no cover - depende do ambiente
    import bcrypt as _bcrypt
except Exception:  # pragma: no cover
    _bcrypt = None  # type: ignore[assignment]

_PBKDF2_ROUNDS = 260_000
_PBKDF2_PREFIX = "pbkdf2_sha256"
# bcrypt trunca em 72 bytes; pre-hash evita truncamento silencioso de senhas longas
_BCRYPT_MAX_BYTES = 72


def _prepare(password: str) -> bytes:
    raw = password.encode("utf-8")
    if len(raw) > _BCRYPT_MAX_BYTES:
        raw = base64.b64encode(hashlib.sha256(raw).digest())
    return raw


def hash_password(password: str) -> str:
    """Gera o hash da senha (bcrypt quando disponivel, senao PBKDF2)."""
    if _bcrypt is not None:
        return _bcrypt.hashpw(_prepare(password), _bcrypt.gensalt(rounds=12)).decode("utf-8")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS)
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ROUNDS}${salt}${digest.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Compara a senha com o hash armazenado (aceita bcrypt e PBKDF2)."""
    if not hashed:
        return False
    try:
        if hashed.startswith(_PBKDF2_PREFIX):
            _, rounds, salt, digest = hashed.split("$", 3)
            calc = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), int(rounds))
            return hmac.compare_digest(calc.hex(), digest)
        if _bcrypt is None:  # pragma: no cover - ambiente sem bcrypt lendo hash bcrypt
            return False
        return _bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    """True quando o hash usa um esquema mais fraco que o atual."""
    return _bcrypt is not None and hashed.startswith(_PBKDF2_PREFIX)
