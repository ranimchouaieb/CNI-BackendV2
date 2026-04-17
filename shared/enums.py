from enum import Enum


class StatutInscription(str, Enum):
    EN_ATTENTE = "en_attente_validation"
    CONFIRME   = "confirme"
    REJETE     = "rejete"


class StatutCycle(str, Enum):
    VERT    = "vert"
    ORANGE  = "orange"
    ROUGE   = "rouge"
    TERMINE = "termine"


class Role(str, Enum):
    ADMIN       = "admin"
    FORMATEUR   = "formateur"
    PARTICIPANT = "participant"


class StatutFormateur(str, Enum):
    EN_ATTENTE = "en_attente"
    VALIDE     = "valide"
    REJETE     = "rejete"
