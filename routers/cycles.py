from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.cycle import CycleCreate, CycleUpdate, CycleResponse
from services.cycle_service import CycleService
from deps import get_cycle_service, get_current_admin, get_current_user, get_optional_user
from models.user import UserORM

router = APIRouter()


@router.get("/", response_model=List[CycleResponse])
def list_cycles(
    gouvernorat: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    page_size: Optional[int] = Query(None, ge=1, le=500),
    current_user: Optional[UserORM] = Depends(get_optional_user),
    svc: CycleService = Depends(get_cycle_service),
):
    include_cancelled = current_user is not None and current_user.is_admin()
    return svc.list_all(
        gouvernorat=gouvernorat,
        statut=statut,
        search=search,
        include_cancelled=include_cancelled,
        skip=skip,
        limit=page_size or limit,
    )


@router.get("/disponibles/inscription", response_model=List[CycleResponse])
def list_disponibles(svc: CycleService = Depends(get_cycle_service)):
    return svc.list_disponibles()


@router.get("/annules", response_model=List[CycleResponse])
def list_annules(svc: CycleService = Depends(get_cycle_service)):
    return svc.list_annules()


@router.get("/termines", response_model=List[CycleResponse])
def list_termines(svc: CycleService = Depends(get_cycle_service)):
    return svc.list_termines()


@router.get("/formateur/{formateur_id}", response_model=List[CycleResponse])
def list_by_formateur(
    formateur_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: CycleService = Depends(get_cycle_service),
):
    if not current_user.is_admin() and current_user.id != formateur_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return svc.list_by_formateur(formateur_id)


@router.get("/{cycle_id}", response_model=CycleResponse)
def get_cycle(cycle_id: int, svc: CycleService = Depends(get_cycle_service)):
    return svc.get_by_id(cycle_id)


@router.post("/", response_model=CycleResponse, status_code=201)
def creer_cycle(
    data: CycleCreate,
    admin=Depends(get_current_admin),
    svc: CycleService = Depends(get_cycle_service),
):
    return svc.creer(data)


@router.put("/{cycle_id}", response_model=CycleResponse)
def modifier_cycle(
    cycle_id: int,
    data: CycleUpdate,
    admin=Depends(get_current_admin),
    svc: CycleService = Depends(get_cycle_service),
):
    return svc.modifier(cycle_id, data)


@router.delete("/{cycle_id}", status_code=204)
def supprimer_cycle(
    cycle_id: int,
    admin=Depends(get_current_admin),
    svc: CycleService = Depends(get_cycle_service),
):
    svc.supprimer(cycle_id)
