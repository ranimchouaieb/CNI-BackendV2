from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.user import UserResponse, UserUpdate, ChangePasswordRequest
from services.user_service import UserService
from deps import get_user_service, get_current_admin, get_current_user
from models.user import UserORM

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin=Depends(get_current_admin),
    svc: UserService = Depends(get_user_service),
):
    return svc.list_all(role=role, search=search)


@router.get("/destinataires", response_model=List[UserResponse])
def get_destinataires(
    current_user: UserORM = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.get_destinataires(current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    if not current_user.is_admin() and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return svc.get_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def modifier_user(
    user_id: int,
    data: UserUpdate,
    current_user: UserORM = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.modifier(user_id, data, current_user)


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_active(
    user_id: int,
    admin=Depends(get_current_admin),
    svc: UserService = Depends(get_user_service),
):
    return svc.toggle_active(user_id)


@router.post("/change-password", status_code=204)
def changer_mot_de_passe(
    data: ChangePasswordRequest,
    current_user: UserORM = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    svc.changer_mot_de_passe(current_user.id, data.old_password, data.new_password)
