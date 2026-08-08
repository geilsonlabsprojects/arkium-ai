"""Dependencies compartilhadas: autenticacao JWT, API key e rate limit."""

from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_api_key
from app.db.session import get_db
from app.models import ApiKey, User
from app.services import rate_limit, settings_service

bearer_scheme = HTTPBearer(auto_error=False)


def client_ip(request: Request) -> str:
    """IP do cliente, respeitando proxies reversos (X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Usuario autenticado via JWT (painel web)."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de acesso ausente")
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido ou expirado")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inativo ou inexistente")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Exige privilegio de administrador."""
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores")
    return user


def get_api_key_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Tuple[User, Optional[ApiKey]]:
    """Autentica as rotas /v1/* .

    Aceita tanto uma API key (`Authorization: Bearer ark-...`, o formato que os
    SDKs da OpenAI enviam) quanto um JWT do painel. Aplica rate limit e
    atualiza estatisticas de uso da chave.
    """
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            {"error": {"message": "Chave de API ausente", "type": "invalid_request_error", "code": "no_api_key"}},
        )

    token = credentials.credentials
    api_key: Optional[ApiKey] = None

    if token.startswith("ark-"):
        api_key = db.query(ApiKey).filter(ApiKey.key_hash == hash_api_key(token)).first()
        if not api_key or not api_key.is_active:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                {"error": {"message": "Chave de API invalida", "type": "invalid_request_error", "code": "invalid_api_key"}},
            )
        if api_key.is_expired:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                {"error": {"message": "Chave de API expirada", "type": "invalid_request_error", "code": "expired_api_key"}},
            )
        user = db.query(User).filter(User.id == api_key.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario da chave esta inativo")
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.last_used_ip = client_ip(request)
        api_key.request_count += 1
        db.commit()
    else:
        user = get_current_user(credentials, db)

    # Rate limit por chave (ou por usuario, quando autenticado por JWT)
    limits = settings_service.inference_defaults(db)
    identity = f"key:{api_key.id}" if api_key else f"user:{user.id}"
    allowed, remaining, reset = rate_limit.check(
        identity, limits["rate_limit_requests"], limits["rate_limit_window"]
    )
    if not allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            {"error": {"message": f"Limite de requisicoes excedido. Tente novamente em {reset}s.", "type": "rate_limit_error"}},
            headers={"Retry-After": str(reset), "X-RateLimit-Remaining": str(remaining)},
        )

    return user, api_key
