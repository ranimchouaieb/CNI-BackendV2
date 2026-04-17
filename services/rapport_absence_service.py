from datetime import date
from sqlalchemy.orm import Session, joinedload

from models.rapport_absence import RapportAbsenceORM
from models.cycle import CycleORM
from models.user import UserORM
from models.notification import NotificationORM
from schemas.rapport_absence import RapportAbsenceCreate, RapportAbsenceUpdate


class RapportAbsenceService:

    def __init__(self, db: Session):
        self.db = db

    def creer(self, formateur_id: int, data: RapportAbsenceCreate) -> RapportAbsenceORM:
        cycle = self.db.query(CycleORM).filter(
            CycleORM.id == data.cycle_id,
            CycleORM.formateurs.any(UserORM.id == formateur_id),
        ).first()
        if not cycle:
            raise LookupError("Cycle introuvable ou non assigné à ce formateur")

        rapport = RapportAbsenceORM(
            cycle_id=data.cycle_id,
            formateur_id=formateur_id,
            date_rapport=data.date_rapport or date.today(),
            contenu=data.contenu,
            participants_absents=[p.model_dump() for p in data.participants_absents],
            statut="brouillon",
        )
        self.db.add(rapport)
        self.db.commit()
        self.db.refresh(rapport)
        return self._load(rapport.id)

    def modifier(self, rapport_id: int, formateur_id: int, data: RapportAbsenceUpdate, is_admin: bool = False) -> RapportAbsenceORM:
        rapport = self.db.query(RapportAbsenceORM).filter(
            RapportAbsenceORM.id == rapport_id,
            RapportAbsenceORM.formateur_id == formateur_id,
        ).first()
        if not rapport:
            raise LookupError("Rapport introuvable")
        if rapport.statut == "soumis" and not is_admin:
            raise ValueError("Un rapport soumis ne peut plus être modifié")

        update_data = data.model_dump(exclude_unset=True)
        if "participants_absents" in update_data and update_data["participants_absents"] is not None:
            update_data["participants_absents"] = [
                p.model_dump() if hasattr(p, "model_dump") else p
                for p in update_data["participants_absents"]
            ]
        for field, value in update_data.items():
            setattr(rapport, field, value)

        if data.statut == "soumis":
            cycle = self.db.get(CycleORM, rapport.cycle_id)
            formateur = self.db.get(UserORM, formateur_id)
            admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
            nom_complet = f"{formateur.prenom} {formateur.nom}" if formateur else "Formateur"
            for admin in admins:
                self.db.add(NotificationORM(
                    user_id=admin.id,
                    type="rapport_absence_soumis",
                    titre="Rapport d'absence soumis",
                    contenu=f"{nom_complet} — {cycle.theme_formation if cycle else ''}",
                    lien_action="/admin/rapports-absence",
                ))

        self.db.commit()
        self.db.refresh(rapport)
        return self._load(rapport.id)

    def list_by_formateur(self, formateur_id: int) -> list[RapportAbsenceORM]:
        return (
            self.db.query(RapportAbsenceORM)
            .options(joinedload(RapportAbsenceORM.cycle))
            .filter(RapportAbsenceORM.formateur_id == formateur_id)
            .order_by(RapportAbsenceORM.date_rapport.desc())
            .all()
        )

    def list_all_soumis(self) -> list[RapportAbsenceORM]:
        rapports = (
            self.db.query(RapportAbsenceORM)
            .options(joinedload(RapportAbsenceORM.cycle), joinedload(RapportAbsenceORM.formateur))
            .filter(RapportAbsenceORM.statut == "soumis")
            .order_by(RapportAbsenceORM.created_at.desc())
            .all()
        )
        for r in rapports:
            r.statut = "vu_admin"
        self.db.commit()
        return rapports

    def get_by_id(self, rapport_id: int) -> RapportAbsenceORM:
        r = self._load(rapport_id)
        if not r:
            raise LookupError(f"Rapport {rapport_id} introuvable")
        return r

    def _load(self, rapport_id: int) -> RapportAbsenceORM:
        return (
            self.db.query(RapportAbsenceORM)
            .options(joinedload(RapportAbsenceORM.cycle), joinedload(RapportAbsenceORM.formateur))
            .filter(RapportAbsenceORM.id == rapport_id)
            .first()
        )
