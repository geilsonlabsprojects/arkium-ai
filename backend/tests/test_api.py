"""Testes de integracao da API (auth, chaves, compatibilidade OpenAI)."""

import pytest


def test_health_responde_mesmo_sem_ollama(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "online"
    assert body["ollama"] in {"online", "offline"}


def test_rota_raiz_e_platform_sao_publicas(client):
    assert client.get("/").status_code == 200
    assert "name" in client.get("/api/platform").json()


def test_login_invalido_nao_revela_se_email_existe(client):
    r1 = client.post("/api/auth/login", json={"email": "admin@arkium-teste.com", "password": "errada"})
    r2 = client.post("/api/auth/login", json={"email": "ninguem@arkium-teste.com", "password": "errada"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_rotas_protegidas_exigem_token(client):
    for path in ("/api/users/me", "/api/keys", "/api/admin/settings"):
        assert client.get(path).status_code in (401, 403)


def test_login_e_perfil(client, auth_headers):
    me = client.get("/api/users/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@arkium-teste.com"
    assert "hashed_password" not in me.json()


def test_ciclo_de_vida_da_api_key(client, auth_headers):
    created = client.post("/api/keys", json={"name": "teste"}, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    raw = body["key"]
    assert raw.startswith("ark-")

    # A chave completa nunca reaparece na listagem
    listed = client.get("/api/keys", headers=auth_headers).json()
    assert all("key" not in item for item in listed)
    assert any(item["key_prefix"] == body["key_prefix"] for item in listed)

    # A chave autentica /v1
    assert client.get("/v1/models", headers={"Authorization": f"Bearer {raw}"}).status_code in (200, 503)

    # Revogada, deixa de autenticar
    client.post(f"/api/keys/{body['id']}/revoke", headers=auth_headers)
    revoked = client.get("/v1/models", headers={"Authorization": f"Bearer {raw}"})
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "invalid_api_key"


def test_api_key_expirada_e_recusada(client, auth_headers):
    created = client.post("/api/keys", json={"name": "curta", "expires_in_days": 1}, headers=auth_headers).json()
    assert created["expires_at"] is not None

    # Força a expiracao diretamente no banco
    from datetime import datetime, timedelta, timezone

    from app.db.session import SessionLocal
    from app.models import ApiKey

    db = SessionLocal()
    key = db.query(ApiKey).filter(ApiKey.id == created["id"]).first()
    key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    db.close()

    response = client.get("/v1/models", headers={"Authorization": f"Bearer {created['key']}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "expired_api_key"


def test_v1_sem_credencial_retorna_erro_no_formato_openai(client):
    response = client.get("/v1/models")
    assert response.status_code == 401
    assert response.json()["error"]["type"] == "invalid_request_error"


def test_usuario_nao_ve_chaves_de_outro(client, auth_headers):
    client.post("/api/auth/register", json={"name": "Outro", "email": "outro@arkium-teste.com", "password": "OutraSenha#2026"})
    token = client.post(
        "/api/auth/login", json={"email": "outro@arkium-teste.com", "password": "OutraSenha#2026"}
    ).json()["access_token"]
    outro = {"Authorization": f"Bearer {token}"}

    minha = client.post("/api/keys", json={"name": "privada"}, headers=auth_headers).json()
    assert client.delete(f"/api/keys/{minha['id']}", headers=outro).status_code == 404
    assert client.get("/api/keys", headers=outro).json() == []


def test_usuario_comum_nao_acessa_area_admin(client):
    token = client.post(
        "/api/auth/login", json={"email": "outro@arkium-teste.com", "password": "OutraSenha#2026"}
    ).json()["access_token"]
    response = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_cabecalhos_de_seguranca_presentes(client):
    headers = client.get("/health").headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert "X-Frame-Options" in headers


def test_chat_completions_com_ollama_offline_retorna_erro_claro(client, auth_headers):
    response = client.post(
        "/v1/chat/completions",
        json={"model": "llama3.2", "messages": [{"role": "user", "content": "oi"}]},
        headers=auth_headers,
    )
    assert response.status_code in (404, 503, 504)
    assert "error" in response.json()
