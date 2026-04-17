from pydantic import BaseModel
from typing import List, Optional


class StatsMensuel(BaseModel):
    mois: str
    participants: int
    revenus: float
    cycles: int
    satisfaction: float


class FormationPopulaire(BaseModel):
    id: int
    theme_formation: str
    nb_cycles: int
    nb_participants: int
    revenus: float
    satisfaction_moyenne: Optional[float] = None


class UsersStats(BaseModel):
    total: int
    participants: int
    formateurs: int
    formateurs_valides: int


class CyclesStats(BaseModel):
    planifies: int
    actifs: int
    termines: int
    annules: int
    taux_remplissage_moyen: float


class InscriptionsStats(BaseModel):
    en_attente: int
    confirmees: int


class RevenusStats(BaseModel):
    mois_courant: float
    annee_courante: float


class TauxStats(BaseModel):
    satisfaction_moyenne: Optional[float] = None
    completion: float


class DashboardStats(BaseModel):
    users: UsersStats
    cycles: CyclesStats
    inscriptions: InscriptionsStats
    revenus: RevenusStats
    taux: TauxStats
    certifications_emises: int


class AgendaCycle(BaseModel):
    id: int
    theme_formation: str
    date_debut: str
    date_fin: str
    lieu: str
    statut: str
    nb_inscrits: int
    capacite_max: int
    formateur: Optional[str] = None


class AgendaResponse(BaseModel):
    cycles: List[AgendaCycle]
    total_cycles: int
