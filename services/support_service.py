import os
from sqlalchemy.orm import Session

from models.support import SupportCoursORM
from models.cycle import CycleORM
from models.notification import NotificationORM
from models.inscription import InscriptionORM
from fastapi import UploadFile

SUPPORT_DIR = "uploads/supports"


class SupportService:

    def __init__(self, db: Session):
        self.db = db

    def list_by_cycle(self, cycle_id: int, user_id: int, user_role: str) -> list[SupportCoursORM]:
        cycle = self.db.get(CycleORM, cycle_id)
        if not cycle:
            raise LookupError(f"Cycle {cycle_id} introuvable")

        # Vérification accès : admin, formateur du cycle, ou participant confirmé
        if user_role == "participant":
            insc = self.db.query(InscriptionORM).filter(
                InscriptionORM.cycle_id == cycle_id,
                InscriptionORM.participant_id == user_id,
                InscriptionORM.statut == "confirme",
            ).first()
            if not insc:
                raise ValueError("Vous n'avez pas accès aux supports de ce cycle")

        return self.db.query(SupportCoursORM).filter(SupportCoursORM.cycle_id == cycle_id).all()

    def uploader(self, cycle_id: int, formateur_id: int, titre: str, description: str, file: UploadFile) -> SupportCoursORM:
        cycle = self.db.get(CycleORM, cycle_id)
        if not cycle:
            raise LookupError(f"Cycle {cycle_id} introuvable")

        is_formateur_du_cycle = any(f.id == formateur_id for f in cycle.formateurs)
        if not is_formateur_du_cycle:
            raise ValueError("Vous n'êtes pas formateur de ce cycle")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".pptx", ".docx", ".xlsx", ".zip"):
            raise ValueError("Format non accepté (PDF, PPTX, DOCX, XLSX, ZIP)")

        os.makedirs(SUPPORT_DIR, exist_ok=True)
        filename = f"support_{cycle_id}_{formateur_id}_{os.urandom(4).hex()}{ext}"
        filepath = os.path.join(SUPPORT_DIR, filename)

        with open(filepath, "wb") as f:
            content = file.file.read()
            if len(content) > 50 * 1024 * 1024:
                raise ValueError("Fichier trop volumineux (max 50 MB)")
            f.write(content)

        support = SupportCoursORM(
            cycle_id=cycle_id,
            formateur_id=formateur_id,
            titre=titre,
            description=description,
            fichier_path=filepath,
            fichier_type=ext.lstrip("."),
        )
        self.db.add(support)
        self.db.flush()

        self._notifier_participants(cycle)
        self._notifier_admins(cycle, titre)
        self.db.commit()
        self.db.refresh(support)
        return support

    def get_fichier_path(self, support_id: int) -> str:
        support = self.db.get(SupportCoursORM, support_id)
        if not support:
            raise LookupError(f"Support {support_id} introuvable")
        return support.fichier_path

    def supprimer(self, support_id: int, formateur_id: int) -> None:
        support = self.db.get(SupportCoursORM, support_id)
        if not support:
            raise LookupError(f"Support {support_id} introuvable")
        if support.formateur_id != formateur_id:
            raise ValueError("Vous ne pouvez supprimer que vos propres supports")
        if os.path.exists(support.fichier_path):
            os.remove(support.fichier_path)
        self.db.delete(support)
        self.db.commit()

    def _notifier_admins(self, cycle: CycleORM, titre: str) -> None:
        from models.user import UserORM
        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="support_cours_ajoute",
                titre=f"Nouveau support de cours ajouté — {cycle.theme_formation}",
                contenu=f"Support : « {titre} »",
                lien_action=f"/admin/cycles",
            ))

    def _notifier_participants(self, cycle: CycleORM) -> None:
        inscrits = self.db.query(InscriptionORM).filter(
            InscriptionORM.cycle_id == cycle.id,
            InscriptionORM.statut == "confirme",
        ).all()
        for insc in inscrits:
            self.db.add(NotificationORM(
                user_id=insc.participant_id,
                type="nouveau_support",
                titre=f"Nouveau support de cours — {cycle.theme_formation}",
                lien_action="/mes-inscriptions",
            ))
