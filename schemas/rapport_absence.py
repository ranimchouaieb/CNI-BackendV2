from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime


class ParticipantAbsentItem(BaseModel):
    participant_id: int
    nom: str
    jours: List[int] = Field(..., description="Jours d'absence [1,2,3,4,5]")


class RapportAbsenceCreate(BaseModel):
    cycle_id: int = Field(..., gt=0)
    date_rapport: Optional[date] = None
    contenu: Optional[str] = None
    participants_absents: List[ParticipantAbsentItem] = []


class RapportAbsenceUpdate(BaseModel):
    contenu: Optional[str] = None
    participants_absents: Optional[List[ParticipantAbsentItem]] = None
    statut: Optional[str] = Field(None, pattern="^(brouillon|soumis)$")


class CycleMinimalRapport(BaseModel):
    id: int
    theme_formation: str
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None

    model_config = {"from_attributes": True}


class FormateurMinimalRapport(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str

    model_config = {"from_attributes": True}


class RapportAbsenceResponse(BaseModel):
    id: int
    cycle_id: int
    formateur_id: int
    date_rapport: Optional[date] = None
    contenu: Optional[str] = None
    participants_absents: Any = []
    statut: str
    created_at: Optional[datetime] = None
    cycle: Optional[CycleMinimalRapport] = None
    formateur: Optional[FormateurMinimalRapport] = None

    model_config = {"from_attributes": True}
