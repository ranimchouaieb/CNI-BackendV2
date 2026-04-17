from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    receiver_id: int
    contenu: str
    inscription_id: Optional[int] = None


class SenderMinimal(BaseModel):
    id: int
    nom: str
    prenom: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    inscription_id: Optional[int] = None
    contenu: str
    lu: bool
    created_at: datetime
    sender: Optional[SenderMinimal] = None
    receiver: Optional[SenderMinimal] = None

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    titre: str
    contenu: Optional[str] = None
    lien_action: Optional[str] = None
    lu: bool
    created_at: datetime

    model_config = {"from_attributes": True}
