from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.user import UserORM
from models.profile import ProfileParticipantORM, ProfileFormateurORM
from models.notification import NotificationORM
from schemas.auth import RegisterRequest
from shared.security import hash_password, verify_password, create_token
import random


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterRequest) -> UserORM:
        if self.db.query(UserORM).filter(UserORM.email == data.email).first():
            raise ValueError("Cet email est déjà utilisé")
        if data.numero_cin and self.db.query(UserORM).filter(UserORM.numero_cin == data.numero_cin).first():
            raise ValueError("Ce numéro CIN est déjà utilisé")

        user = UserORM(
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            nom=data.nom,
            prenom=data.prenom,
            numero_cin=data.numero_cin,
            telephone=data.telephone,
        )
        self.db.add(user)
        self.db.flush()

        # Créer profil automatiquement selon le rôle
        if data.role == "participant":
            self.db.add(ProfileParticipantORM(user_id=user.id))
        elif data.role == "formateur":
            self.db.add(ProfileFormateurORM(user_id=user.id))
            self._notifier_admins_nouveau_formateur(user)

        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> tuple[str, UserORM]:
        user = self.db.query(UserORM).filter(UserORM.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Email ou mot de passe incorrect")
        if not user.is_active:
            raise ValueError("Compte désactivé")
        """#cas admin +2fa 
        if user.is_admin() and user.totp_enabled:
            code=str(random.randint(100000, 999999)) #générer un code TOTP temporaire
            user.totp_secret=code #stocké dans la base de données
            user.totp_verified_at=datetime.utcnow() + timedelta(minutes=5)""" #code valable 5 minutes #marquer comme non vérifi   rq: on changera le nom apres : expires at = datetime.utcnow() + timedelta(minutes=5) #code valable 5 minutes
        token = create_token({"sub": str(user.id), "role": user.role})
        return token, user

    def _notifier_admins_nouveau_formateur(self, formateur: UserORM) -> None:
        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="nouveau_formateur",
                titre=f"Nouveau formateur inscrit — {formateur.prenom} {formateur.nom}",
                lien_action="/admin/formateurs",
            ))
