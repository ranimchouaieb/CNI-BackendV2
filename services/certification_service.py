import hashlib
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from models.certification import CertificationORM
from models.inscription import InscriptionORM
from models.cycle import CycleORM
from models.user import UserORM
from models.notification import NotificationORM
from config import settings


class CertificationService:

    def __init__(self, db: Session):
        self.db = db

    def _get_inscription(self, inscription_id: int) -> InscriptionORM:
        insc = (
            self.db.query(InscriptionORM)
            .options(joinedload(InscriptionORM.cycle))
            .filter(InscriptionORM.id == inscription_id)
            .first()
        )
        if not insc:
            raise LookupError(f"Inscription {inscription_id} introuvable")
        return insc

    def generer(self, inscription_id: int) -> CertificationORM:
        insc = self._get_inscription(inscription_id)
        cycle = self.db.get(CycleORM, insc.cycle_id)
        if not cycle:
            raise LookupError(f"Cycle {insc.cycle_id} introuvable")

        if cycle.date_fin >= date.today():
            raise ValueError("Le cycle n'est pas encore terminé")

        nb_jours = max(1, (cycle.date_fin - cycle.date_debut).days + 1)
        nb_presences = sum(
            1 for j in range(1, 6)
            if getattr(insc, f"emargement_jour_{j}", False)
        )
        progression = (nb_presences / nb_jours) * 100

        if progression < 50:
            raise ValueError(f"Progression insuffisante ({progression:.0f}% < 50% requis)")

        if self.db.query(CertificationORM).filter(CertificationORM.inscription_id == inscription_id).first():
            raise ValueError("Une attestation a déjà été générée pour cette inscription")

        numero = self._generate_numero()
        hash_cert = self._generate_hash(insc, cycle)

        cert = CertificationORM(
            inscription_id=insc.id,
            participant_id=insc.participant_id,
            cycle_id=insc.cycle_id,
            numero_certification=numero,
            hash_verification=hash_cert,
            date_emission=datetime.utcnow(),
        )
        self.db.add(cert)
        self.db.flush()

        # Génération PDF et stockage du chemin
        try:
            from services.pdf_service import PdfService
            pdf_bytes = PdfService(self.db).attestation_pdf_for_cert(insc, cycle, cert)
            import os
            certs_dir = os.path.join("uploads", "certifications")
            os.makedirs(certs_dir, exist_ok=True)
            pdf_path = os.path.join(certs_dir, f"cert_{cert.numero_certification.replace('-', '_')}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            cert.pdf_path = pdf_path
        except Exception:
            pass  # Non bloquant — le PDF peut être généré à la demande

        self.db.add(NotificationORM(
            user_id=insc.participant_id,
            type="certification_emise",
            titre=f"Attestation de formation émise — {cycle.theme_formation}",
            contenu=f"N° {numero}",
            lien_action="/mes-certifications",
        ))

        self.db.commit()
        self.db.refresh(cert)
        return cert

    def try_auto_generate(self, inscription_id: int) -> Optional[CertificationORM]:
        """Tentative silencieuse — utilisée après chaque mise à jour d'émargement."""
        try:
            return self.generer(inscription_id)
        except (ValueError, LookupError):
            return None

    def list_filtered(
        self,
        nom: Optional[str] = None,
        cin: Optional[str] = None,
        formation: Optional[str] = None,
        date_emission: Optional[str] = None,
    ) -> list[CertificationORM]:
        q = self.db.query(CertificationORM).options(
            joinedload(CertificationORM.participant),
            joinedload(CertificationORM.cycle),
        )
        if nom:
            q = q.join(CertificationORM.participant, isouter=True).filter(
                (UserORM.nom.ilike(f"%{nom}%")) | (UserORM.prenom.ilike(f"%{nom}%"))
            )
        if cin:
            q = q.join(CertificationORM.participant, isouter=True).filter(
                UserORM.numero_cin.ilike(f"%{cin}%")
            )
        if formation:
            q = q.join(CertificationORM.cycle, isouter=True).filter(
                CycleORM.theme_formation.ilike(f"%{formation}%")
            )
        if date_emission:
            try:
                parsed = date.fromisoformat(date_emission)
                q = q.filter(
                    CertificationORM.date_emission >= datetime(parsed.year, parsed.month, parsed.day),
                    CertificationORM.date_emission < datetime(parsed.year, parsed.month, parsed.day, 23, 59, 59),
                )
            except ValueError:
                pass
        return q.order_by(CertificationORM.date_emission.desc()).all()

    def list_all(self) -> list[CertificationORM]:
        return (
            self.db.query(CertificationORM)
            .options(
                joinedload(CertificationORM.participant),
                joinedload(CertificationORM.cycle),
            )
            .order_by(CertificationORM.date_emission.desc())
            .all()
        )

    def list_by_participant(self, participant_id: int) -> list[CertificationORM]:
        return (
            self.db.query(CertificationORM)
            .options(joinedload(CertificationORM.cycle))
            .filter(CertificationORM.participant_id == participant_id)
            .order_by(CertificationORM.date_emission.desc())
            .all()
        )

    def get_by_id(self, cert_id: int) -> CertificationORM:
        cert = (
            self.db.query(CertificationORM)
            .options(
                joinedload(CertificationORM.participant),
                joinedload(CertificationORM.cycle),
            )
            .filter(CertificationORM.id == cert_id)
            .first()
        )
        if not cert:
            raise LookupError(f"Certification {cert_id} introuvable")
        return cert

    def verifier(self, hash_value: str) -> Optional[CertificationORM]:
        return (
            self.db.query(CertificationORM)
            .options(
                joinedload(CertificationORM.participant),
                joinedload(CertificationORM.cycle),
            )
            .filter(CertificationORM.hash_verification == hash_value)
            .first()
        )

    def _generate_numero(self) -> str:
        annee = datetime.utcnow().year
        count = self.db.query(CertificationORM).count() + 1
        return f"CNI-{annee}-{str(count).zfill(6)}"

    def _generate_hash(self, insc: InscriptionORM, cycle: CycleORM) -> str:
        date_emission = datetime.utcnow().isoformat()
        data = f"{insc.participant_id}:{insc.cycle_id}:{date_emission}:{settings.secret_key}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
