"""Testes do cliente Ollama usando um transporte HTTP simulado."""

import json

import httpx
import pytest

from app.services.ollama_service import (
    ModelNotFound,
    OllamaService,
    OllamaTimeout,
    OllamaUnavailable,
)


def service_with(handler) -> OllamaService:
    """Servico apontando para um transporte falso (sem rede)."""
    service = OllamaService(hosts=["http://fake:11434"], timeout=5)
    service._clients["http://fake:11434"] = httpx.AsyncClient(
        base_url="http://fake:11434", transport=httpx.MockTransport(handler)
    )
    return service


@pytest.mark.asyncio
async def test_lista_modelos():
    def handler(request):
        return httpx.Response(200, json={"models": [{"name": "llama3.2:latest"}]})

    service = service_with(handler)
    assert await service.model_names() == ["llama3.2:latest"]
    assert await service.has_model("llama3.2")  # tolera ausencia da tag :latest
    assert not await service.has_model("inexistente")
    await service.aclose()


@pytest.mark.asyncio
async def test_lista_modelos_nao_quebra_com_ollama_offline():
    def handler(request):
        raise httpx.ConnectError("recusada", request=request)

    service = service_with(handler)
    assert await service.list_models() == []  # degrada com elegancia
    assert await service.is_online() is False
    await service.aclose()


@pytest.mark.asyncio
async def test_modelo_inexistente_vira_erro_tipado():
    def handler(request):
        return httpx.Response(404, text='model "x" not found, try pulling it first')

    service = service_with(handler)
    with pytest.raises(ModelNotFound):
        await service.chat({"model": "x", "messages": []})
    await service.aclose()


@pytest.mark.asyncio
async def test_timeout_vira_erro_de_timeout():
    def handler(request):
        raise httpx.ReadTimeout("demorou", request=request)

    service = service_with(handler)
    with pytest.raises(OllamaTimeout):
        await service.chat({"model": "x", "messages": []})
    await service.aclose()


@pytest.mark.asyncio
async def test_conexao_recusada_vira_indisponivel():
    def handler(request):
        raise httpx.ConnectError("recusada", request=request)

    service = service_with(handler)
    with pytest.raises(OllamaUnavailable):
        await service.chat({"model": "x", "messages": []})
    await service.aclose()


@pytest.mark.asyncio
async def test_streaming_ignora_linhas_invalidas():
    def handler(request):
        body = "\n".join(
            [
                json.dumps({"message": {"content": "Ola"}, "done": False}),
                "lixo-nao-json",
                json.dumps({"message": {"content": " mundo"}, "done": True}),
            ]
        )
        return httpx.Response(200, text=body)

    service = service_with(handler)
    chunks = [c async for c in service.chat_stream({"model": "m", "messages": []})]
    assert "".join(c["message"]["content"] for c in chunks) == "Ola mundo"
    await service.aclose()


@pytest.mark.asyncio
async def test_embeddings_usa_fallback_do_endpoint_legado():
    chamadas: list[str] = []

    def handler(request):
        chamadas.append(request.url.path)
        if request.url.path == "/api/embed":
            return httpx.Response(404, text="not found")
        return httpx.Response(200, json={"embedding": [0.1, 0.2]})

    service = service_with(handler)
    vectors = await service.embeddings("nomic-embed-text", ["texto"])
    assert vectors == [[0.1, 0.2]]
    assert "/api/embeddings" in chamadas  # caiu para a API antiga
    await service.aclose()
