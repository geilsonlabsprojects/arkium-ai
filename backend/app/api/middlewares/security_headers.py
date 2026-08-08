"""Middleware de cabecalhos de seguranca (equivalente ao Helmet do Node)."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "1; mode=block",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona headers defensivos a todas as respostas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in HEADERS.items():
            response.headers.setdefault(header, value)
        return response
