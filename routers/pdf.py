from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from services.pdf_service import PdfService
from deps import get_pdf_service, get_current_user
from models.user import UserORM

router = APIRouter()


@router.get("/feuille-presence/{cycle_id}")
def feuille_presence(
    cycle_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: PdfService = Depends(get_pdf_service),
):
    if not current_user.is_admin() and not current_user.is_formateur():
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    pdf_bytes = svc.feuille_presence(cycle_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=presence_cycle_{cycle_id}.pdf"},
    )


@router.get("/attestation/{inscription_id}")
def attestation_pdf(
    inscription_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: PdfService = Depends(get_pdf_service),
):
    pdf_bytes = svc.attestation_pdf(inscription_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=attestation_{inscription_id}.pdf"},
    )
