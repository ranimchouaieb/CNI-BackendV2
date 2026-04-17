from typing import Optional

from sqlalchemy.orm import Session, joinedload

from models.user import UserORM
from schemas.user import UserUpdate
from shared.security import hash_password, verify_password


class UserService:

    def __init__(self, db: Session):
        self.db = db

    def list_all(self, role: Optional[str] = None, search: Optional[str] = None) -> list[UserORM]:
        q = self.db.query(UserORM)
        if role:
            q = q.filter(UserORM.role == role)
        if search:
            q = q.filter(
                (UserORM.nom.ilike(f"%{search}%")) |
                (UserORM.prenom.ilike(f"%{search}%")) |
                (UserORM.email.ilike(f"%{search}%"))
            )
        return q.order_by(UserORM.nom).all()

    def get_by_id(self, user_id: int) -> UserORM:
        user = self.db.get(UserORM, user_id)
        if not user:
            raise LookupError(f"Utilisateur {user_id} introuvable")
        return user

    def modifier(self, user_id: int, data: UserUpdate, requester: UserORM) -> UserORM:
        user = self.get_by_id(user_id)
        if not requester.is_admin() and requester.id != user_id:
            raise ValueError("Vous ne pouvez modifier que votre propre profil")

        update_fields = data.model_dump(exclude_unset=True)
        if "is_active" in update_fields and not requester.is_admin():
            raise ValueError("Seul un admin peut modifier le statut actif d'un compte")

        for field, value in update_fields.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def changer_mot_de_passe(self, user_id: int, old_password: str, new_password: str) -> None:
        user = self.get_by_id(user_id)
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Ancien mot de passe incorrect")
        if len(new_password) < 8:
            raise ValueError("Le nouveau mot de passe doit contenir au moins 8 caractères")
        user.password_hash = hash_password(new_password)
        self.db.commit()

    def toggle_active(self, user_id: int) -> UserORM:
        user = self.get_by_id(user_id)
        user.is_active = not user.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_destinataires(self, current_user: UserORM) -> list[UserORM]:
        """Liste des utilisateurs à qui current_user peut envoyer un message."""
        from models.inscription import InscriptionORM
        from models.associations import cycle_formateurs

        if current_user.is_admin():
            return (
                self.db.query(UserORM)
                .filter(UserORM.id != current_user.id)
                .order_by(UserORM.nom)
                .all()
            )

        if current_user.is_formateur():
            admin_ids = self.db.query(UserORM.id).filter(UserORM.role == "admin").subquery()
            participant_ids = (
                self.db.query(InscriptionORM.participant_id)
                .join(cycle_formateurs, cycle_formateurs.c.cycle_id == InscriptionORM.cycle_id)
                .filter(
                    cycle_formateurs.c.user_id == current_user.id,
                    InscriptionORM.statut == "confirme",
                )
                .subquery()
            )
            return (
                self.db.query(UserORM)
                .filter(
                    UserORM.id != current_user.id,
                    (UserORM.id.in_(admin_ids)) | (UserORM.id.in_(participant_ids)),
                )
                .order_by(UserORM.nom)
                .all()
            )

        # Participant
        admin_ids = self.db.query(UserORM.id).filter(UserORM.role == "admin").subquery()
        formateur_ids = (
            self.db.query(cycle_formateurs.c.user_id)
            .join(InscriptionORM, InscriptionORM.cycle_id == cycle_formateurs.c.cycle_id)
            .filter(
                InscriptionORM.participant_id == current_user.id,
                InscriptionORM.statut == "confirme",
            )
            .subquery()
        )
        return (
            self.db.query(UserORM)
            .filter(
                UserORM.id != current_user.id,
                (UserORM.id.in_(admin_ids)) | (UserORM.id.in_(formateur_ids)),
            )
            .order_by(UserORM.nom)
            .all()
        )
