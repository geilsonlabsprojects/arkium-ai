"""Rotas de autenticacao e perfil do usuario."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenOut,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticacao"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenOut:
    """Cria uma conta. O primeiro usuario do sistema vira administrador."""
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Este e-mail ja esta cadastrado")

    is_first = db.query(User).count() == 0
    user = User(
        email=email,
        name=payload.name.strip(),
        hashed_password=hash_password(payload.password),
        is_admin=is_first,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenOut:
    """Autentica por e-mail e senha e devolve um JWT."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        # Mensagem generica: nao revela se o e-mail existe
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais invalidas")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Conta desativada")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    """Logout e feito no cliente (descarte do token). Endpoint mantido por simetria."""
    return None


@router.post("/password/reset-request")
def reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict:
    """Gera um token de reset de senha valido por um curto periodo.

    Sem servico de e-mail (requisito: nada pago), o token e devolvido na
    resposta apenas quando o e-mail existe; em producao, envie-o por e-mail.
    """
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user:
        return {"message": "Se o e-mail existir, um token de redefinicao sera enviado."}
    token = create_access_token(str(user.id), extra={"scope": "password_reset"})
    return {"message": "Token de redefinicao gerado.", "reset_token": token}


@router.post("/password/reset-confirm")
def reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> dict:
    """Define uma nova senha a partir do token de reset."""
    data = decode_access_token(payload.token)
    if not data or data.get("scope") != "password_reset":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token de redefinicao invalido ou expirado")
    user = db.query(User).filter(User.id == int(data["sub"])).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Senha redefinida com sucesso."}
