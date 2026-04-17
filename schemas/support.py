from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SupportResponse(BaseModel):
    id: int
    cycle_id: int
    formateur_id: int
    titre: str
    description: Optional[str] = None
    fichier_path: str
    fichier_type: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
