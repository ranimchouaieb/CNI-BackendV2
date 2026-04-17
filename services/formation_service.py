from typing import Optional

from sqlalchemy.orm import Session

from models.formation import FormationORM
from schemas.formation import FormationCreate, FormationUpdate


class FormationService:

    def __init__(self, db: Session):
        self.db = db

    def get_domaines(self) -> list[str]:
        rows = (
            self.db.query(FormationORM.domaine)
            .filter(FormationORM.domaine.isnot(None))
            .distinct()
            .order_by(FormationORM.domaine)
            .all()
        )
        return [r.domaine for r in rows]

    def list_all(self, search: Optional[str] = None, domaine: Optional[str] = None, limit: Optional[int] = None) -> list[FormationORM]:
        q = self.db.query(FormationORM)
        if search:
            q = q.filter(FormationORM.titre.ilike(f"%{search}%"))
        if domaine:
            q = q.filter(FormationORM.domaine == domaine)
        q = q.order_by(FormationORM.titre)
        if limit:
            q = q.limit(limit)
        return q.all()

    def check_duplicate(self, titre: str, exclude_id: Optional[int] = None) -> dict:
        q = self.db.query(FormationORM).filter(FormationORM.titre == titre)
        if exclude_id:
            q = q.filter(FormationORM.id != exclude_id)
        exists = q.first() is not None
        return {"duplicate": exists}

    def get_by_id(self, formation_id: int) -> FormationORM:
        f = self.db.get(FormationORM, formation_id)
        if not f:
            raise LookupError(f"Formation {formation_id} introuvable")
        return f

    def creer(self, data: FormationCreate) -> FormationORM:
        if self.db.query(FormationORM).filter(FormationORM.titre == data.titre).first():
            raise ValueError(f"Une formation avec le titre '{data.titre}' existe déjà")
        formation = FormationORM(**data.model_dump())
        self.db.add(formation)
        self.db.commit()
        self.db.refresh(formation)
        return formation

    def modifier(self, formation_id: int, data: FormationUpdate) -> FormationORM:
        formation = self.get_by_id(formation_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(formation, field, value)
        self.db.commit()
        self.db.refresh(formation)
        return formation

    def supprimer(self, formation_id: int) -> None:
        formation = self.get_by_id(formation_id)
        if formation.cycles:
            raise ValueError("Impossible de supprimer une formation avec des cycles existants")
        self.db.delete(formation)
        self.db.commit()
