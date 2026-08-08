"""Cliente HTTP do Ollama - o ponto mais critico de compatibilidade do Arkium.

Objetivos desta implementacao:

* Nunca assumir que o Ollama esta no ar. Cada falha vira um erro tipado com
  mensagem util (offline, timeout, modelo inexistente, modelo carregando...).
* Reaproveitar conexoes (um `AsyncClient` por host, com pool) em vez de abrir
  um cliente por chamada - reduz latencia e evita sockets pendurados.
* Tolerar diferentes versoes do Ollama: `/api/embed` (novo) com fallback para
  `/api/embeddings` (antigo), `/api/ps` opcional, `/api/version` opcional.
* Ser agnostico ao modelo: nao ha nenhuma logica especifica de familia.
* Failover entre varios hosts (`OLLAMA_HOSTS` aceita lista separada por virgula).
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import logger

# Endpoints que podem nao existir em versoes antigas do Ollama
EMBED_ENDPOINTS = ("/api/embed", "/api/embeddings")


class OllamaError(RuntimeError):
    """Erro generico de comunicacao com o Ollama."""

    status_code = 503
    error_type = "service_unavailable"
    code = "ollama_error"


class OllamaUnavailable(OllamaError):
    """Nao foi possivel conectar em nenhum host do Ollama."""

    status_code = 503
    error_type = "service_unavailable"
    code = "ollama_unavailable"


class OllamaTimeout(OllamaError):
    """O Ollama demorou mais que o timeout configurado."""

    status_code = 504
    error_type = "timeout_error"
    code = "timeout"


class ModelNotFound(OllamaError):
    """O modelo pedido nao esta instalado no Ollama."""

    status_code = 404
    error_type = "invalid_request_error"
    code = "model_not_found"


class ModelBusy(OllamaError):
    """O modelo esta sendo carregado/baixado e ainda nao pode responder."""

    status_code = 503
    error_type = "service_unavailable"
    code = "model_loading"


class OllamaBadRequest(OllamaError):
    """O Ollama recusou os parametros enviados."""

    status_code = 400
    error_type = "invalid_request_error"
    code = "invalid_parameters"


@dataclass
class HostState:
    """Saude observada de um host (evita martelar um servidor fora do ar)."""

    online: bool = False
    checked_at: float = 0.0
    version: Optional[str] = None
    last_error: Optional[str] = None


def _classify(host: str, exc: Exception) -> OllamaError:
    """Traduz excecoes httpx em erros de dominio com mensagem util."""
    if isinstance(exc, httpx.TimeoutException):
        return OllamaTimeout(
            f"O Ollama ({host}) nao respondeu dentro de {settings.OLLAMA_TIMEOUT}s. "
            "Modelos grandes no primeiro carregamento podem exceder o timeout: "
            "aumente OLLAMA_TIMEOUT ou use um modelo menor."
        )
    if isinstance(exc, httpx.ConnectError):
        return OllamaUnavailable(
            f"Nao foi possivel conectar ao Ollama em {host}. Verifique se o servico esta rodando "
            "(`ollama serve`) e se OLLAMA_HOSTS aponta para o endereco correto."
        )
    if isinstance(exc, httpx.RemoteProtocolError):
        return OllamaError(f"A conexao com o Ollama ({host}) foi interrompida antes do fim da resposta.")
    return OllamaUnavailable(f"Falha de comunicacao com o Ollama ({host}): {exc}")


def _classify_status(host: str, status_code: int, body: str) -> OllamaError:
    """Traduz respostas HTTP de erro do Ollama."""
    text = (body or "").strip()
    lowered = text.lower()
    if status_code == 404 or "not found" in lowered or "try pulling it first" in lowered:
        return ModelNotFound(text or "Modelo nao encontrado no Ollama.")
    if status_code == 400:
        return OllamaBadRequest(text or "Parametros invalidos para o modelo.")
    if status_code in (429, 503) or "loading" in lowered or "busy" in lowered:
        return ModelBusy(text or "O modelo esta ocupado ou sendo carregado. Tente novamente em instantes.")
    return OllamaError(f"Ollama ({host}) respondeu {status_code}: {text[:300]}")


class OllamaService:
    """Servico de acesso ao Ollama com pool de conexoes, retry e failover."""

    def __init__(self, hosts: Optional[List[str]] = None, timeout: Optional[int] = None) -> None:
        self.hosts = hosts or settings.ollama_hosts_list
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._state: Dict[str, HostState] = {h: HostState() for h in self.hosts}
        self._lock = asyncio.Lock()
        self._cursor = 0

    # ------------------------------------------------------------------ infra
    def _timeout(self, read: Optional[float] = None) -> httpx.Timeout:
        return httpx.Timeout(
            connect=settings.OLLAMA_CONNECT_TIMEOUT,
            read=read if read is not None else self.timeout,
            write=30.0,
            pool=settings.OLLAMA_CONNECT_TIMEOUT,
        )

    async def client(self, host: str) -> httpx.AsyncClient:
        """Cliente reaproveitado por host (keep-alive)."""
        client = self._clients.get(host)
        if client is None or client.is_closed:
            async with self._lock:
                client = self._clients.get(host)
                if client is None or client.is_closed:
                    client = httpx.AsyncClient(
                        base_url=host,
                        timeout=self._timeout(),
                        limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
                        headers={"User-Agent": "Arkium/2.0"},
                    )
                    self._clients[host] = client
        return client

    async def aclose(self) -> None:
        """Fecha todos os clientes (chamado no shutdown da aplicacao)."""
        for client in list(self._clients.values()):
            try:
                await client.aclose()
            except Exception:  # pragma: no cover
                pass
        self._clients.clear()

    def _ordered_hosts(self) -> List[str]:
        """Hosts em round-robin, priorizando os conhecidos como online."""
        if not self.hosts:
            raise OllamaUnavailable("Nenhum host Ollama configurado (defina OLLAMA_HOSTS no .env).")
        rotated = self.hosts[self._cursor % len(self.hosts) :] + self.hosts[: self._cursor % len(self.hosts)]
        self._cursor = (self._cursor + 1) % max(len(self.hosts), 1)
        healthy = [h for h in rotated if self._state.get(h, HostState()).online]
        unknown = [h for h in rotated if h not in healthy]
        return healthy + unknown

    def _mark(self, host: str, online: bool, error: Optional[str] = None) -> None:
        state = self._state.setdefault(host, HostState())
        state.online = online
        state.checked_at = time.monotonic()
        state.last_error = error

    # ---------------------------------------------------------------- request
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict] = None,
        read_timeout: Optional[float] = None,
        retries: Optional[int] = None,
        hosts: Optional[List[str]] = None,
    ) -> httpx.Response:
        """Executa uma chamada tentando cada host, com retry e backoff."""
        attempts = settings.OLLAMA_MAX_RETRIES if retries is None else retries
        last_error: OllamaError = OllamaUnavailable("Nenhum host Ollama disponivel.")

        for host in hosts or self._ordered_hosts():
            client = await self.client(host)
            for attempt in range(attempts + 1):
                try:
                    response = await client.request(
                        method, path, json=json_body, timeout=self._timeout(read_timeout)
                    )
                    if response.status_code >= 400:
                        error = _classify_status(host, response.status_code, response.text)
                        # Erros do cliente nao devem ser repetidos em outro host
                        if isinstance(error, (ModelNotFound, OllamaBadRequest)):
                            self._mark(host, True)
                            raise error
                        last_error = error
                        self._mark(host, True, str(error))
                        break
                    self._mark(host, True)
                    return response
                except (ModelNotFound, OllamaBadRequest):
                    raise
                except httpx.HTTPError as exc:
                    last_error = _classify(host, exc)
                    self._mark(host, False, str(last_error))
                    if isinstance(last_error, OllamaTimeout) or attempt >= attempts:
                        break
                    await asyncio.sleep(0.4 * (2**attempt))
        raise last_error

    # ----------------------------------------------------------------- health
    async def ping(self, host: str) -> HostState:
        """Checa um host respeitando o TTL de cache (evita flood de checagens)."""
        state = self._state.setdefault(host, HostState())
        if state.checked_at and (time.monotonic() - state.checked_at) < settings.OLLAMA_HEALTH_TTL:
            return state
        client = await self.client(host)
        try:
            response = await client.get("/api/version", timeout=httpx.Timeout(settings.OLLAMA_CONNECT_TIMEOUT))
            if response.status_code == 404:  # versoes antigas nao tem /api/version
                response = await client.get("/api/tags", timeout=httpx.Timeout(settings.OLLAMA_CONNECT_TIMEOUT))
                state.version = "desconhecida"
            elif response.status_code == 200:
                try:
                    state.version = response.json().get("version")
                except ValueError:
                    state.version = "desconhecida"
            self._mark(host, response.status_code == 200, None if response.status_code == 200 else "http error")
        except httpx.HTTPError as exc:
            self._mark(host, False, str(_classify(host, exc)))
        return self._state[host]

    async def is_online(self) -> bool:
        """True se ao menos um host responder."""
        results = await asyncio.gather(*(self.ping(h) for h in self.hosts), return_exceptions=True)
        return any(isinstance(r, HostState) and r.online for r in results)

    async def status(self) -> Dict[str, Any]:
        """Diagnostico completo por host (usado no monitoramento)."""
        await asyncio.gather(*(self.ping(h) for h in self.hosts), return_exceptions=True)
        hosts = [
            {
                "url": host,
                "online": state.online,
                "version": state.version,
                "last_error": state.last_error,
            }
            for host, state in ((h, self._state.get(h, HostState())) for h in self.hosts)
        ]
        return {"online": any(h["online"] for h in hosts), "hosts": hosts}

    async def version(self) -> Optional[str]:
        for host in self.hosts:
            state = await self.ping(host)
            if state.online:
                return state.version
        return None

    # ----------------------------------------------------------------- models
    async def list_models(self) -> List[Dict[str, Any]]:
        """Modelos instalados, deduplicados entre hosts. Nunca levanta excecao."""
        seen: Dict[str, Dict[str, Any]] = {}
        for host in self.hosts:
            try:
                response = await self._request("GET", "/api/tags", read_timeout=15, retries=0, hosts=[host])
                for model in response.json().get("models", []):
                    name = model.get("name") or model.get("model")
                    if name:
                        seen.setdefault(name, {**model, "name": name, "host": host})
            except OllamaError as exc:
                logger.warning("Falha ao listar modelos em %s: %s", host, exc)
        return list(seen.values())

    async def model_names(self) -> List[str]:
        return [m["name"] for m in await self.list_models()]

    async def has_model(self, model: str) -> bool:
        """Aceita `llama3.2` como equivalente a `llama3.2:latest`."""
        names = await self.model_names()
        if model in names:
            return True
        base = model.split(":")[0]
        return any(n == f"{base}:latest" or n.split(":")[0] == base for n in names)

    async def show(self, model: str) -> Dict[str, Any]:
        """Detalhes/capacidades de um modelo (`/api/show`)."""
        response = await self._request("POST", "/api/show", json_body={"model": model}, read_timeout=30)
        return response.json()

    async def running_models(self) -> List[Dict[str, Any]]:
        """Modelos carregados em memoria (`/api/ps`; opcional em versoes antigas)."""
        running: List[Dict[str, Any]] = []
        for host in self.hosts:
            try:
                response = await self._request("GET", "/api/ps", read_timeout=10, retries=0, hosts=[host])
                for model in response.json().get("models", []):
                    running.append({**model, "host": host})
            except OllamaError as exc:
                logger.debug("/api/ps indisponivel em %s: %s", host, exc)
        return running

    async def pull_stream(self, model: str) -> AsyncIterator[Dict[str, Any]]:
        """Baixa um modelo transmitindo o progresso (NDJSON)."""
        host = self._ordered_hosts()[0]
        client = await self.client(host)
        try:
            async with client.stream(
                "POST", "/api/pull", json={"model": model, "stream": True}, timeout=self._timeout(None)
            ) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", "replace")
                    raise _classify_status(host, response.status_code, body)
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as exc:
            raise _classify(host, exc) from exc

    async def delete_model(self, model: str) -> None:
        """Remove um modelo do Ollama."""
        await self._request("DELETE", "/api/delete", json_body={"model": model}, read_timeout=60)

    # ------------------------------------------------------------------- chat
    async def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Chamada nao-streaming de `/api/chat`."""
        response = await self._request("POST", "/api/chat", json_body={**payload, "stream": False})
        return self._json(response)

    async def chat_stream(self, payload: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Streaming de `/api/chat`: um dict por chunk NDJSON."""
        async for chunk in self._stream("/api/chat", payload):
            yield chunk

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Chamada nao-streaming de `/api/generate`."""
        response = await self._request("POST", "/api/generate", json_body={**payload, "stream": False})
        return self._json(response)

    async def generate_stream(self, payload: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Streaming de `/api/generate`."""
        async for chunk in self._stream("/api/generate", payload):
            yield chunk

    async def _stream(self, path: str, payload: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Streaming NDJSON generico, com erro tipado e fechamento garantido."""
        last_error: OllamaError = OllamaUnavailable("Nenhum host Ollama disponivel.")
        for host in self._ordered_hosts():
            client = await self.client(host)
            try:
                async with client.stream(
                    "POST", path, json={**payload, "stream": True}, timeout=self._timeout(None)
                ) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode("utf-8", "replace")
                        error = _classify_status(host, response.status_code, body)
                        if isinstance(error, (ModelNotFound, OllamaBadRequest)):
                            raise error
                        last_error = error
                        continue
                    self._mark(host, True)
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            logger.debug("Chunk NDJSON invalido ignorado (%s)", host)
                            continue
                        if chunk.get("error"):
                            raise _classify_status(host, 500, str(chunk["error"]))
                        yield chunk
                    return
            except (ModelNotFound, OllamaBadRequest):
                raise
            except httpx.HTTPError as exc:
                last_error = _classify(host, exc)
                self._mark(host, False, str(last_error))
                continue
        raise last_error

    # -------------------------------------------------------------- embeddings
    async def embeddings(self, model: str, inputs: List[str]) -> List[List[float]]:
        """Embeddings com suporte a Ollama novo (`/api/embed`) e antigo."""
        try:
            response = await self._request(
                "POST", EMBED_ENDPOINTS[0], json_body={"model": model, "input": inputs}, read_timeout=120
            )
            vectors = response.json().get("embeddings") or []
            if vectors:
                return vectors
        except OllamaError as exc:
            # 404 aqui pode significar "endpoint inexistente" (Ollama antigo);
            # se o modelo realmente nao existir, o fallback abaixo tambem falha.
            logger.debug("/api/embed indisponivel, tentando /api/embeddings: %s", exc)

        # Fallback: endpoint legado aceita um unico prompt por chamada
        vectors = []
        for text in inputs:
            response = await self._request(
                "POST", EMBED_ENDPOINTS[1], json_body={"model": model, "prompt": text}, read_timeout=120
            )
            vectors.append(response.json().get("embedding", []))
        return vectors

    @staticmethod
    def _json(response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise OllamaError("O Ollama devolveu uma resposta incompleta ou invalida.") from exc


# Instancia compartilhada pela aplicacao
ollama_service = OllamaService()
