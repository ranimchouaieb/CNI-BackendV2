import os
import shutil
from datetime import date
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session, joinedload

from models.cycle import CycleORM
from models.user import UserORM
from models.notification import NotificationORM
from schemas.cycle import CycleCreate, CycleUpdate

PROGRAMMES_DIR = os.path.join("uploads", "programmes")
ALLOWED_PROGRAMME_EXTENSIONS = [".pdf", ".doc", ".docx"]


def _calculer_statut(cycle: CycleORM) -> str:
    if cycle.is_cancelled:
        return "rouge"
    today = date.today()
    if cycle.date_fin < today:
        return "termine"
    if cycle.date_debut <= today:
        return "vert"
    return "orange"


class CycleService:

    def __init__(self, db: Session):
        self.db = db

    def _get_with_relations(self, cycle_id: int) -> CycleORM:
        cycle = (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
            .filter(CycleORM.id == cycle_id)
            .first()
        )
        if not cycle:
            raise LookupError(f"Cycle {cycle_id} introuvable")
        return cycle

    def list_all(
        self,
        gouvernorat: Optional[str] = None,
        statut: Optional[str] = None,
        search: Optional[str] = None,
        include_cancelled: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CycleORM]:
        q = (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
        )
        if not include_cancelled:
            q = q.filter(CycleORM.is_cancelled == False)
        if gouvernorat:
            q = q.filter(CycleORM.gouvernorat == gouvernorat)
        if statut:
            q = q.filter(CycleORM.statut == statut)
        if search:
            q = q.filter(CycleORM.theme_formation.ilike(f"%{search}%"))
        return q.order_by(CycleORM.date_debut.desc()).offset(skip).limit(limit).all()

    def list_disponibles(self) -> list[CycleORM]:
        """Cycles ouverts à l'inscription (futurs, non annulés, pas pleins)."""
        return (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
            .filter(
                CycleORM.is_cancelled == False,
                CycleORM.date_debut > date.today(),
                CycleORM.nb_inscrits < CycleORM.capacite_max,
            )
            .order_by(CycleORM.date_debut)
            .all()
        )

    def list_annules(self) -> list[CycleORM]:
        return (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
            .filter(CycleORM.is_cancelled == True)
            .order_by(CycleORM.date_debut.desc())
            .limit(20)
            .all()
        )

    def list_termines(self) -> list[CycleORM]:
        return (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
            .filter(CycleORM.is_cancelled == False, CycleORM.date_fin < date.today())
            .order_by(CycleORM.date_fin.desc())
            .limit(20)
            .all()
        )

    def list_by_formation(self, formation_id: int) -> list[CycleORM]:
        return (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs))
            .filter(CycleORM.formation_id == formation_id)
            .order_by(CycleORM.date_debut.desc())
            .all()
        )

    def list_by_formateur(self, formateur_id: int) -> list[CycleORM]:
        formateur = self.db.get(UserORM, formateur_id)
        if not formateur:
            raise LookupError(f"Formateur {formateur_id} introuvable")
        return (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.formation))
            .filter(CycleORM.formateurs.any(UserORM.id == formateur_id))
            .order_by(CycleORM.date_debut.desc())
            .all()
        )

    def get_by_id(self, cycle_id: int) -> CycleORM:
        return self._get_with_relations(cycle_id)

    def creer(self, data: CycleCreate) -> CycleORM:
        if data.date_fin < data.date_debut:
            raise ValueError("La date de fin doit être après la date de début")

        formateurs = []
        for fid in data.formateur_ids:
            f = self.db.get(UserORM, fid)
            if not f or f.role != "formateur":
                raise LookupError(f"Formateur {fid} introuvable")
            formateurs.append(f)

        cycle_data = data.model_dump(exclude={"formateur_ids"})
        cycle = CycleORM(**cycle_data)
        cycle.formateurs = formateurs
        cycle.statut = _calculer_statut(cycle)

        self.db.add(cycle)
        self.db.flush()

        for f in formateurs:
            self._notifier_formateur(f.id, cycle)

        self.db.commit()
        self.db.refresh(cycle)
        return self._get_with_relations(cycle.id)

    def modifier(self, cycle_id: int, data: CycleUpdate) -> CycleORM:
        cycle = self._get_with_relations(cycle_id)
        old_formateur_ids = {f.id for f in cycle.formateurs}

        update_data = data.model_dump(exclude_unset=True)
        new_formateur_ids = update_data.pop("formateur_ids", None)

        for field, value in update_data.items():
            setattr(cycle, field, value)

        if new_formateur_ids is not None:
            formateurs = []
            for fid in new_formateur_ids:
                f = self.db.get(UserORM, fid)
                if not f or f.role != "formateur":
                    raise LookupError(f"Formateur {fid} introuvable")
                formateurs.append(f)
            cycle.formateurs = formateurs
            added = set(new_formateur_ids) - old_formateur_ids
            for fid in added:
                self._notifier_formateur(fid, cycle)

        cycle.statut = _calculer_statut(cycle)
        self.db.commit()
        return self._get_with_relations(cycle_id)

    def supprimer(self, cycle_id: int) -> None:
        cycle = self.get_by_id(cycle_id)
        if cycle.nb_inscrits > 0:
            raise ValueError("Impossible de supprimer un cycle avec des inscrits")
        if cycle.certifications:
            raise ValueError("Impossible de supprimer un cycle avec des attestations émises")
        self.db.delete(cycle)
        self.db.commit()

    def upload_programme(self, cycle_id: int, user_id: int, user_role: str, file: UploadFile) -> dict:
        cycle = self._get_with_relations(cycle_id)
        if user_role == "participant":
            raise ValueError("Accès réservé admin/formateur")
        if user_role == "formateur" and not any(f.id == user_id for f in cycle.formateurs):
            raise ValueError("Ce cycle ne vous est pas assigné")

        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in ALLOWED_PROGRAMME_EXTENSIONS:
            raise ValueError(f"Format non autorisé. Acceptés : {', '.join(ALLOWED_PROGRAMME_EXTENSIONS)}")

        os.makedirs(PROGRAMMES_DIR, exist_ok=True)
        safe_filename = f"programme_cycle_{cycle_id}{file_ext}"
        file_path = os.path.join(PROGRAMMES_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cycle.programme = file_path
        self.db.commit()
        return {"message": "Programme uploadé avec succès", "filename": safe_filename}

    def get_programme_path(self, cycle_id: int) -> str:
        cycle = self._get_with_relations(cycle_id)
        if not cycle.programme or not os.path.exists(cycle.programme):
            raise LookupError("Programme non disponible pour ce cycle")
        return cycle.programme

    def _notifier_formateur(self, formateur_id: int, cycle: CycleORM) -> None:
        self.db.add(NotificationORM(
            user_id=formateur_id,
            type="cycle_assigne",
            titre="Nouveau cycle assigné",
            contenu=f"Vous avez été assigné au cycle : {cycle.theme_formation} ({cycle.date_debut} → {cycle.date_fin})",
            lien_action="/formateur-cycles",
        ))
