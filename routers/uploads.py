"""
Router Uploads — Programme détaillé d'un cycle (upload/download).
"""
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from services.cycle_service import CycleService
from deps import get_cycle_service, get_current_user

router = APIRouter()


@router.post("/cycles/{cycle_id}/programme")
async def upload_programme_cycle(
    cycle_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    svc: CycleService = Depends(get_cycle_service),
):
    """Upload programme détaillé d'un cycle (PDF, DOC, DOCX). Admin ou formateur du cycle."""
    try:
        return svc.upload_programme(cycle_id, current_user.id, current_user.role, file)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cycles/{cycle_id}/programme")
def download_programme_cycle(
    cycle_id: int,
    svc: CycleService = Depends(get_cycle_service),
):
    """Télécharge le programme d'un cycle (accès public)."""
    try:
        path = svc.get_programme_path(cycle_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=os.path.basename(path),
    )
