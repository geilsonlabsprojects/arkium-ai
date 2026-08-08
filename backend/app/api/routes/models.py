"""Rotas do painel para gestao de modelos do Ollama."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models import User
from app.services import settings_service
from app.services.ollama_service import ollama_service

router = APIRouter(prefix="/api/models", tags=["Modelos"])


@router.get("")
async def list_models(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Modelos instalados, modelos carregados em memoria e o modelo padrao."""
    models = await ollama_service.list_models()
    return {
        "default_model": settings_service.inference_defaults(db)["model"],
        "models": models,
        "running": await ollama_service.running_models(),
        "online": await ollama_service.is_online(),
    }


@router.post("/default")
def set_default_model(
    model: str,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Define o modelo padrao usado quando a requisicao nao informa um."""
    settings_service.update_many(db, {"default_model": model})
    return {"default_model": model}
