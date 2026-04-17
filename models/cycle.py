from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time,
    Text, Numeric, ForeignKey, CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models.associations import cycle_formateurs


class CycleORM(Base):
    __tablename__ = "cycles"

    id             = Column(Integer, primary_key=True, index=True)
    formation_id   = Column(Integer, ForeignKey("formations.id", ondelete="SET NULL"), nullable=True, index=True)
    numero_action  = Column(String(50))
    theme_formation = Column(String(200), nullable=False, index=True)
    mode_formation = Column(String(20), nullable=False)
    entreprise     = Column(String(100), nullable=False, index=True)
    lieu           = Column(String(100), nullable=False)
    gouvernorat    = Column(String(50), nullable=False, index=True)
    date_debut     = Column(Date, nullable=False, index=True)
    date_fin       = Column(Date, nullable=False)
    horaire_debut  = Column(Time, nullable=False)
    horaire_fin    = Column(Time, nullable=False)
    pause_debut    = Column(Time)
    pause_fin      = Column(Time)
    capacite_max   = Column(Integer, default=15)
    nb_inscrits    = Column(Integer, default=0)
    statut         = Column(String(20), default="orange")
    description    = Column(Text)
    objectifs      = Column(Text)
    programme      = Column(Text)
    prix           = Column(Numeric(10, 2))
    tva_pct        = Column(Numeric(5, 2), nullable=True)
    is_cancelled   = Column(Boolean, default=False)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("date_fin >= date_debut", name="check_dates"),
        CheckConstraint("horaire_fin > horaire_debut", name="check_horaires"),
        CheckConstraint("nb_inscrits <= capacite_max", name="check_capacite"),
        CheckConstraint("capacite_max >= 5 AND capacite_max <= 30", name="check_capacite_range"),
        CheckConstraint("statut IN ('vert', 'orange', 'rouge', 'termine')", name="check_statut"),
        CheckConstraint("mode_formation IN ('Inter', 'Intra')", name="check_mode"),
    )

    formation    = relationship("FormationORM", back_populates="cycles")
    formateurs   = relationship("UserORM", secondary=cycle_formateurs, back_populates="cycles_formateur")
    inscriptions = relationship("InscriptionORM", back_populates="cycle", cascade="all, delete-orphan")
    certifications = relationship("CertificationORM", back_populates="cycle")
    supports     = relationship("SupportCoursORM", back_populates="cycle", cascade="all, delete-orphan")
    rapports_absence = relationship("RapportAbsenceORM", back_populates="cycle", cascade="all, delete-orphan")
