"""Endpoints compativeis com a API da OpenAI (namespace /v1).

Qualquer SDK da OpenAI funciona apontando `base_url` para
`http://localhost:8000/v1` e usando uma API key gerada no painel.
"""

from __future__ import annotations

import json
import time
from typing import AsyncIterator, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_api_key_context
from app.db.session import SessionLocal, get_db
from app.models import ApiKey, User
from app.schemas.openai import (
    ChatCompletionRequest,
    CompletionRequest,
    EmbeddingsRequest,
    ModelList,
)
from app.services import log_service, settings_service
from app.services.ollama_service import OllamaError, ollama_service
from app.services.openai_adapter import (
    chat_chunk,
    chat_completion_response,
    chat_request_to_ollama,
    completion_chunk,
    completion_request_to_ollama,
    completion_response,
    model_cards,
    new_id,
    usage_from_ollama,
)

router = APIRouter(prefix="/v1", tags=["Compatibilidade OpenAI"])

Auth = Tuple[User, ApiKey | None]


def _openai_error(message: str, err_type: str = "api_error", code: str | None = None) -> dict:
    """Envelope de erro no formato da OpenAI."""
    return {"error": {"message": message, "type": err_type, "param": None, "code": code}}


@router.get("/models", response_model=ModelList, summary="Lista os modelos disponiveis")
async def list_models(auth: Auth = Depends(get_api_key_context)) -> ModelList:
    """Detecta automaticamente todos os modelos instalados no Ollama."""
    try:
        models = await ollama_service.list_models()
    except OllamaError as exc:
        raise HTTPException(exc.status_code, _openai_error(str(exc), exc.error_type, exc.code)) from exc
    return ModelList(data=model_cards(models))


@router.get("/models/{model_id:path}", summary="Detalhes de um modelo")
async def retrieve_model(model_id: str, auth: Auth = Depends(get_api_key_context)) -> dict:
    """Retorna o card de um modelo especifico."""
    cards = model_cards(await ollama_service.list_models())
    for card in cards:
        if card["id"] == model_id:
            return card
    raise HTTPException(status.HTTP_404_NOT_FOUND, _openai_error(f"Modelo '{model_id}' nao encontrado", "invalid_request_error"))


@router.post("/chat/completions", summary="Chat completions (compativel com OpenAI)")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    auth: Auth = Depends(get_api_key_context),
    db: Session = Depends(get_db),
):
    """Gera uma resposta de chat. Suporta streaming via Server-Sent Events."""
    user, api_key = auth
    defaults = settings_service.inference_defaults(db)
    model = body.model or defaults["model"]
    payload = chat_request_to_ollama(body, model, defaults)
    ip = client_ip(request)
    started = time.perf_counter()

    if body.stream:
        return StreamingResponse(
            _chat_sse(payload, model, user.id, api_key.id if api_key else None, ip, started),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
        )

    try:
        data = await ollama_service.chat(payload)
    except OllamaError as exc:
        log_service.record(
            db, endpoint="/v1/chat/completions", user_id=user.id,
            api_key_id=api_key.id if api_key else None, model=model, status_code=exc.status_code,
            duration_ms=(time.perf_counter() - started) * 1000, ip_address=ip, error=str(exc),
        )
        raise HTTPException(exc.status_code, _openai_error(str(exc), exc.error_type, exc.code)) from exc

    content = (data.get("message") or {}).get("content", "")
    response = chat_completion_response(model, content, data)
    log_service.record(
        db, endpoint="/v1/chat/completions", user_id=user.id,
        api_key_id=api_key.id if api_key else None, model=model,
        duration_ms=(time.perf_counter() - started) * 1000, usage=response["usage"], ip_address=ip,
    )
    return response


async def _chat_sse(payload, model, user_id, api_key_id, ip, started) -> AsyncIterator[str]:
    """Gerador SSE de `chat.completion.chunk`, encerrando com `data: [DONE]`."""
    chunk_id = new_id("chatcmpl")
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error: str | None = None

    # Primeiro chunk anuncia o papel do autor, como faz a OpenAI
    yield f"data: {json.dumps(chat_chunk(chunk_id, model, {'role': 'assistant', 'content': ''}))}\n\n"
    try:
        async for part in ollama_service.chat_stream(payload):
            delta = (part.get("message") or {}).get("content", "")
            if delta:
                yield f"data: {json.dumps(chat_chunk(chunk_id, model, {'content': delta}))}\n\n"
            if part.get("done"):
                usage = usage_from_ollama(part)
                yield f"data: {json.dumps(chat_chunk(chunk_id, model, {}, 'stop'))}\n\n"
    except OllamaError as exc:
        error = str(exc)
        yield f"data: {json.dumps(_openai_error(error, 'service_unavailable'))}\n\n"

    yield "data: [DONE]\n\n"

    # O log usa uma sessao propria: a do request ja foi encerrada pelo FastAPI
    db = SessionLocal()
    try:
        log_service.record(
            db, endpoint="/v1/chat/completions", user_id=user_id, api_key_id=api_key_id,
            model=model, status_code=503 if error else 200,
            duration_ms=(time.perf_counter() - started) * 1000, usage=usage, ip_address=ip, error=error,
        )
    finally:
        db.close()


@router.post("/completions", summary="Text completions (compativel com OpenAI)")
async def completions(
    body: CompletionRequest,
    request: Request,
    auth: Auth = Depends(get_api_key_context),
    db: Session = Depends(get_db),
):
    """Completions de texto puro, com ou sem streaming."""
    user, api_key = auth
    defaults = settings_service.inference_defaults(db)
    model = body.model or defaults["model"]
    payload = completion_request_to_ollama(body, model, defaults)
    ip = client_ip(request)
    started = time.perf_counter()

    if body.stream:
        return StreamingResponse(
            _completion_sse(payload, model, user.id, api_key.id if api_key else None, ip, started),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        data = await ollama_service.generate(payload)
    except OllamaError as exc:
        raise HTTPException(exc.status_code, _openai_error(str(exc), exc.error_type, exc.code)) from exc

    response = completion_response(model, data.get("response", ""), data)
    log_service.record(
        db, endpoint="/v1/completions", user_id=user.id, api_key_id=api_key.id if api_key else None,
        model=model, duration_ms=(time.perf_counter() - started) * 1000,
        usage=response["usage"], ip_address=ip,
    )
    return response


async def _completion_sse(payload, model, user_id, api_key_id, ip, started) -> AsyncIterator[str]:
    """Gerador SSE de `text_completion`."""
    chunk_id = new_id("cmpl")
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error: str | None = None
    try:
        async for part in ollama_service.generate_stream(payload):
            text = part.get("response", "")
            if text:
                yield f"data: {json.dumps(completion_chunk(chunk_id, model, text))}\n\n"
            if part.get("done"):
                usage = usage_from_ollama(part)
                yield f"data: {json.dumps(completion_chunk(chunk_id, model, '', 'stop'))}\n\n"
    except OllamaError as exc:
        error = str(exc)
        yield f"data: {json.dumps(_openai_error(error, 'service_unavailable'))}\n\n"

    yield "data: [DONE]\n\n"

    db = SessionLocal()
    try:
        log_service.record(
            db, endpoint="/v1/completions", user_id=user_id, api_key_id=api_key_id, model=model,
            status_code=503 if error else 200, duration_ms=(time.perf_counter() - started) * 1000,
            usage=usage, ip_address=ip, error=error,
        )
    finally:
        db.close()


@router.post("/embeddings", summary="Embeddings (compativel com OpenAI)")
async def embeddings(
    body: EmbeddingsRequest,
    request: Request,
    auth: Auth = Depends(get_api_key_context),
    db: Session = Depends(get_db),
) -> dict:
    """Gera embeddings usando um modelo de embedding do Ollama.

    Requer um modelo apropriado instalado (ex.: `ollama pull nomic-embed-text`).
    Se o modelo nao suportar embeddings, retorna 501 com a estrutura pronta.
    """
    user, api_key = auth
    defaults = settings_service.inference_defaults(db)
    model = body.model or "nomic-embed-text"
    inputs = [body.input] if isinstance(body.input, str) else list(body.input)
    started = time.perf_counter()

    try:
        vectors = await ollama_service.embeddings(model, inputs)
    except OllamaError as exc:
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED,
            _openai_error(
                f"Embeddings indisponiveis para o modelo '{model}'. Instale um modelo de embedding "
                f"(ex.: ollama pull nomic-embed-text). Detalhe: {exc}",
                "not_implemented",
            ),
        ) from exc

    log_service.record(
        db, endpoint="/v1/embeddings", user_id=user.id, api_key_id=api_key.id if api_key else None,
        model=model, duration_ms=(time.perf_counter() - started) * 1000, ip_address=client_ip(request),
    )
    return {
        "object": "list",
        "model": model,
        "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)],
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
