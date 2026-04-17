from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from database import Base


class ProfileParticipantORM(Base):
    __tablename__ = "profiles_participant"

    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    poste_actuel          = Column(String(100))
    domaine               = Column(String(100))
    annees_experience     = Column(Integer)
    competences_manuelles = Column(JSONB, default={})
    competences_ia        = Column(JSONB, default={})
    objectif_carriere     = Column(String(200))
    horizon_temporel      = Column(String(50))
    budget_disponible     = Column(String(50))
    cv_path               = Column(String(255))
    cv_uploaded_at        = Column(DateTime)
    parcours_ia_genere    = Column(JSONB)
    parcours_ia_date      = Column(DateTime)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("annees_experience >= 0", name="check_annees_exp"),
    )

    user = relationship("UserORM", back_populates="profile_participant")


class ProfileFormateurORM(Base):
    __tablename__ = "profiles_formateur"

    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cv_path               = Column(String(255))
    cv_uploaded_at        = Column(DateTime)
    competences_detectees = Column(JSONB, default={})
    annees_experience     = Column(Integer, default=0)
    statut_validation     = Column(String(20), default="en_attente")
    date_validation       = Column(DateTime)
    validation_commentaire = Column(Text)
    themes_compatibles    = Column(JSONB)
    note_moyenne          = Column(Numeric(3, 2), default=0)
    nb_evaluations        = Column(Integer, default=0)
    bio                   = Column(Text)
    specialites           = Column(String(200))
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "statut_validation IN ('en_attente', 'valide', 'rejete', 'suspendu')",
            name="check_statut_validation",
        ),
    )

    user = relationship("UserORM", back_populates="profile_formateur")
