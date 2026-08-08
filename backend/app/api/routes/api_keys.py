"""CRUD das API keys do usuario autenticado."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import generate_api_key
from app.db.session import get_db
from app.models import ApiKey, User
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyOut, ApiKeyRename

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


def _owned(db: Session, key_id: int, user: User) -> ApiKey:
    """Busca a chave garantindo que ela pertence ao usuario autenticado."""
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chave nao encontrada")
    return key


@router.get("", response_model=list[ApiKeyOut])
def list_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ApiKeyOut]:
    """Lista as chaves do usuario (sem expor o segredo)."""
    rows = db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(ApiKey.id.desc()).all()
    return [ApiKeyOut.model_validate(r) for r in rows]


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_key(
    payload: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyCreated:
    """Cria uma chave. O valor completo aparece SOMENTE nesta resposta."""
    raw, key_hash, prefix = generate_api_key()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)
        if payload.expires_in_days
        else None
    )
    key = ApiKey(
        user_id=user.id,
        name=payload.name.strip(),
        key_hash=key_hash,
        key_prefix=prefix,
        expires_at=expires_at,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return ApiKeyCreated(**ApiKeyOut.model_validate(key).model_dump(), key=raw)


@router.patch("/{key_id}", response_model=ApiKeyOut)
def rename_key(
    key_id: int,
    payload: ApiKeyRename,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyOut:
    """Renomeia uma chave."""
    key = _owned(db, key_id, user)
    key.name = payload.name.strip()
    db.commit()
    db.refresh(key)
    return ApiKeyOut.model_validate(key)


@router.post("/{key_id}/revoke", response_model=ApiKeyOut)
def revoke_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyOut:
    """Revoga (desativa) uma chave sem apaga-la, preservando o historico."""
    key = _owned(db, key_id, user)
    key.is_active = False
    db.commit()
    db.refresh(key)
    return ApiKeyOut.model_validate(key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Exclui definitivamente uma chave."""
    db.delete(_owned(db, key_id, user))
    db.commit()
