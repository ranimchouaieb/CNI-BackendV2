from typing import List

from fastapi import APIRouter, Depends, HTTPException

from schemas.rapport_absence import RapportAbsenceCreate, RapportAbsenceUpdate, RapportAbsenceResponse
from services.rapport_absence_service import RapportAbsenceService
from deps import get_current_user, get_current_admin, get_rapport_absence_service

router = APIRouter()


@router.post("/", response_model=RapportAbsenceResponse, status_code=201)
def creer_rapport(
    data: RapportAbsenceCreate,
    current_user=Depends(get_current_user),
    svc: RapportAbsenceService = Depends(get_rapport_absence_service),
):
    if not current_user.is_formateur():
        raise HTTPException(status_code=403, detail="Réservé aux formateurs")
    return svc.creer(current_user.id, data)


@router.put("/{rapport_id}", response_model=RapportAbsenceResponse)
def modifier_rapport(
    rapport_id: int,
    data: RapportAbsenceUpdate,
    current_user=Depends(get_current_user),
    svc: RapportAbsenceService = Depends(get_rapport_absence_service),
):
    if not (current_user.is_formateur() or current_user.is_admin()):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return svc.modifier(rapport_id, current_user.id, data, is_admin=current_user.is_admin())


@router.get("/mes-rapports", response_model=List[RapportAbsenceResponse])
def get_mes_rapports(
    current_user=Depends(get_current_user),
    svc: RapportAbsenceService = Depends(get_rapport_absence_service),
):
    if not current_user.is_formateur():
        raise HTTPException(status_code=403, detail="Réservé aux formateurs")
    return svc.list_by_formateur(current_user.id)


@router.get("/", response_model=List[RapportAbsenceResponse])
def get_all_rapports(
    admin=Depends(get_current_admin),
    svc: RapportAbsenceService = Depends(get_rapport_absence_service),
):
    return svc.list_all_soumis()


@router.get("/{rapport_id}", response_model=RapportAbsenceResponse)
def get_rapport(
    rapport_id: int,
    current_user=Depends(get_current_user),
    svc: RapportAbsenceService = Depends(get_rapport_absence_service),
):
    rapport = svc.get_by_id(rapport_id)
    if current_user.is_formateur() and rapport.formateur_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return rapport
