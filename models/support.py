from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class SupportCoursORM(Base):
    __tablename__ = "supports_cours"

    id           = Column(Integer, primary_key=True, index=True)
    cycle_id     = Column(Integer, ForeignKey("cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    formateur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    titre        = Column(String(200), nullable=False)
    description  = Column(Text)
    fichier_path = Column(String(500), nullable=False)
    fichier_type = Column(String(10))
    created_at   = Column(DateTime, default=datetime.utcnow)

    cycle     = relationship("CycleORM", back_populates="supports")
    formateur = relationship("UserORM", foreign_keys=[formateur_id])
