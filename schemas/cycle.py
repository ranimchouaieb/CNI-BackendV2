from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import date, time, datetime


class FormateurMinimal(BaseModel):
    id: int
    nom: str
    prenom: str

    model_config = {"from_attributes": True}


class FormationMinimal(BaseModel):
    id: int
    titre: str

    model_config = {"from_attributes": True}


class CycleCreate(BaseModel):
    formation_id: Optional[int] = None
    numero_action: Optional[str] = None
    theme_formation: str
    mode_formation: str
    entreprise: str
    lieu: str
    gouvernorat: str
    date_debut: date
    date_fin: date
    horaire_debut: time
    horaire_fin: time
    pause_debut: Optional[time] = None
    pause_fin: Optional[time] = None
    capacite_max: int = 15
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    prix: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None
    formateur_ids: List[int] = []

    @field_validator("mode_formation")
    @classmethod
    def valider_mode(cls, v: str) -> str:
        if v not in ("Inter", "Intra"):
            raise ValueError("mode_formation doit être 'Inter' ou 'Intra'")
        return v

    @field_validator("capacite_max")
    @classmethod
    def valider_capacite(cls, v: int) -> int:
        if not (5 <= v <= 30):
            raise ValueError("La capacité doit être entre 5 et 30")
        return v


class CycleUpdate(BaseModel):
    formation_id: Optional[int] = None
    numero_action: Optional[str] = None
    theme_formation: Optional[str] = None
    mode_formation: Optional[str] = None
    entreprise: Optional[str] = None
    lieu: Optional[str] = None
    gouvernorat: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    horaire_debut: Optional[time] = None
    horaire_fin: Optional[time] = None
    pause_debut: Optional[time] = None
    pause_fin: Optional[time] = None
    capacite_max: Optional[int] = None
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    prix: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None
    formateur_ids: Optional[List[int]] = None
    is_cancelled: Optional[bool] = None


class CycleResponse(BaseModel):
    id: int
    formation_id: Optional[int] = None
    numero_action: Optional[str] = None
    theme_formation: str
    mode_formation: str
    entreprise: str
    lieu: str
    gouvernorat: str
    date_debut: date
    date_fin: date
    horaire_debut: time
    horaire_fin: time
    pause_debut: Optional[time] = None
    pause_fin: Optional[time] = None
    capacite_max: int = 15
    nb_inscrits: int = 0
    statut: Optional[str] = "orange"
    description: Optional[str] = None
    objectifs: Optional[str] = None
    programme: Optional[str] = None
    prix: Optional[Decimal] = None
    tva_pct: Optional[Decimal] = None
    is_cancelled: Optional[bool] = False
    formateurs: List[FormateurMinimal] = []
    formation: Optional[FormationMinimal] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
