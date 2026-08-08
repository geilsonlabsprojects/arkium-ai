"""Rotas de perfil do usuario logado e administracao de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import PasswordChange, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Usuarios"])


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)) -> UserOut:
    """Perfil do usuario autenticado."""
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    """Atualiza nome e/ou e-mail do usuario autenticado."""
    if payload.email:
        email = payload.email.lower().strip()
        clash = db.query(User).filter(User.email == email, User.id != user.id).first()
        if clash:
            raise HTTPException(status.HTTP_409_CONFLICT, "Este e-mail ja esta em uso")
        user.email = email
    if payload.name is not None:
        user.name = payload.name.strip()
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/me/password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Troca a senha exigindo a senha atual."""
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Senha atual incorreta")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Senha alterada com sucesso."}


@router.get("", response_model=list[UserOut])
def list_users(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """Lista todos os usuarios (somente administradores)."""
    return [UserOut.model_validate(u) for u in db.query(User).order_by(User.id).all()]


@router.patch("/{user_id}/active", response_model=UserOut)
def toggle_active(
    user_id: int,
    active: bool,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> UserOut:
    """Ativa/desativa uma conta (nao permite se auto-desativar)."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao e possivel alterar o proprio status")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")
    target.is_active = active
    db.commit()
    db.refresh(target)
    return UserOut.model_validate(target)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    """Remove um usuario e todos os seus dados relacionados."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao e possivel excluir a propria conta")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")
    db.delete(target)
    db.commit()
