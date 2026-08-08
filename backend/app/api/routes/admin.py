"""Dashboard administrativo: estatisticas, monitoramento, logs e settings."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import __version__
from app.api.deps import get_current_admin, get_current_user
from app.core.config import settings as env_settings
from app.db.session import get_db
from app.models import ApiKey, RequestLog, User
from app.schemas.admin import (
    DashboardStats,
    HealthStatus,
    RequestLogOut,
    SettingUpdate,
    SystemStats,
    UsagePoint,
)
from app.services import monitoring, settings_service
from app.services.ollama_service import ollama_service

router = APIRouter(prefix="/api/admin", tags=["Administracao"])


async def _health(db: Session) -> HealthStatus:
    """Status agregado dos componentes da plataforma."""
    try:
        db.query(User).limit(1).all()
        database = "online"
    except Exception:  # pragma: no cover
        database = "offline"
    return HealthStatus(
        api="online",
        database=database,
        ollama="online" if await ollama_service.is_online() else "offline",
        version=__version__,
        platform_name=settings_service.get_value(db, "platform_name", env_settings.PLATFORM_NAME),
    )


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DashboardStats:
    """Todos os numeros exibidos no painel administrativo."""
    now = datetime.now(timezone.utc)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_month = start_day.replace(day=1)

    total_requests = db.query(func.count(RequestLog.id)).scalar() or 0
    requests_today = db.query(func.count(RequestLog.id)).filter(RequestLog.created_at >= start_day).scalar() or 0
    requests_month = db.query(func.count(RequestLog.id)).filter(RequestLog.created_at >= start_month).scalar() or 0
    avg_duration = db.query(func.avg(RequestLog.duration_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(RequestLog.total_tokens)).scalar() or 0

    # Uso diario dos ultimos 14 dias
    daily: list[UsagePoint] = []
    for offset in range(13, -1, -1):
        day = start_day - timedelta(days=offset)
        nxt = day + timedelta(days=1)
        rows = db.query(
            func.count(RequestLog.id), func.coalesce(func.sum(RequestLog.total_tokens), 0)
        ).filter(RequestLog.created_at >= day, RequestLog.created_at < nxt).one()
        daily.append(UsagePoint(date=day.strftime("%Y-%m-%d"), requests=int(rows[0]), tokens=int(rows[1])))

    top_models = [
        {"model": name or "desconhecido", "requests": int(count)}
        for name, count in db.query(RequestLog.model, func.count(RequestLog.id))
        .group_by(RequestLog.model)
        .order_by(func.count(RequestLog.id).desc())
        .limit(5)
        .all()
    ]

    models = await ollama_service.list_models()
    return DashboardStats(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_api_keys=db.query(func.count(ApiKey.id)).scalar() or 0,
        total_requests=total_requests,
        requests_today=requests_today,
        requests_month=requests_month,
        avg_duration_ms=round(float(avg_duration), 2),
        total_tokens=int(total_tokens),
        models_available=len(models),
        system=SystemStats(**monitoring.system_stats()),
        health=await _health(db),
        daily_usage=daily,
        top_models=top_models,
    )


@router.get("/monitoring")
async def monitoring_snapshot(_: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> dict:
    """Dados em tempo real da pagina de monitoramento."""
    return {
        "system": monitoring.system_stats(),
        "health": (await _health(db)).model_dump(),
        "running_models": await ollama_service.running_models(),
        "ollama_hosts": env_settings.ollama_hosts_list,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/logs", response_model=list[RequestLogOut])
def list_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    only_errors: bool = False,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[RequestLogOut]:
    """Logs de requisicao paginados, do mais recente para o mais antigo."""
    query = db.query(RequestLog)
    if only_errors:
        query = query.filter(RequestLog.error.isnot(None))
    rows = query.order_by(RequestLog.id.desc()).offset(offset).limit(limit).all()
    return [RequestLogOut.model_validate(r) for r in rows]


@router.delete("/logs")
def clear_logs(
    older_than_days: int = Query(default=0, ge=0),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Limpa os logs (todos, ou apenas os mais antigos que N dias)."""
    query = db.query(RequestLog)
    if older_than_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        query = query.filter(RequestLog.created_at < cutoff)
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}


@router.get("/settings")
def read_settings(_: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> dict:
    """Todas as configuracoes editaveis."""
    return settings_service.get_all(db)


@router.put("/settings")
def write_settings(
    payload: SettingUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Atualiza configuracoes em lote."""
    return settings_service.update_many(db, payload.values)


@router.get("/my-usage")
def my_usage(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Resumo de uso do usuario autenticado (painel do usuario)."""
    base = db.query(RequestLog).filter(RequestLog.user_id == user.id)
    start_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "total_requests": base.count(),
        "requests_today": base.filter(RequestLog.created_at >= start_day).count(),
        "total_tokens": int(
            db.query(func.coalesce(func.sum(RequestLog.total_tokens), 0))
            .filter(RequestLog.user_id == user.id)
            .scalar()
            or 0
        ),
        "active_keys": db.query(func.count(ApiKey.id))
        .filter(ApiKey.user_id == user.id, ApiKey.is_active.is_(True))
        .scalar()
        or 0,
    }
