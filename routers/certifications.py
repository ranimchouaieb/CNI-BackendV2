import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from schemas.certification import CertificationResponse, CertificationVerifyResponse
from services.certification_service import CertificationService
from services.pdf_service import PdfService
from deps import get_certification_service, get_current_admin, get_current_user, get_pdf_service
from models.user import UserORM

router = APIRouter()


@router.get("/", response_model=List[CertificationResponse])
def list_certifications(
    nom: Optional[str] = Query(None),
    cin: Optional[str] = Query(None),
    formation: Optional[str] = Query(None),
    date_emission: Optional[str] = Query(None),
    admin=Depends(get_current_admin),
    svc: CertificationService = Depends(get_certification_service),
):
    return svc.list_filtered(nom=nom, cin=cin, formation=formation, date_emission=date_emission)


@router.get("/mes-certifications", response_model=List[CertificationResponse])
def mes_certifications(
    current_user: UserORM = Depends(get_current_user),
    svc: CertificationService = Depends(get_certification_service),
):
    return svc.list_by_participant(current_user.id)


@router.post("/generer/{inscription_id}", response_model=CertificationResponse, status_code=201)
def generer_certification(
    inscription_id: int,
    admin=Depends(get_current_admin),
    svc: CertificationService = Depends(get_certification_service),
):
    return svc.generer(inscription_id)


@router.get("/{cert_id}/pdf")
def telecharger_pdf(
    cert_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: CertificationService = Depends(get_certification_service),
    pdf_svc: PdfService = Depends(get_pdf_service),
):
    try:
        cert = svc.get_by_id(cert_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if current_user.role == "participant" and cert.participant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    pdf_bytes = pdf_svc.attestation_pdf(cert.inscription_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Certificat_{cert.numero_certification}.pdf"},
    )


@router.post("/{cert_id}/regenerer-pdf", response_model=CertificationResponse)
def regenerer_pdf(
    cert_id: int,
    admin=Depends(get_current_admin),
    svc: CertificationService = Depends(get_certification_service),
    pdf_svc: PdfService = Depends(get_pdf_service),
):
    """Force la re-génération du PDF de l'attestation (utile si le PDF était manquant)."""
    try:
        cert = svc.get_by_id(cert_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Vérifie que le PDF peut être généré (lève ValueError si inscription sans cert)
    pdf_svc.attestation_pdf(cert.inscription_id)
    return cert


@router.get("/verify/{hash_value}", response_model=CertificationVerifyResponse)
def verifier_certification(
    hash_value: str,
    svc: CertificationService = Depends(get_certification_service),
):
    cert = svc.verifier(hash_value)
    if not cert:
        return CertificationVerifyResponse(
            valide=False,
            message="Attestation invalide ou introuvable",
        )
    return CertificationVerifyResponse(
        valide=True,
        numero_certification=cert.numero_certification,
        participant_nom=cert.participant.nom,
        participant_prenom=cert.participant.prenom,
        cycle_theme=cert.cycle.theme_formation,
        date_emission=cert.date_emission,
        message="Attestation authentique — Centre National de l'Informatique",
    )
