import os
from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.profile import ProfileParticipantORM, ProfileFormateurORM
from models.inscription import InscriptionORM
from models.cycle import CycleORM
from models.user import UserORM
from models.notification import NotificationORM
from schemas.profile import ProfileParticipantUpdate, ProfileFormateurUpdate, ValidateFormateurRequest

CV_DIR_FORMATEUR = "uploads/cvs_formateurs"
CV_DIR_PARTICIPANT = "uploads/cvs_participants"


class ProfileService:

    def __init__(self, db: Session):
        self.db = db

    # ── Participant ───────────────────────────────────────────────────────────

    def get_participant(self, user_id: int) -> ProfileParticipantORM:
        profile = self.db.query(ProfileParticipantORM).filter(
            ProfileParticipantORM.user_id == user_id
        ).first()
        if not profile:
            # Créer si inexistant
            profile = ProfileParticipantORM(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def modifier_participant(self, user_id: int, data: ProfileParticipantUpdate) -> ProfileParticipantORM:
        profile = self.get_participant(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    # ── Formateur ─────────────────────────────────────────────────────────────

    def get_formateur(self, user_id: int) -> ProfileFormateurORM:
        profile = self.db.query(ProfileFormateurORM).filter(
            ProfileFormateurORM.user_id == user_id
        ).first()
        if not profile:
            profile = ProfileFormateurORM(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def modifier_formateur(self, user_id: int, data: ProfileFormateurUpdate) -> ProfileFormateurORM:
        profile = self.get_formateur(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_formateurs(self, statut: Optional[str] = None) -> list[ProfileFormateurORM]:
        q = self.db.query(ProfileFormateurORM)
        if statut:
            q = q.filter(ProfileFormateurORM.statut_validation == statut)
        return q.all()

    def valider_formateur(self, user_id: int, data: ValidateFormateurRequest) -> ProfileFormateurORM:
        if data.statut not in ("valide", "rejete", "suspendu"):
            raise ValueError("Statut invalide")

        profile = self.get_formateur(user_id)

        if data.statut == "valide" and not profile.cv_path:
            raise ValueError("Impossible de valider un formateur sans CV uploadé")

        profile.statut_validation = data.statut
        profile.date_validation = datetime.utcnow()
        profile.validation_commentaire = data.commentaire

        self.db.add(NotificationORM(
            user_id=user_id,
            type="profil_valide" if data.statut == "valide" else "profil_rejete",
            titre="Votre profil formateur a été examiné",
            contenu=data.commentaire or "",
            lien_action="/mon-profil",
        ))

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_progression(self, user_id: int) -> dict:
        """Retourne la progression par cycle pour un participant."""
        inscriptions = (
            self.db.query(InscriptionORM)
            .filter(
                InscriptionORM.participant_id == user_id,
                InscriptionORM.statut == "confirme",
            )
            .all()
        )
        progressions = []
        for insc in inscriptions:
            cycle = self.db.get(CycleORM, insc.cycle_id)
            if not cycle:
                continue
            nb_jours = max(1, (cycle.date_fin - cycle.date_debut).days + 1)
            nb_presences = sum(
                1 for j in range(1, 6)
                if getattr(insc, f"emargement_jour_{j}", False)
            )
            progression = round((nb_presences / nb_jours) * 100, 1)
            eligible_certification = nb_presences >= max(1, nb_jours // 2)
            progressions.append({
                "cycle_id": cycle.id,
                "theme_formation": cycle.theme_formation,
                "date_debut": str(cycle.date_debut),
                "date_fin": str(cycle.date_fin),
                "nb_jours": nb_jours,
                "nb_presences": nb_presences,
                "progression": progression,
                "eligible_certification": eligible_certification,
            })
        return {"progressions": progressions}

    def get_formateur_stats(self, user_id: int) -> dict:
        """Stats globales d'un formateur."""
        from models.associations import cycle_formateurs
        cycles = (
            self.db.query(CycleORM)
            .join(cycle_formateurs, cycle_formateurs.c.cycle_id == CycleORM.id)
            .filter(cycle_formateurs.c.user_id == user_id)
            .all()
        )
        total_cycles = len(cycles)
        total_participants = sum(c.nb_inscrits for c in cycles)
        profile = self.get_formateur(user_id)
        return {
            "total_cycles": total_cycles,
            "total_participants_formes": total_participants,
            "note_moyenne": float(profile.note_moyenne) if profile.note_moyenne else None,
            "nb_evaluations": profile.nb_evaluations,
        }

    def upload_cv_participant(self, user_id: int, file: UploadFile) -> ProfileParticipantORM:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".doc", ".docx"):
            raise ValueError("Format non accepté (PDF, DOC, DOCX)")

        os.makedirs(CV_DIR_PARTICIPANT, exist_ok=True)
        filename = f"cv_participant_{user_id}{ext}"
        filepath = os.path.join(CV_DIR_PARTICIPANT, filename)

        with open(filepath, "wb") as f:
            content = file.file.read()
            if len(content) > 20 * 1024 * 1024:
                raise ValueError("CV trop volumineux (max 20 MB)")
            f.write(content)

        profile = self.get_participant(user_id)
        profile.cv_path = filepath
        profile.cv_uploaded_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upload_cv_formateur(self, user_id: int, file: UploadFile) -> ProfileFormateurORM:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext != ".pdf":
            raise ValueError("Le CV doit être au format PDF")

        os.makedirs(CV_DIR_FORMATEUR, exist_ok=True)
        filename = f"cv_formateur_{user_id}.pdf"
        filepath = os.path.join(CV_DIR_FORMATEUR, filename)

        with open(filepath, "wb") as f:
            content = file.file.read()
            if len(content) > 20 * 1024 * 1024:
                raise ValueError("CV trop volumineux (max 20 MB)")
            f.write(content)

        profile = self.get_formateur(user_id)
        profile.cv_path = filepath
        profile.cv_uploaded_at = datetime.utcnow()

        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="cv_formateur_soumis",
                titre="CV formateur soumis",
                lien_action="/admin/formateurs",
            ))

        self.db.commit()
        self.db.refresh(profile)
        return profile
