import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from schemas.profile import (
    ProfileParticipantUpdate, ProfileParticipantResponse,
    ProfileFormateurUpdate, ProfileFormateurResponse,
    ValidateFormateurRequest,
)
from services.profile_service import ProfileService
from deps import get_profile_service, get_current_user, get_current_admin, get_current_formateur
from models.user import UserORM

router = APIRouter()


# ── Participant ───────────────────────────────────────────────────────────────

@router.get("/participant/me", response_model=ProfileParticipantResponse)
def get_mon_profil_participant(
    current_user: UserORM = Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.get_participant(current_user.id)


@router.post("/participant/me", response_model=ProfileParticipantResponse)
def creer_mon_profil_participant(
    current_user: UserORM = Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    """Crée (ou retourne si existant) le profil participant."""
    return svc.get_participant(current_user.id)


@router.put("/participant/me", response_model=ProfileParticipantResponse)
def modifier_mon_profil_participant(
    data: ProfileParticipantUpdate,
    current_user: UserORM = Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.modifier_participant(current_user.id, data)


@router.post("/participant/me/upload-cv", response_model=ProfileParticipantResponse)
def upload_cv_participant(
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.upload_cv_participant(current_user.id, file)


@router.get("/participant/me/cv")
def telecharger_cv_participant(
    current_user=Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    if not current_user.is_participant():
        raise HTTPException(status_code=403, detail="Réservé aux participants")
    profile = svc.get_participant(current_user.id)
    if not profile.cv_path or not os.path.exists(profile.cv_path):
        raise HTTPException(status_code=404, detail="Aucun CV uploadé")
    ext = os.path.splitext(profile.cv_path)[1]
    return FileResponse(
        profile.cv_path,
        media_type="application/octet-stream",
        filename=f"CV_{current_user.prenom}_{current_user.nom}{ext}",
    )


@router.get("/participant/me/progression")
def get_progression_participant(
    current_user: UserORM = Depends(get_current_user),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.get_progression(current_user.id)


# ── Formateur ─────────────────────────────────────────────────────────────────

@router.get("/formateur/me", response_model=ProfileFormateurResponse)
def get_mon_profil_formateur(
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.get_formateur(current_user.id)


@router.post("/formateur/me", response_model=ProfileFormateurResponse)
def creer_mon_profil_formateur(
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    """Crée (ou retourne si existant) le profil formateur."""
    return svc.get_formateur(current_user.id)


@router.put("/formateur/me", response_model=ProfileFormateurResponse)
def modifier_mon_profil_formateur(
    data: ProfileFormateurUpdate,
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.modifier_formateur(current_user.id, data)


@router.get("/formateur/me/stats")
def get_stats_formateur(
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.get_formateur_stats(current_user.id)


@router.post("/formateur/me/cv", response_model=ProfileFormateurResponse)
def upload_mon_cv(
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.upload_cv_formateur(current_user.id, file)


@router.post("/formateur/me/upload-cv", response_model=ProfileFormateurResponse)
def upload_mon_cv_alias(
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.upload_cv_formateur(current_user.id, file)


@router.get("/formateur/me/cv")
def telecharger_mon_cv(
    current_user: UserORM = Depends(get_current_formateur),
    svc: ProfileService = Depends(get_profile_service),
):
    profile = svc.get_formateur(current_user.id)
    if not profile.cv_path:
        raise HTTPException(status_code=404, detail="Aucun CV uploadé")
    return FileResponse(profile.cv_path, filename=f"cv_{current_user.nom}.pdf")


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/formateurs", response_model=List[ProfileFormateurResponse])
def list_formateurs(
    statut: Optional[str] = None,
    admin=Depends(get_current_admin),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.list_formateurs(statut=statut)


@router.get("/formateur/{user_id}", response_model=ProfileFormateurResponse)
def get_profil_formateur(
    user_id: int,
    admin=Depends(get_current_admin),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.get_formateur(user_id)


@router.get("/formateur/{user_id}/cv")
def telecharger_cv_formateur(
    user_id: int,
    admin=Depends(get_current_admin),
    svc: ProfileService = Depends(get_profile_service),
):
    profile = svc.get_formateur(user_id)
    if not profile.cv_path:
        raise HTTPException(status_code=404, detail="Aucun CV uploadé")
    return FileResponse(profile.cv_path)


@router.put("/formateur/{user_id}/valider", response_model=ProfileFormateurResponse)
def valider_formateur(
    user_id: int,
    data: ValidateFormateurRequest,
    admin=Depends(get_current_admin),
    svc: ProfileService = Depends(get_profile_service),
):
    return svc.valider_formateur(user_id, data)
