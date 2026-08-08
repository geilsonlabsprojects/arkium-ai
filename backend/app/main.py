"""Ponto de entrada da aplicacao FastAPI (Arkium AI)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.middlewares.request_logger import RequestLoggerMiddleware
from app.api.middlewares.security_headers import SecurityHeadersMiddleware
from app.api.routes import admin, api_keys, auth, conversations, health, models, openai_v1, users
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.init_db import init_db
from app.services.ollama_service import ollama_service

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Garante banco criado e admin existente antes de aceitar requisicoes."""
    logger.info("Iniciando %s v%s", settings.PLATFORM_NAME, __version__)
    init_db()
    logger.info("Ollama configurado em: %s", ", ".join(settings.ollama_hosts_list))
    yield
    await ollama_service.aclose()
    logger.info("Encerrando %s", settings.PLATFORM_NAME)


DESCRIPTION = """
API local de IA **100% compativel com a OpenAI**, servida pelo Ollama.

Aponte qualquer SDK da OpenAI para `http://localhost:8000/v1` usando uma
API key gerada no painel:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="ark-...")
resp = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Ola!"}],
)
```
"""

app = FastAPI(
    title=settings.PLATFORM_NAME,
    description=DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ------------------------------------------------------------------ middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time-ms", "X-RateLimit-Remaining", "Retry-After"],
)


# --------------------------------------------------------------- error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Erros HTTP em envelope OpenAI quando a rota pertence a /v1."""
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail, headers=getattr(exc, "headers", None))
    if request.url.path.startswith("/v1"):
        content = {"error": {"message": str(detail), "type": "invalid_request_error", "code": exc.status_code}}
    else:
        content = {"detail": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=content, headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Erros de validacao Pydantic com mensagem legivel."""
    return JSONResponse(
        status_code=422,
        content={"error": {"message": "Dados invalidos", "type": "invalid_request_error", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # pragma: no cover
    """Nunca vaza stack trace para o cliente."""
    logger.exception("Erro nao tratado em %s", request.url.path)
    return JSONResponse(status_code=500, content={"error": {"message": "Erro interno do servidor", "type": "api_error"}})


# --------------------------------------------------------------------- routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(api_keys.router)
app.include_router(models.router)
app.include_router(conversations.router)
app.include_router(admin.router)
app.include_router(openai_v1.router)


@app.get("/", tags=["Sistema"])
def root() -> dict:
    """Rota raiz com atalhos uteis."""
    return {
        "name": settings.PLATFORM_NAME,
        "version": __version__,
        "docs": "/docs",
        "openai_base_url": "/v1",
    }
