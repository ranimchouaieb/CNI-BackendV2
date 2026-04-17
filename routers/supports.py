import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from schemas.support import SupportResponse
from services.support_service import SupportService
from deps import get_support_service, get_current_user, get_current_formateur
from models.user import UserORM

router = APIRouter()


@router.get("/cycle/{cycle_id}", response_model=list[SupportResponse])
def list_supports(
    cycle_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: SupportService = Depends(get_support_service),
):
    return svc.list_by_cycle(cycle_id, current_user.id, current_user.role)


@router.post("/cycle/{cycle_id}", response_model=SupportResponse, status_code=201)
def uploader_support(
    cycle_id: int,
    titre: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_formateur),
    svc: SupportService = Depends(get_support_service),
):
    return svc.uploader(cycle_id, current_user.id, titre, description, file)


@router.get("/{support_id}/telecharger")
def telecharger_support(
    support_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: SupportService = Depends(get_support_service),
):
    try:
        path = svc.get_fichier_path(support_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(path, filename=os.path.basename(path))


@router.get("/{support_id}/download")
def download_support(
    support_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: SupportService = Depends(get_support_service),
):
    """Alias pour /telecharger — compatibilité frontend."""
    try:
        path = svc.get_fichier_path(support_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(path, filename=os.path.basename(path))


@router.delete("/{support_id}", status_code=204)
def supprimer_support(
    support_id: int,
    current_user: UserORM = Depends(get_current_formateur),
    svc: SupportService = Depends(get_support_service),
):
    svc.supprimer(support_id, current_user.id)
