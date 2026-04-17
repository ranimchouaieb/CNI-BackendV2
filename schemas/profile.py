from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal


class ProfileParticipantUpdate(BaseModel):
    poste_actuel: Optional[str] = None
    domaine: Optional[str] = None
    annees_experience: Optional[int] = None
    competences_manuelles: Optional[Any] = None
    objectif_carriere: Optional[str] = None
    horizon_temporel: Optional[str] = None
    budget_disponible: Optional[str] = None


class ProfileParticipantResponse(BaseModel):
    id: int
    user_id: int
    poste_actuel: Optional[str] = None
    domaine: Optional[str] = None
    annees_experience: Optional[int] = None
    competences_manuelles: Optional[Any] = None
    competences_ia: Optional[Any] = None
    objectif_carriere: Optional[str] = None
    horizon_temporel: Optional[str] = None
    budget_disponible: Optional[str] = None
    cv_path: Optional[str] = None
    cv_uploaded_at: Optional[datetime] = None
    parcours_ia_genere: Optional[Any] = None
    parcours_ia_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileFormateurUpdate(BaseModel):
    bio: Optional[str] = None
    specialites: Optional[str] = None
    annees_experience: Optional[int] = None


class ProfileFormateurResponse(BaseModel):
    id: int
    user_id: int
    cv_path: Optional[str] = None
    cv_uploaded_at: Optional[datetime] = None
    competences_detectees: Optional[Any] = None
    annees_experience: int
    statut_validation: str
    date_validation: Optional[datetime] = None
    validation_commentaire: Optional[str] = None
    themes_compatibles: Optional[Any] = None
    note_moyenne: Optional[Decimal] = None
    nb_evaluations: int
    bio: Optional[str] = None
    specialites: Optional[str] = None

    model_config = {"from_attributes": True}


class ValidateFormateurRequest(BaseModel):
    statut: str
    commentaire: Optional[str] = None
