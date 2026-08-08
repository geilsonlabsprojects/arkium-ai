"""Fixtures dos testes: banco isolado em arquivo temporario e cliente HTTP."""

import os
import tempfile
from pathlib import Path

import pytest

# Configura o ambiente ANTES de importar a aplicacao
TMP_DB = Path(tempfile.mkdtemp(prefix="arkium-test-")) / "test.db"
os.environ.update(
    {
        "SECRET_KEY": "chave-de-teste-com-mais-de-32-caracteres-000000",
        "DATABASE_URL": f"sqlite:///{TMP_DB}",
        "ADMIN_EMAIL": "admin@arkium-teste.com",
        "ADMIN_PASSWORD": "SenhaForte#2026",
        "RATE_LIMIT_REQUESTS": "1000",
        "LOG_LEVEL": "WARNING",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.init_db import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    init_db()
    yield
    TMP_DB.unlink(missing_ok=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_token(client):
    response = client.post(
        "/api/auth/login", json={"email": "admin@arkium-teste.com", "password": "SenhaForte#2026"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
