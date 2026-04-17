from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class ParticipantMinimal(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    numero_cin: Optional[str] = None

    model_config = {"from_attributes": True}


class CycleMinimal(BaseModel):
    id: int
    theme_formation: str
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    lieu: Optional[str] = None

    model_config = {"from_attributes": True}


class CertificationResponse(BaseModel):
    id: int
    inscription_id: int
    participant_id: int
    cycle_id: int
    numero_certification: str
    hash_verification: str
    date_emission: datetime
    pdf_path: Optional[str] = None
    participant: Optional[ParticipantMinimal] = None
    cycle: Optional[CycleMinimal] = None

    model_config = {"from_attributes": True}


class CertificationVerifyResponse(BaseModel):
    valide: bool
    numero_certification: Optional[str] = None
    participant_nom: Optional[str] = None
    participant_prenom: Optional[str] = None
    cycle_theme: Optional[str] = None
    date_emission: Optional[datetime] = None
    message: str
