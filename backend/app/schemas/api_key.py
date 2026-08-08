"""Schemas das API keys."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=120)
    # Novo: chaves podem nascer com prazo de validade (0/None = sem expiracao)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=3650)


class ApiKeyRename(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    is_active: bool
    is_expired: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    request_count: int


class ApiKeyCreated(ApiKeyOut):
    """Retornado apenas na criacao: contem a chave em texto puro (uma unica vez)."""

    key: str
