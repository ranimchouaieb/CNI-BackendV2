from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from schemas.dashboard import DashboardStats, StatsMensuel, FormationPopulaire, AgendaResponse
from services.dashboard_service import DashboardService
from deps import get_dashboard_service, get_current_admin, get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    admin=Depends(get_current_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    return svc.get_stats()


@router.get("/analytics", response_model=List[StatsMensuel])
def get_analytics(
    admin=Depends(get_current_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    return svc.get_analytics()


@router.get("/formations-populaires", response_model=List[FormationPopulaire])
def get_formations_populaires(
    limit: int = Query(10, ge=1, le=50),
    admin=Depends(get_current_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    return svc.get_formations_populaires(limit=limit)


@router.get("/agenda", response_model=AgendaResponse)
def get_agenda(
    mois: int = Query(..., ge=1, le=12),
    annee: int = Query(..., ge=2000, le=2100),
    admin=Depends(get_current_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    return svc.get_agenda(mois, annee)


@router.get("/agenda/participant")
def get_agenda_participant(
    current_user=Depends(get_current_user),
    svc: DashboardService = Depends(get_dashboard_service),
):
    if not current_user.is_participant():
        raise HTTPException(status_code=403, detail="Réservé aux participants")
    return svc.get_agenda_participant(current_user.id)


@router.get("/", response_model=DashboardStats)
def get_dashboard(
    admin=Depends(get_current_admin),
    svc: DashboardService = Depends(get_dashboard_service),
):
    return svc.get_stats()
