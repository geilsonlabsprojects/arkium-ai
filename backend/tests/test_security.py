"""Testes das primitivas de seguranca (senhas, JWT, API keys)."""

from app.core import security
from app.core.passwords import hash_password, needs_rehash, verify_password


def test_hash_de_senha_gera_valores_diferentes_e_verifica():
    hashed = hash_password("SenhaForte#2026")
    assert hashed != hash_password("SenhaForte#2026")  # salt aleatorio
    assert verify_password("SenhaForte#2026", hashed)
    assert not verify_password("senha-errada", hashed)


def test_verify_password_nao_explode_com_hash_invalido():
    assert verify_password("qualquer", "nao-e-um-hash") is False
    assert needs_rehash("nao-e-um-hash") in (True, False)


def test_senha_longa_e_aceita():
    # bcrypt trunca em 72 bytes; o wrapper deve tratar sem lancar excecao
    longa = "a" * 200
    assert verify_password(longa, hash_password(longa))


def test_token_de_acesso_valida_escopo():
    token = security.create_access_token("1")
    payload = security.decode_access_token(token)
    assert payload and payload["sub"] == "1"

    reset = security.create_scoped_token("1", security.SCOPE_PASSWORD_RESET, 15)
    # Token de reset NAO pode autenticar a API
    assert security.decode_access_token(reset) is None
    assert security.decode_token(reset, security.SCOPE_PASSWORD_RESET) is not None


def test_token_expirado_e_rejeitado():
    token = security.create_scoped_token("1", security.SCOPE_ACCESS, -1)
    assert security.decode_access_token(token) is None


def test_token_adulterado_e_rejeitado():
    token = security.create_access_token("1")
    assert security.decode_access_token(token[:-3] + "abc") is None


def test_mask_secret_nunca_expoe_o_valor():
    raw, _, _ = security.generate_api_key()
    assert raw not in security.mask_secret(raw)


def test_api_key_tem_prefixo_e_hash_estavel():
    raw, key_hash, prefix = security.generate_api_key()
    assert raw.startswith("ark-")
    assert prefix and raw.startswith(prefix)
    assert security.hash_api_key(raw) == key_hash
    assert len(key_hash) == 64  # sha256 hex
    assert raw not in key_hash
