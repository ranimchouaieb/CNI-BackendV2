from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class FormationORM(Base):
    __tablename__ = "formations"

    id          = Column(Integer, primary_key=True, index=True)
    titre       = Column(String(200), nullable=False, index=True)
    domaine     = Column(String(100), index=True)
    description = Column(Text)
    objectifs   = Column(Text)
    programme   = Column(Text)
    duree_jours = Column(Integer, default=5)
    prix_base   = Column(Numeric(10, 2))
    tva_pct     = Column(Numeric(5, 2), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cycles = relationship("CycleORM", back_populates="formation")
