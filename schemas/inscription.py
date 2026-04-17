from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date


class InscriptionCreate(BaseModel):
    cycle_id: int
    numero_cin: Optional[str] = None
    direction_service: Optional[str] = None
    entreprise_participant: Optional[str] = None


class InscriptionValider(BaseModel):
    motif: Optional[str] = None


class InscriptionRejeter(BaseModel):
    motif: str


class EmargementUpdate(BaseModel):
    emargement_jour_1: Optional[bool] = None
    emargement_jour_2: Optional[bool] = None
    emargement_jour_3: Optional[bool] = None
    emargement_jour_4: Optional[bool] = None
    emargement_jour_5: Optional[bool] = None


class EvaluationCreate(BaseModel):
    note_evaluation: int
    commentaire: Optional[str] = None

    @field_validator("note_evaluation")
    @classmethod
    def valider_note(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("La note doit être entre 1 et 5")
        return v


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
    statut: Optional[str] = None
    nb_inscrits: Optional[int] = 0
    capacite_max: Optional[int] = 0

    model_config = {"from_attributes": True}


class InscriptionResponse(BaseModel):
    id: int
    cycle_id: int
    participant_id: int
    numero_cin: Optional[str] = None
    direction_service: Optional[str] = None
    entreprise_participant: Optional[str] = None
    statut: str = "en_attente_validation"
    preuve_paiement_path: Optional[str] = None
    preuve_paiement_uploaded_at: Optional[datetime] = None
    validation_motif: Optional[str] = None
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    emargement_jour_1: Optional[bool] = False
    emargement_jour_2: Optional[bool] = False
    emargement_jour_3: Optional[bool] = False
    emargement_jour_4: Optional[bool] = False
    emargement_jour_5: Optional[bool] = False
    note_evaluation: Optional[int] = None
    commentaire: Optional[str] = None
    date_inscription: Optional[datetime] = None
    created_at: Optional[datetime] = None
    participant: Optional[ParticipantMinimal] = None
    cycle: Optional[CycleMinimal] = None

    model_config = {"from_attributes": True}


class InscriptionFormateurResponse(BaseModel):
    id: int
    cycle_id: int
    participant_id: int
    statut: str = "en_attente_validation"
    emargement_jour_1: Optional[bool] = False
    emargement_jour_2: Optional[bool] = False
    emargement_jour_3: Optional[bool] = False
    emargement_jour_4: Optional[bool] = False
    emargement_jour_5: Optional[bool] = False
    note_evaluation: Optional[int] = None
    participant: Optional[ParticipantMinimal] = None
    cycle: Optional[CycleMinimal] = None

    model_config = {"from_attributes": True}
