"""Schemas de dashboard, monitoramento, logs e configuracoes."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SettingUpdate(BaseModel):
    """Atualizacao parcial em lote das configuracoes chave/valor."""

    values: Dict[str, str] = Field(default_factory=dict)


class RequestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    endpoint: str
    model: Optional[str]
    status_code: int
    duration_ms: float
    total_tokens: int
    ip_address: Optional[str]
    error: Optional[str]
    created_at: datetime


class UsagePoint(BaseModel):
    date: str
    requests: int
    tokens: int


class SystemStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float


class HealthStatus(BaseModel):
    api: str
    database: str
    ollama: str
    version: str
    platform_name: str


class DashboardStats(BaseModel):
    total_users: int
    total_api_keys: int
    total_requests: int
    requests_today: int
    requests_month: int
    avg_duration_ms: float
    total_tokens: int
    models_available: int
    system: SystemStats
    health: HealthStatus
    daily_usage: List[UsagePoint]
    top_models: List[Dict[str, Any]]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    model: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = Field(default_factory=list)
