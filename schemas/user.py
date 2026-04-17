from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    nom: str
    prenom: str
    numero_cin: Optional[str] = None
    telephone: Optional[str] = None
    is_active: Optional[bool] = True
    totp_enabled: Optional[bool] = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
