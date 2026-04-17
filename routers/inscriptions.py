from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from schemas.inscription import (
    InscriptionCreate, InscriptionResponse, InscriptionFormateurResponse,
    InscriptionValider, InscriptionRejeter, EmargementUpdate, EvaluationCreate,
)
from services.inscription_service import InscriptionService
from deps import get_inscription_service, get_current_user, get_current_admin, get_current_formateur
from models.user import UserORM

router = APIRouter()


class DecisionRequest(BaseModel):
    decision: str  # 'valider' ou 'rejete'
    motif: Optional[str] = None


class InscriptionUpdate(BaseModel):
    note_evaluation: Optional[int] = None
    commentaire: Optional[str] = None
    emargement_jour_1: Optional[bool] = None
    emargement_jour_2: Optional[bool] = None
    emargement_jour_3: Optional[bool] = None
    emargement_jour_4: Optional[bool] = None
    emargement_jour_5: Optional[bool] = None


@router.get("/", response_model=List[InscriptionResponse])
def list_inscriptions(
    page_size: int = Query(100, ge=1, le=500),
    nom: Optional[str] = Query(None),
    cin: Optional[str] = Query(None),
    formation: Optional[str] = Query(None),
    date_debut: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.list_filtered(
        user_id=current_user.id,
        role=current_user.role,
        nom=nom,
        cin=cin,
        formation=formation,
        date_debut=date_debut,
        statut=statut,
        page_size=page_size,
    )


@router.get("/check-eligibility/{cycle_id}")
def check_eligibility(
    cycle_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    """Vérifie si le participant connecté est éligible à s'inscrire au cycle."""
    if not current_user.is_participant():
        raise HTTPException(status_code=403, detail="Réservé aux participants")
    return svc.check_eligibility(cycle_id, current_user.id)


@router.post("/", response_model=InscriptionResponse, status_code=201)
def creer_inscription(
    data: InscriptionCreate,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.creer(participant_id=current_user.id, data=data)


@router.get("/mes-inscriptions", response_model=List[InscriptionResponse])
def mes_inscriptions(
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.list_by_participant(current_user.id)


@router.get("/en-attente", response_model=List[InscriptionResponse])
def inscriptions_en_attente(
    admin=Depends(get_current_admin),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.list_en_attente()


@router.get("/cycle/{cycle_id}")
def inscriptions_by_cycle(
    cycle_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    inscriptions = svc.list_by_cycle(cycle_id)
    if current_user.is_formateur():
        return [InscriptionFormateurResponse.model_validate(i) for i in inscriptions]
    return [InscriptionResponse.model_validate(i) for i in inscriptions]


@router.post("/cycle/{cycle_id}/soumettre-emargement")
def soumettre_emargement_cycle(
    cycle_id: int,
    current_user: UserORM = Depends(get_current_formateur),
    svc: InscriptionService = Depends(get_inscription_service),
):
    try:
        result = svc.soumettre_emargement_notifie(
            cycle_id, current_user.id, current_user.prenom, current_user.nom
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {
        "message": result["message"],
        "cycle_id": result["cycle_id"],
        "inscriptions": [InscriptionFormateurResponse.model_validate(i) for i in result["inscriptions"]],
    }


@router.get("/{inscription_id}", response_model=InscriptionResponse)
def get_inscription(
    inscription_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.get_by_id(inscription_id)


@router.put("/{inscription_id}", response_model=InscriptionResponse)
def update_inscription(
    inscription_id: int,
    data: InscriptionUpdate,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.update(inscription_id, data.model_dump(exclude_unset=True))


@router.post("/{inscription_id}/valider", response_model=InscriptionResponse)
def valider_ou_rejeter(
    inscription_id: int,
    data: DecisionRequest,
    admin: UserORM = Depends(get_current_admin),
    svc: InscriptionService = Depends(get_inscription_service),
):
    if data.decision == "rejete":
        return svc.rejeter(inscription_id, admin.id, data.motif or "")
    return svc.valider(inscription_id, admin.id, data.motif)


@router.put("/{inscription_id}/valider", response_model=InscriptionResponse)
def valider_inscription(
    inscription_id: int,
    data: InscriptionValider,
    admin: UserORM = Depends(get_current_admin),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.valider(inscription_id, admin.id, data.motif)


@router.put("/{inscription_id}/rejeter", response_model=InscriptionResponse)
def rejeter_inscription(
    inscription_id: int,
    data: InscriptionRejeter,
    admin: UserORM = Depends(get_current_admin),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.rejeter(inscription_id, admin.id, data.motif)


@router.get("/{inscription_id}/preuve-paiement")
def get_preuve_paiement(
    inscription_id: int,
    admin=Depends(get_current_admin),
    svc: InscriptionService = Depends(get_inscription_service),
):
    insc = svc.get_by_id(inscription_id)
    if not insc.preuve_paiement_path:
        raise HTTPException(status_code=404, detail="Aucune preuve de paiement")
    return FileResponse(insc.preuve_paiement_path)


@router.post("/{inscription_id}/preuve-paiement", response_model=InscriptionResponse)
def upload_preuve_paiement(
    inscription_id: int,
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.upload_preuve_paiement(inscription_id, current_user.id, file)


@router.post("/{inscription_id}/upload-preuve", response_model=InscriptionResponse)
def upload_preuve(
    inscription_id: int,
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.upload_preuve_paiement(inscription_id, current_user.id, file)


@router.delete("/{inscription_id}", status_code=204)
def annuler_inscription(
    inscription_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    svc.annuler(inscription_id, current_user.id)


@router.put("/{inscription_id}/emargement", response_model=InscriptionResponse)
def mettre_a_jour_emargement(
    inscription_id: int,
    data: EmargementUpdate,
    current_user: UserORM = Depends(get_current_formateur),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.mettre_a_jour_emargement(inscription_id, data)


@router.post("/{inscription_id}/evaluation", response_model=InscriptionResponse)
def soumettre_evaluation(
    inscription_id: int,
    data: EvaluationCreate,
    current_user: UserORM = Depends(get_current_user),
    svc: InscriptionService = Depends(get_inscription_service),
):
    return svc.soumettre_evaluation(inscription_id, current_user.id, data)
