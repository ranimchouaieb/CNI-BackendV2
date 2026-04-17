from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from schemas.user import UserResponse
from services.auth_service import AuthService
from deps import get_auth_service, get_current_user
from models.user import UserORM

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, svc: AuthService = Depends(get_auth_service)):
    return svc.register(data)


@router.post("/login", response_model=TokenResponse) # response_model is not the database model and not the service return type — it’s the shape of the JSON response that clients will receive
def login(form: OAuth2PasswordRequestForm = Depends(), svc: AuthService = Depends(get_auth_service)):
    """Login via form-data (OAuth2 standard — utilisé par /docs)."""
    token, user = svc.login(form.username, form.password)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        nom=user.nom,
        prenom=user.prenom,
        totp_required=user.totp_enabled,
    )


@router.post("/login-json", response_model=TokenResponse)
def login_json(data: LoginRequest, svc: AuthService = Depends(get_auth_service)):
    """Login via JSON body (utilisé par le frontend)."""
    token, user = svc.login(data.email, data.password)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        nom=user.nom,
        prenom=user.prenom,
        totp_required=user.totp_enabled,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserORM = Depends(get_current_user)):
    return current_user
