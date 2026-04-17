from typing import List

from fastapi import APIRouter, Depends, HTTPException

from schemas.message import MessageCreate, MessageResponse, NotificationResponse
from schemas.user import UserResponse
from services.message_service import MessageService
from services.user_service import UserService
from deps import get_message_service, get_user_service, get_current_user
from models.user import UserORM

router = APIRouter()


@router.get("/destinataires", response_model=List[UserResponse])
def get_destinataires(
    current_user: UserORM = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    return svc.get_destinataires(current_user)


@router.post("/", response_model=MessageResponse, status_code=201)
def envoyer_message(
    data: MessageCreate,
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.envoyer(current_user, data)


@router.get("/inbox", response_model=List[MessageResponse])
def inbox(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.get_inbox(current_user.id)


@router.get("/sent", response_model=List[MessageResponse])
def sent(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.get_sent(current_user.id)


@router.get("/unread-count")
def unread_count(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return {"count": svc.count_unread(current_user.id)}


@router.get("/conversation/{user_id}", response_model=List[MessageResponse])
def conversation(
    user_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.get_conversation(current_user.id, user_id)


@router.put("/{message_id}/lu", response_model=MessageResponse)
def marquer_lu(
    message_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.marquer_lu(message_id, current_user.id)


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications/", response_model=List[NotificationResponse])
def get_notifications(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return svc.get_notifications(current_user.id)


@router.get("/notifications/unread-count")
def notifs_unread_count(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    return {"count": svc.count_unread_notifications(current_user.id)}


@router.put("/notifications/{notif_id}/lu")
def marquer_notif_lue(
    notif_id: int,
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    try:
        svc.marquer_notif_lue(notif_id, current_user.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Notification marquée comme lue"}


@router.put("/notifications/tout-lire")
def marquer_toutes_lues(
    current_user: UserORM = Depends(get_current_user),
    svc: MessageService = Depends(get_message_service),
):
    svc.marquer_toutes_notifications_lues(current_user.id)
    return {"message": "Toutes les notifications marquées comme lues"}
