from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from database import Base


class RapportAbsenceORM(Base):
    __tablename__ = "rapports_absence"

    id              = Column(Integer, primary_key=True, index=True)
    cycle_id        = Column(Integer, ForeignKey("cycles.id", ondelete="CASCADE"), nullable=False)
    formateur_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_rapport    = Column(Date, default=datetime.utcnow)
    contenu         = Column(Text)
    participants_absents = Column(JSONB, default=[])
    statut          = Column(String(20), default="brouillon")
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("statut IN ('brouillon', 'soumis', 'vu_admin')", name="check_statut_rapport"),
    )

    cycle     = relationship("CycleORM", back_populates="rapports_absence")
    formateur = relationship("UserORM", back_populates="rapports_absence")
