"""Schemas compativeis com a API da OpenAI.

Os nomes de campo replicam exatamente o contrato publico da OpenAI para que
SDKs existentes (openai-python, openai-node, LangChain, etc.) funcionem sem
alteracao apontando a `base_url` para esta plataforma.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage] = Field(min_length=1)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=131072)
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    seed: Optional[int] = None
    user: Optional[str] = None


class CompletionRequest(BaseModel):
    model: Optional[str] = None
    prompt: Union[str, List[str]]
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=131072)
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    suffix: Optional[str] = None
    user: Optional[str] = None


class EmbeddingsRequest(BaseModel):
    model: Optional[str] = None
    input: Union[str, List[str]]
    encoding_format: Literal["float", "base64"] = "float"
    user: Optional[str] = None


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "ollama"
    # Metadados extras expostos pelo Ollama (nao quebram clientes OpenAI)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard]
