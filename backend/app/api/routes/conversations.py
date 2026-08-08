"""Historico de conversas do playground: listar, ver, apagar e exportar."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Conversation, Message, User
from app.schemas.admin import ConversationDetail, ConversationOut, MessageOut

router = APIRouter(prefix="/api/conversations", tags=["Historico"])


def _owned(db: Session, conversation_id: int, user: User) -> Conversation:
    """Recupera a conversa validando a propriedade."""
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversa nao encontrada")
    return convo


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Conversas do usuario, mais recentes primeiro."""
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [ConversationOut.model_validate(r) for r in rows]


@router.post("", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
def create_conversation(
    title: str = "Nova conversa",
    model: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria uma conversa vazia."""
    convo = Conversation(user_id=user.id, title=title[:200], model=model)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return ConversationDetail(**ConversationOut.model_validate(convo).model_dump(), messages=[])


@router.get("/{conversation_id}", response_model=ConversationDetail)
def read_conversation(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Conversa completa, com todas as mensagens."""
    convo = _owned(db, conversation_id, user)
    return ConversationDetail(
        **ConversationOut.model_validate(convo).model_dump(),
        messages=[MessageOut.model_validate(m) for m in convo.messages],
    )


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def add_message(
    conversation_id: int,
    role: str,
    content: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Anexa uma mensagem a conversa."""
    if role not in {"system", "user", "assistant"}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Papel de mensagem invalido")
    convo = _owned(db, conversation_id, user)
    message = Message(conversation_id=convo.id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageOut.model_validate(message)


@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Exporta a conversa em JSON (download)."""
    convo = _owned(db, conversation_id, user)
    payload = {
        "title": convo.title,
        "model": convo.model,
        "created_at": convo.created_at.isoformat(),
        "messages": [{"role": m.role, "content": m.content} for m in convo.messages],
    }
    return JSONResponse(
        content=json.loads(json.dumps(payload)),
        headers={"Content-Disposition": f'attachment; filename="conversa-{convo.id}.json"'},
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """Apaga a conversa e suas mensagens."""
    db.delete(_owned(db, conversation_id, user))
    db.commit()
