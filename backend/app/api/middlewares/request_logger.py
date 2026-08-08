"""Middleware que mede a duracao e loga cada requisicao HTTP."""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging_config import logger


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Registra metodo, caminho, status e tempo de resposta."""

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.1f}"
        logger.info(
            "%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms
        )
        return response
