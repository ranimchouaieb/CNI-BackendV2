"""
Service PDF — génère feuilles de présence et attestations CNI.
Utilise reportlab + qrcode.
"""
import io
import os
from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlalchemy.orm import Session, joinedload

from models.cycle import CycleORM
from models.inscription import InscriptionORM
from models.certification import CertificationORM
from config import settings


def _logo_path() -> str:
    return os.path.join("uploads", "logo_cni.png")


def _calc_heures(cycle: CycleORM) -> int:
    nb_jours = (cycle.date_fin - cycle.date_debut).days + 1
    h_debut = datetime.combine(cycle.date_debut, cycle.horaire_debut)
    h_fin = datetime.combine(cycle.date_debut, cycle.horaire_fin)
    return int(nb_jours * (h_fin - h_debut).seconds / 3600)


class PdfService:

    def __init__(self, db: Session):
        self.db = db
        self.logo = _logo_path()

    # ── Feuille de Présence ────────────────────────────────────────────────

    def feuille_presence(self, cycle_id: int) -> bytes:
        cycle = (
            self.db.query(CycleORM)
            .options(joinedload(CycleORM.formateurs), joinedload(CycleORM.inscriptions).joinedload(InscriptionORM.participant))
            .filter(CycleORM.id == cycle_id)
            .first()
        )
        if not cycle:
            raise LookupError(f"Cycle {cycle_id} introuvable")

        inscriptions = [
            i for i in cycle.inscriptions
            if i.statut == "confirme" and i.participant
        ]

        buf = io.BytesIO()
        pdf = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        self._header_presence(pdf, width, height, cycle)
        self._tableau_presence(pdf, width, height, inscriptions, cycle)
        self._footer_formateur(pdf, width, cycle)
        pdf.save()
        return buf.getvalue()

    def _header_presence(self, pdf, width, height, cycle: CycleORM):
        y = height - 2 * cm
        if os.path.exists(self.logo):
            pdf.drawImage(self.logo, 2 * cm, y - 1.5 * cm, width=3 * cm, height=1.5 * cm)

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(width / 2, y - 0.5 * cm, "Feuille De Présence")

        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(width - 2 * cm, y, "Réf : FORM.FINC.03")
        pdf.drawRightString(width - 2 * cm, y - 0.4 * cm, "Version : 02")
        pdf.drawRightString(width - 2 * cm, y - 0.8 * cm, f"Date : {datetime.now().strftime('%d/%m/%Y')}")

        y -= 2.5 * cm
        pdf.setFont("Helvetica", 10)
        pdf.drawString(2 * cm, y, "Entreprise: Centre National de l'Informatique")
        y -= 0.5 * cm
        pdf.drawString(2 * cm, y, f"N° Action : {cycle.numero_action or 'N/A'}")
        y -= 0.5 * cm
        pdf.drawString(2 * cm, y, f"Thème : {cycle.theme_formation}")
        pdf.drawString(12 * cm, y, f"Mode : {cycle.mode_formation}")
        y -= 0.5 * cm
        pdf.drawString(2 * cm, y, f"Lieu : {cycle.lieu}")
        pdf.drawString(12 * cm, y, f"Gouvernorat : {cycle.gouvernorat}")
        y -= 0.5 * cm
        pdf.drawString(2 * cm, y,
                       f"Période : du {cycle.date_debut.strftime('%d/%m/%Y')} au {cycle.date_fin.strftime('%d/%m/%Y')}")
        pdf.drawString(10 * cm, y,
                       f"Horaire : {cycle.horaire_debut.strftime('%H:%M')} à {cycle.horaire_fin.strftime('%H:%M')}")

    def _tableau_presence(self, pdf, width, height, inscriptions, cycle: CycleORM):
        y = height - 8 * cm
        nb_jours = min((cycle.date_fin - cycle.date_debut).days + 1, 5)

        col_x = [2 * cm, 3 * cm, 6 * cm, 8.5 * cm, 11 * cm]
        emarg_x = 13.5 * cm
        emarg_w = 1.2 * cm

        pdf.setFont("Helvetica-Bold", 8)
        for col, label in zip(col_x, ["N°", "Nom et Prénom", "N°CIN", "Direction/Service", "Entreprise"]):
            pdf.drawString(col, y, label)
        pdf.drawCentredString(emarg_x + nb_jours * emarg_w / 2, y + 0.3 * cm, "ÉMARGEMENT")

        y -= 0.5 * cm
        for i in range(nb_jours):
            d = cycle.date_debut + timedelta(days=i)
            pdf.setFont("Helvetica", 7)
            pdf.drawCentredString(emarg_x + i * emarg_w + 0.6 * cm, y, d.strftime('%d/%m'))

        y -= 0.7 * cm
        pdf.setFont("Helvetica", 9)
        for idx, insc in enumerate(inscriptions[:15], 1):
            p = insc.participant
            pdf.drawString(col_x[0], y, str(idx))
            pdf.drawString(col_x[1], y, f"{p.nom} {p.prenom}"[:22])
            pdf.drawString(col_x[2], y, (insc.numero_cin or "")[:12])
            pdf.drawString(col_x[3], y, (insc.direction_service or "")[:15])
            pdf.drawString(col_x[4], y, (insc.entreprise_participant or "")[:12])

            for i in range(nb_jours):
                rx = emarg_x + i * emarg_w
                present = getattr(insc, f"emargement_jour_{i+1}", False)
                if present:
                    pdf.setFillColorRGB(0.85, 1.0, 0.85)
                    pdf.rect(rx, y - 0.3 * cm, emarg_w, 0.7 * cm, fill=1, stroke=1)
                    pdf.setFillColorRGB(0, 0.55, 0)
                    pdf.setFont("Helvetica-Bold", 9)
                    pdf.drawCentredString(rx + emarg_w / 2, y - 0.05 * cm, "P")
                    pdf.setFillColorRGB(0, 0, 0)
                    pdf.setFont("Helvetica", 9)
                else:
                    pdf.rect(rx, y - 0.3 * cm, emarg_w, 0.7 * cm, fill=0, stroke=1)

            y -= 0.8 * cm
            if y < 6 * cm:
                break

    def _footer_formateur(self, pdf, width, cycle: CycleORM):
        y = 5 * cm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(2 * cm, y, "Nom et prénom du formateur :")
        if cycle.formateurs:
            f = cycle.formateurs[0]
            pdf.setFont("Helvetica", 10)
            pdf.drawString(2 * cm, y - 0.5 * cm, f"{f.prenom} {f.nom}")
        pdf.drawString(8 * cm, y, "Signature :")
        pdf.line(8 * cm, y - 1 * cm, 11 * cm, y - 1 * cm)
        pdf.drawString(13 * cm, y, "Cachet organisme :")

    # ── Attestation PDF (avec QR code) ────────────────────────────────────

    def attestation_pdf_for_cert(self, insc, cycle, cert) -> bytes:
        """Version sans requête DB — utilise les objets déjà chargés."""
        return self._render_certificat(insc.participant, cycle, cert)

    def attestation_pdf(self, inscription_id: int) -> bytes:
        insc = (
            self.db.query(InscriptionORM)
            .options(
                joinedload(InscriptionORM.participant),
                joinedload(InscriptionORM.cycle),
                joinedload(InscriptionORM.certification),
            )
            .filter(InscriptionORM.id == inscription_id)
            .first()
        )
        if not insc:
            raise LookupError(f"Inscription {inscription_id} introuvable")
        if not insc.certification:
            raise ValueError("Aucune attestation générée pour cette inscription")

        return self._render_certificat(insc.participant, insc.cycle, insc.certification)

    def _render_certificat(self, participant, cycle: CycleORM, cert: CertificationORM) -> bytes:
        import qrcode

        buf = io.BytesIO()
        pdf = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        # Bordure
        pdf.setStrokeColor(colors.HexColor("#1a3a6b"))
        pdf.setLineWidth(4)
        pdf.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)
        pdf.setLineWidth(1.5)
        pdf.rect(1.3 * cm, 1.3 * cm, width - 2.6 * cm, height - 2.6 * cm)

        y = height - 3.5 * cm
        if os.path.exists(self.logo):
            pdf.drawImage(self.logo, width / 2 - 2.5 * cm, y, width=5 * cm, height=2.5 * cm)

        y -= 2 * cm
        pdf.setFont("Helvetica-Bold", 26)
        pdf.setFillColor(colors.HexColor("#1a3a6b"))
        pdf.drawCentredString(width / 2, y, "ATTESTATION DE FORMATION")

        y -= 0.5 * cm
        pdf.setStrokeColor(colors.HexColor("#d4af37"))
        pdf.setLineWidth(2)
        pdf.line(3 * cm, y, width - 3 * cm, y)

        y -= 1.5 * cm
        pdf.setFont("Helvetica", 13)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, y, "Ce certificat est décerné à :")

        y -= 1 * cm
        pdf.setFont("Helvetica-Bold", 20)
        pdf.setFillColor(colors.HexColor("#1a3a6b"))
        pdf.drawCentredString(width / 2, y, f"{participant.prenom} {participant.nom}")

        if participant.numero_cin:
            y -= 0.6 * cm
            pdf.setFont("Helvetica", 11)
            pdf.setFillColor(colors.grey)
            pdf.drawCentredString(width / 2, y, f"CIN : {participant.numero_cin}")

        y -= 1.2 * cm
        pdf.setFont("Helvetica", 13)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, y, "Pour avoir suivi avec succès la formation :")

        y -= 0.9 * cm
        pdf.setFont("Helvetica-Bold", 15)
        pdf.setFillColor(colors.HexColor("#1a3a6b"))
        theme = cycle.theme_formation
        pdf.drawCentredString(width / 2, y, f"« {theme[:58]}... »" if len(theme) > 60 else f"« {theme} »")

        y -= 1 * cm
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(
            width / 2, y,
            f"Du {cycle.date_debut.strftime('%d/%m/%Y')} au {cycle.date_fin.strftime('%d/%m/%Y')}"
        )

        nb_heures = _calc_heures(cycle)
        y -= 0.6 * cm
        pdf.drawCentredString(width / 2, y, f"Durée : {nb_heures} heures")

        y -= 1 * cm
        pdf.setStrokeColor(colors.HexColor("#d4af37"))
        pdf.setLineWidth(1.5)
        pdf.line(3 * cm, y, width - 3 * cm, y)

        y -= 0.8 * cm
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(colors.HexColor("#1a3a6b"))
        pdf.drawCentredString(width / 2, y, f"N° {cert.numero_certification}")

        y -= 0.5 * cm
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.grey)
        pdf.drawCentredString(width / 2, y, f"Délivré le {cert.date_emission.strftime('%d/%m/%Y')}")

        # QR code
        verify_url = f"{settings.app_base_url}/certifications/verify/{cert.hash_verification}"
        qr = qrcode.QRCode(version=2, box_size=6, border=2)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        qr_x = width - 5 * cm
        qr_y = 2.5 * cm
        pdf.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=3.5 * cm, height=3.5 * cm)
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(colors.grey)
        pdf.drawCentredString(qr_x + 1.75 * cm, qr_y - 0.3 * cm, "Vérifier l'authenticité")

        # Signature
        sig_y = 4 * cm
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(colors.black)
        pdf.drawString(2.5 * cm, sig_y, "Le Directeur Général")
        pdf.line(2.5 * cm, sig_y - 1.5 * cm, 7 * cm, sig_y - 1.5 * cm)

        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(colors.lightgrey)
        pdf.drawCentredString(width / 2, 1.5 * cm,
                              f"Hash SHA256 : {cert.hash_verification[:32]}...")

        pdf.save()
        return buf.getvalue()
