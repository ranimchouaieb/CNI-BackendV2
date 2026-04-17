import os
from datetime import date, datetime
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session, joinedload

from models.inscription import InscriptionORM
from models.cycle import CycleORM
from models.user import UserORM
from models.notification import NotificationORM
from models.profile import ProfileFormateurORM
from schemas.inscription import InscriptionCreate, EmargementUpdate, EvaluationCreate
from shared.enums import StatutInscription

_DATE_FMT = "%Y-%m-%d"

UPLOAD_DIR = "uploads/paiements"


class InscriptionService:

    def __init__(self, db: Session):
        self.db = db

    def _get_cycle(self, cycle_id: int) -> CycleORM:
        cycle = self.db.get(CycleORM, cycle_id)
        if not cycle:
            raise LookupError(f"Cycle {cycle_id} introuvable")
        return cycle

    def _get_inscription(self, inscription_id: int) -> InscriptionORM:
        insc = (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant), joinedload(InscriptionORM.cycle))
            .filter(InscriptionORM.id == inscription_id)
            .first()
        )
        if not insc:
            raise LookupError(f"Inscription {inscription_id} introuvable")
        return insc

    def creer(self, participant_id: int, data: InscriptionCreate) -> InscriptionORM:
        cycle = self._get_cycle(data.cycle_id)

        if cycle.is_cancelled:
            raise ValueError("Ce cycle est annulé")
        if cycle.date_debut <= date.today():
            raise ValueError("Le cycle a déjà commencé — inscription impossible")
        if cycle.nb_inscrits >= cycle.capacite_max:
            raise ValueError("Capacité maximale du cycle atteinte")

        doublon = self.db.query(InscriptionORM).filter(
            InscriptionORM.participant_id == participant_id,
            InscriptionORM.cycle_id == data.cycle_id,
        ).first()
        if doublon:
            raise ValueError("Vous êtes déjà inscrit à ce cycle")

        # Vérification chevauchement
        inscriptions_actives = (
            self.db.query(InscriptionORM)
            .join(CycleORM)
            .filter(
                InscriptionORM.participant_id == participant_id,
                InscriptionORM.statut.in_(["en_attente_validation", "confirme"]),
                InscriptionORM.cycle_id != data.cycle_id,
            )
            .all()
        )
        for insc in inscriptions_actives:
            other = self.db.get(CycleORM, insc.cycle_id)
            if other and not (cycle.date_fin < other.date_debut or cycle.date_debut > other.date_fin):
                raise ValueError(
                    f"Chevauchement avec le cycle '{other.theme_formation}' "
                    f"({other.date_debut} → {other.date_fin})"
                )

        inscription = InscriptionORM(
            participant_id=participant_id,
            cycle_id=data.cycle_id,
            numero_cin=data.numero_cin,
            direction_service=data.direction_service,
            entreprise_participant=data.entreprise_participant,
            statut=StatutInscription.EN_ATTENTE.value,
        )
        self.db.add(inscription)
        self.db.flush()
        self._notifier_admins_inscription(cycle)
        self.db.commit()
        self.db.refresh(inscription)
        return self._get_inscription(inscription.id)

    def list_by_cycle(self, cycle_id: int) -> list[InscriptionORM]:
        return (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant), joinedload(InscriptionORM.cycle))
            .filter(InscriptionORM.cycle_id == cycle_id)
            .all()
        )

    def list_by_participant(self, participant_id: int) -> list[InscriptionORM]:
        return (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant), joinedload(InscriptionORM.cycle))
            .filter(InscriptionORM.participant_id == participant_id)
            .order_by(InscriptionORM.date_inscription.desc())
            .all()
        )

    def list_all(self) -> list[InscriptionORM]:
        return (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant), joinedload(InscriptionORM.cycle))
            .order_by(InscriptionORM.date_inscription.desc())
            .all()
        )

    def list_filtered(
        self,
        user_id: int,
        role: str,
        nom: Optional[str] = None,
        cin: Optional[str] = None,
        formation: Optional[str] = None,
        date_debut: Optional[str] = None,
        statut: Optional[str] = None,
        page_size: int = 100,
    ) -> list[InscriptionORM]:
        q = self.db.query(InscriptionORM).options(
            joinedload(InscriptionORM.participant),
            joinedload(InscriptionORM.cycle),
        )
        if role == "participant":
            q = q.filter(InscriptionORM.participant_id == user_id)
        elif role == "formateur":
            sub = (
                self.db.query(CycleORM.id)
                .filter(CycleORM.formateurs.any(UserORM.id == user_id))
                .subquery()
            )
            q = q.filter(InscriptionORM.cycle_id.in_(sub))

        cycle_joined = False
        if nom:
            q = q.join(InscriptionORM.participant, isouter=True).filter(
                (UserORM.nom.ilike(f"%{nom}%")) | (UserORM.prenom.ilike(f"%{nom}%"))
            )
        if cin:
            q = q.filter(InscriptionORM.numero_cin.ilike(f"%{cin}%"))
        if formation:
            q = q.join(InscriptionORM.cycle, isouter=True).filter(
                CycleORM.theme_formation.ilike(f"%{formation}%")
            )
            cycle_joined = True
        if date_debut:
            try:
                parsed = date.fromisoformat(date_debut)
                if not cycle_joined:
                    q = q.join(InscriptionORM.cycle, isouter=True)
                q = q.filter(CycleORM.date_debut == parsed)
            except ValueError:
                pass
        if statut:
            q = q.filter(InscriptionORM.statut == statut)

        return q.order_by(InscriptionORM.date_inscription.desc()).limit(page_size).all()

    def check_eligibility(self, cycle_id: int, user_id: int) -> dict:
        errors = []
        try:
            cycle = self._get_cycle(cycle_id)
        except LookupError as e:
            return {"eligible": False, "errors": [str(e)]}

        if cycle.is_cancelled:
            errors.append("Ce cycle est annulé")
        elif cycle.date_debut <= date.today():
            errors.append("Le cycle a déjà commencé")
        elif cycle.nb_inscrits >= cycle.capacite_max:
            errors.append("Capacité maximale atteinte")

        doublon = self.db.query(InscriptionORM).filter(
            InscriptionORM.participant_id == user_id,
            InscriptionORM.cycle_id == cycle_id,
        ).first()
        if doublon:
            errors.append("Vous êtes déjà inscrit à ce cycle")

        return {"eligible": len(errors) == 0, "errors": errors}

    def soumettre_emargement_notifie(self, cycle_id: int, formateur_id: int, formateur_prenom: str, formateur_nom: str) -> dict:
        cycle = self._get_cycle(cycle_id)
        if not any(f.id == formateur_id for f in cycle.formateurs):
            raise ValueError("Ce cycle ne vous est pas assigné")

        inscriptions = (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant))
            .filter(
                InscriptionORM.cycle_id == cycle_id,
                InscriptionORM.statut == "confirme",
            )
            .all()
        )

        total = len(inscriptions)
        presents = [sum(1 for i in inscriptions if getattr(i, f"emargement_jour_{j}")) for j in range(1, 6)]
        contenu = (
            f"Récapitulatif émargement — {cycle.theme_formation}\n"
            f"Soumis par : {formateur_prenom} {formateur_nom}\n"
            f"Participants confirmés : {total}\n"
            f"Présences : J1={presents[0]} | J2={presents[1]} | J3={presents[2]} | J4={presents[3]} | J5={presents[4]}"
        )

        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="emargement_soumis",
                titre=f"Feuille de présence soumise — {cycle.theme_formation}",
                contenu=contenu,
                lien_action="/admin/emargement",
            ))
        self.db.commit()
        return {
            "message": f"{len(admins)} administrateur(s) notifié(s)",
            "cycle_id": cycle_id,
            "inscriptions": inscriptions,
        }

    def update(self, inscription_id: int, fields: dict) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        allowed = {
            "note_evaluation", "commentaire",
            "emargement_jour_1", "emargement_jour_2", "emargement_jour_3",
            "emargement_jour_4", "emargement_jour_5",
        }
        for field, value in fields.items():
            if field in allowed:
                setattr(insc, field, value)
        if any(f.startswith("emargement") for f in fields):
            self._try_auto_certification(insc)
        self.db.commit()
        return self._get_inscription(inscription_id)

    def soumettre_emargement_cycle(self, cycle_id: int) -> list[InscriptionORM]:
        return self.list_by_cycle(cycle_id)

    def list_en_attente(self) -> list[InscriptionORM]:
        return (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.participant), joinedload(InscriptionORM.cycle))
            .filter(InscriptionORM.statut == StatutInscription.EN_ATTENTE.value)
            .order_by(InscriptionORM.date_inscription)
            .all()
        )

    def get_by_id(self, inscription_id: int) -> InscriptionORM:
        return self._get_inscription(inscription_id)

    def valider(self, inscription_id: int, admin_id: int, motif: Optional[str] = None) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        if insc.statut != StatutInscription.EN_ATTENTE.value:
            raise ValueError("Seules les inscriptions en attente peuvent être validées")

        insc.statut = StatutInscription.CONFIRME.value
        insc.validation_motif = motif
        insc.validated_by = admin_id
        insc.validated_at = datetime.utcnow()

        cycle = self.db.get(CycleORM, insc.cycle_id)
        if cycle:
            cycle.nb_inscrits = min(cycle.nb_inscrits + 1, cycle.capacite_max)

        self._notifier_participant(insc.participant_id, "inscription_validee",
                                   "Votre inscription a été validée", "/mes-inscriptions")
        self.db.commit()
        return self._get_inscription(inscription_id)

    def rejeter(self, inscription_id: int, admin_id: int, motif: str) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        if insc.statut != StatutInscription.EN_ATTENTE.value:
            raise ValueError("Seules les inscriptions en attente peuvent être rejetées")

        insc.statut = StatutInscription.REJETE.value
        insc.validation_motif = motif
        insc.validated_by = admin_id
        insc.validated_at = datetime.utcnow()

        self._notifier_participant(insc.participant_id, "inscription_rejetee",
                                   f"Votre inscription a été refusée : {motif}", "/mes-inscriptions")
        self.db.commit()
        return self._get_inscription(inscription_id)

    def annuler(self, inscription_id: int, participant_id: int) -> None:
        insc = self._get_inscription(inscription_id)
        if insc.participant_id != participant_id:
            raise ValueError("Vous ne pouvez annuler que vos propres inscriptions")

        if insc.statut == StatutInscription.CONFIRME.value:
            cycle = self.db.get(CycleORM, insc.cycle_id)
            if cycle:
                cycle.nb_inscrits = max(0, cycle.nb_inscrits - 1)

        self.db.delete(insc)
        self.db.commit()

    def upload_preuve_paiement(self, inscription_id: int, participant_id: int, file: UploadFile) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        if insc.participant_id != participant_id:
            raise ValueError("Accès non autorisé")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".jpg", ".jpeg", ".png"):
            raise ValueError("Format de fichier non accepté (PDF, JPG, PNG uniquement)")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"paiement_{inscription_id}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            content = file.file.read()
            if len(content) > 5 * 1024 * 1024:
                raise ValueError("Fichier trop volumineux (max 5 MB)")
            f.write(content)

        insc.preuve_paiement_path = filepath
        insc.preuve_paiement_type = ext.lstrip(".")
        insc.preuve_paiement_uploaded_at = datetime.utcnow()

        self._notifier_admins_preuve(insc)
        self.db.commit()
        self.db.refresh(insc)
        return insc

    def mettre_a_jour_emargement(self, inscription_id: int, data: EmargementUpdate) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        if insc.statut != StatutInscription.CONFIRME.value:
            raise ValueError("L'émargement n'est possible que pour les inscriptions confirmées")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(insc, field, value)

        self.db.flush()
        self._try_auto_certification(insc)
        self.db.commit()
        return self._get_inscription(inscription_id)

    def soumettre_evaluation(self, inscription_id: int, participant_id: int, data: EvaluationCreate) -> InscriptionORM:
        insc = self._get_inscription(inscription_id)
        if insc.participant_id != participant_id:
            raise ValueError("Accès non autorisé")
        if insc.statut != StatutInscription.CONFIRME.value:
            raise ValueError("L'évaluation n'est possible que pour une inscription confirmée")

        cycle = self.db.get(CycleORM, insc.cycle_id)
        if not cycle or cycle.date_fin >= date.today():
            raise ValueError("L'évaluation n'est possible qu'après la fin du cycle")
        if insc.note_evaluation is not None:
            raise ValueError("Vous avez déjà évalué ce cycle")

        insc.note_evaluation = data.note_evaluation
        insc.commentaire = data.commentaire

        self._update_note_formateurs(cycle)
        self.db.commit()
        return self._get_inscription(inscription_id)

    def _try_auto_certification(self, insc: InscriptionORM) -> None:
        from services.certification_service import CertificationService
        CertificationService(self.db).try_auto_generate(insc.id)

    def _update_note_formateurs(self, cycle: CycleORM) -> None:
        for formateur in cycle.formateurs:
            result = (
                self.db.query(
                    InscriptionORM.note_evaluation
                )
                .join(CycleORM)
                .filter(
                    CycleORM.formateurs.any(UserORM.id == formateur.id),
                    InscriptionORM.note_evaluation.isnot(None),
                )
                .all()
            )
            notes = [r[0] for r in result if r[0] is not None]
            if notes:
                avg = sum(notes) / len(notes)
                profile = self.db.query(ProfileFormateurORM).filter(
                    ProfileFormateurORM.user_id == formateur.id
                ).first()
                if profile:
                    profile.note_moyenne = round(avg, 2)
                    profile.nb_evaluations = len(notes)

    def _notifier_admins_inscription(self, cycle: CycleORM) -> None:
        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="inscription_soumise",
                titre=f"Nouvelle inscription — {cycle.theme_formation}",
                lien_action="/admin/inscriptions/en-attente",
            ))

    def _notifier_admins_preuve(self, insc: InscriptionORM) -> None:
        admins = self.db.query(UserORM).filter(UserORM.role == "admin").all()
        for admin in admins:
            self.db.add(NotificationORM(
                user_id=admin.id,
                type="preuve_paiement_soumise",
                titre="Preuve de paiement soumise",
                lien_action="/admin/inscriptions/en-attente",
            ))

    def _notifier_participant(self, participant_id: int, type_: str, titre: str, lien: str) -> None:
        self.db.add(NotificationORM(
            user_id=participant_id,
            type=type_,
            titre=titre,
            lien_action=lien,
        ))
