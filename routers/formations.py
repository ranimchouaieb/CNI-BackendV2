from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from schemas.formation import FormationCreate, FormationUpdate, FormationResponse
from schemas.cycle import CycleResponse
from services.formation_service import FormationService
from services.cycle_service import CycleService
from deps import get_formation_service, get_cycle_service, get_current_admin

router = APIRouter()


@router.get("/meta/domaines")
def get_domaines(svc: FormationService = Depends(get_formation_service)):
    """Retourne la liste distincte des domaines de formation."""
    return svc.get_domaines()


@router.get("/check-duplicate")
def check_duplicate(
    titre: str = Query(...),
    exclude_id: Optional[int] = Query(None),
    svc: FormationService = Depends(get_formation_service),
):
    return svc.check_duplicate(titre, exclude_id)


@router.get("/", response_model=List[FormationResponse])
def list_formations(
    search: Optional[str] = Query(None),
    domaine: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=500),
    svc: FormationService = Depends(get_formation_service),
):
    return svc.list_all(search=search, domaine=domaine, limit=limit)


@router.get("/{formation_id}/cycles", response_model=List[CycleResponse])
def get_cycles_formation(
    formation_id: int,
    svc_f: FormationService = Depends(get_formation_service),
    svc_c: CycleService = Depends(get_cycle_service),
):
    svc_f.get_by_id(formation_id)  # 404 si inexistant
    return svc_c.list_by_formation(formation_id)


@router.get("/{formation_id}", response_model=FormationResponse)
def get_formation(formation_id: int, svc: FormationService = Depends(get_formation_service)):
    return svc.get_by_id(formation_id)


@router.post("/", response_model=FormationResponse, status_code=201)
def creer_formation(
    data: FormationCreate,
    admin=Depends(get_current_admin),
    svc: FormationService = Depends(get_formation_service),
):
    return svc.creer(data)


@router.put("/{formation_id}", response_model=FormationResponse)
def modifier_formation(
    formation_id: int,
    data: FormationUpdate,
    admin=Depends(get_current_admin),
    svc: FormationService = Depends(get_formation_service),
):
    return svc.modifier(formation_id, data)


@router.delete("/{formation_id}", status_code=204)
def supprimer_formation(
    formation_id: int,
    admin=Depends(get_current_admin),
    svc: FormationService = Depends(get_formation_service),
):
    svc.supprimer(formation_id)
