from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class CertificationORM(Base):
    __tablename__ = "certifications"

    id                   = Column(Integer, primary_key=True, index=True)
    inscription_id       = Column(Integer, ForeignKey("inscriptions.id", ondelete="RESTRICT"), unique=True, nullable=False)
    participant_id       = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    cycle_id             = Column(Integer, ForeignKey("cycles.id", ondelete="RESTRICT"), nullable=False)
    numero_certification = Column(String(20), unique=True, nullable=False, index=True)
    hash_verification    = Column(String(64), unique=True, nullable=False, index=True)
    date_emission        = Column(DateTime, default=datetime.utcnow, nullable=False)
    pdf_path             = Column(String(255))

    inscription = relationship("InscriptionORM", back_populates="certification")
    participant = relationship("UserORM", back_populates="certifications", foreign_keys=[participant_id])
    cycle       = relationship("CycleORM", back_populates="certifications")
