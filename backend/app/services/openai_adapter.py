"""Traducao entre o contrato da OpenAI e o contrato do Ollama.

Mantida isolada para que trocar o motor de inferencia no futuro exija apenas
uma nova implementacao deste adaptador.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.schemas.openai import ChatCompletionRequest, CompletionRequest


def new_id(prefix: str) -> str:
    """Identificador no formato usado pela OpenAI (ex.: chatcmpl-xxxx)."""
    return f"{prefix}-{uuid.uuid4().hex[:24]}"


def build_options(
    temperature: Optional[float],
    top_p: Optional[float],
    max_tokens: Optional[int],
    stop: Any,
    seed: Optional[int] = None,
    defaults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Converte parametros OpenAI para o bloco `options` do Ollama."""
    defaults = defaults or {}
    options: Dict[str, Any] = {}
    temp = temperature if temperature is not None else defaults.get("temperature")
    if temp is not None:
        options["temperature"] = float(temp)
    if top_p is not None:
        options["top_p"] = top_p
    tokens = max_tokens if max_tokens is not None else defaults.get("max_tokens")
    if tokens is not None:
        options["num_predict"] = int(tokens)
    if stop:
        options["stop"] = [stop] if isinstance(stop, str) else list(stop)
    if seed is not None:
        options["seed"] = seed
    return options


def chat_request_to_ollama(req: ChatCompletionRequest, model: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Monta o payload de /api/chat a partir de um ChatCompletionRequest."""
    return {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "options": build_options(req.temperature, req.top_p, req.max_tokens, req.stop, req.seed, defaults),
    }


def completion_request_to_ollama(req: CompletionRequest, model: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Monta o payload de /api/generate a partir de um CompletionRequest."""
    prompt = req.prompt if isinstance(req.prompt, str) else "\n".join(req.prompt)
    return {
        "model": model,
        "prompt": prompt,
        "options": build_options(req.temperature, req.top_p, req.max_tokens, req.stop, None, defaults),
    }


def usage_from_ollama(data: Dict[str, Any]) -> Dict[str, int]:
    """Extrai contagem de tokens no formato `usage` da OpenAI."""
    prompt = int(data.get("prompt_eval_count") or 0)
    completion = int(data.get("eval_count") or 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


def finish_reason(data: Dict[str, Any]) -> str:
    """Mapeia o motivo de parada do Ollama para o vocabulario da OpenAI."""
    reason = data.get("done_reason")
    if reason == "length":
        return "length"
    return "stop"


def chat_completion_response(model: str, content: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Resposta final de /v1/chat/completions."""
    return {
        "id": new_id("chatcmpl"),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "logprobs": None,
                "finish_reason": finish_reason(data),
            }
        ],
        "usage": usage_from_ollama(data),
    }


def chat_chunk(chunk_id: str, model: str, delta: Dict[str, Any], finish: Optional[str] = None) -> Dict[str, Any]:
    """Um chunk de `chat.completion.chunk` para o streaming SSE."""
    return {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "logprobs": None, "finish_reason": finish}],
    }


def completion_response(model: str, text: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Resposta final de /v1/completions."""
    return {
        "id": new_id("cmpl"),
        "object": "text_completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "text": text, "logprobs": None, "finish_reason": finish_reason(data)}],
        "usage": usage_from_ollama(data),
    }


def completion_chunk(chunk_id: str, model: str, text: str, finish: Optional[str] = None) -> Dict[str, Any]:
    """Um chunk de `text_completion` para o streaming SSE."""
    return {
        "id": chunk_id,
        "object": "text_completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "text": text, "logprobs": None, "finish_reason": finish}],
    }


def model_cards(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converte a lista do Ollama para o formato `GET /v1/models` da OpenAI."""
    cards: List[Dict[str, Any]] = []
    for model in models:
        cards.append(
            {
                "id": model.get("name"),
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ollama",
                "meta": {
                    "size": model.get("size"),
                    "family": (model.get("details") or {}).get("family"),
                    "parameter_size": (model.get("details") or {}).get("parameter_size"),
                    "quantization": (model.get("details") or {}).get("quantization_level"),
                    "modified_at": model.get("modified_at"),
                    "host": model.get("host"),
                },
            }
        )
    return cards
