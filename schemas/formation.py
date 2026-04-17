from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class FormationCreate(BaseModel):
    titre: str
    domaine: Optional[str] = None
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    duree_jours: int = 5
    prix_base: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None


class FormationUpdate(BaseModel):
    titre: Optional[str] = None
    domaine: Optional[str] = None
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    duree_jours: Optional[int] = None
    prix_base: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None


class FormationResponse(BaseModel):
    id: int
    titre: str
    domaine: Optional[str] = None
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    duree_jours: int
    prix_base: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}
