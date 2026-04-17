from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nom: str
    prenom: str
    role: str
    numero_cin: Optional[str] = None
    telephone: Optional[str] = None

    @field_validator("role")
    @classmethod
    def valider_role(cls, v: str) -> str:
        if v not in ("admin", "formateur", "participant"):
            raise ValueError("Rôle invalide")
        return v

    @field_validator("password")
    @classmethod
    def valider_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    nom: str
    prenom: str
    totp_required: bool = False


class TOTPSetupResponse(BaseModel):
    secret: str
    qr_uri: str


class TOTPVerifyRequest(BaseModel):
    code: str
