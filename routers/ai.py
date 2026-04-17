from fastapi import APIRouter, Depends, HTTPException

from services.ai_service import AiService
from deps import get_ai_service, get_current_admin, get_current_user
from models.user import UserORM

router = APIRouter()


@router.post("/cv-matcher")
def cv_matcher(
    formation_id: int,
    admin=Depends(get_current_admin),
    svc: AiService = Depends(get_ai_service),
):
    return svc.cv_matcher(formation_id)


@router.post("/career-pathfinder")
def career_pathfinder(
    current_user: UserORM = Depends(get_current_user),
    svc: AiService = Depends(get_ai_service),
):
    if not current_user.is_participant():
        raise HTTPException(status_code=403, detail="Réservé aux participants")
    return svc.career_pathfinder(current_user.id)
