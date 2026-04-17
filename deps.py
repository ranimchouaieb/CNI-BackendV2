"""
Provider central — toutes les fonctions Depends() sont ici.
Les routers importent uniquement depuis deps.py, jamais depuis les services directement.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from shared.security import decode_token
from models.user import UserORM
from services.auth_service import AuthService
from services.formation_service import FormationService
from services.cycle_service import CycleService
from services.inscription_service import InscriptionService
from services.certification_service import CertificationService
from services.user_service import UserService
from services.profile_service import ProfileService
from services.message_service import MessageService
from services.support_service import SupportService
from services.dashboard_service import DashboardService
from services.pdf_service import PdfService
from services.ai_service import AiService
from services.rapport_absence_service import RapportAbsenceService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ── Authentification ──────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserORM:
    payload = decode_token(token)
    user = db.get(UserORM, int(payload.get("sub")))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable ou inactif")
    return user


def get_current_admin(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    if not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux admins")
    return current_user


def get_current_formateur(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    if not current_user.is_formateur() and not current_user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé aux formateurs")
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[UserORM]:
    if not token:
        return None
    try:
        payload = decode_token(token)
        return db.get(UserORM, int(payload.get("sub")))
    except Exception:
        return None


# ── Services ──────────────────────────────────────────────────────────────────

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_formation_service(db: Session = Depends(get_db)) -> FormationService:
    return FormationService(db)


def get_cycle_service(db: Session = Depends(get_db)) -> CycleService:
    return CycleService(db)


def get_inscription_service(db: Session = Depends(get_db)) -> InscriptionService:
    return InscriptionService(db)


def get_certification_service(db: Session = Depends(get_db)) -> CertificationService:
    return CertificationService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    return ProfileService(db)


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    return MessageService(db)


def get_support_service(db: Session = Depends(get_db)) -> SupportService:
    return SupportService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_pdf_service(db: Session = Depends(get_db)) -> PdfService:
    return PdfService(db)


def get_ai_service(db: Session = Depends(get_db)) -> AiService:
    return AiService(db)


def get_rapport_absence_service(db: Session = Depends(get_db)) -> RapportAbsenceService:
    return RapportAbsenceService(db)
