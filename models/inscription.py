from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class InscriptionORM(Base):
    __tablename__ = "inscriptions"

    id                         = Column(Integer, primary_key=True, index=True)
    cycle_id                   = Column(Integer, ForeignKey("cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_cin                 = Column(String(20))
    direction_service          = Column(String(100))
    entreprise_participant     = Column(String(100))
    statut                     = Column(String(30), nullable=False, default="en_attente_validation")
    preuve_paiement_path       = Column(String(255))
    preuve_paiement_type       = Column(String(10))
    preuve_paiement_uploaded_at = Column(DateTime)
    validation_motif           = Column(Text)
    validated_by               = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    validated_at               = Column(DateTime)
    emargement_jour_1          = Column(Boolean, default=False)
    emargement_jour_2          = Column(Boolean, default=False)
    emargement_jour_3          = Column(Boolean, default=False)
    emargement_jour_4          = Column(Boolean, default=False)
    emargement_jour_5          = Column(Boolean, default=False)
    note_evaluation            = Column(Integer)
    commentaire                = Column(Text)
    date_inscription           = Column(DateTime, default=datetime.utcnow)
    created_at                 = Column(DateTime, default=datetime.utcnow)
    updated_at                 = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("cycle_id", "participant_id", name="unique_participant_cycle"),
        CheckConstraint(
            "statut IN ('en_attente_validation', 'confirme', 'rejete')",
            name="check_statut_inscription",
        ),
        CheckConstraint("note_evaluation >= 1 AND note_evaluation <= 5", name="check_note"),
    )

    cycle       = relationship("CycleORM", back_populates="inscriptions")
    participant = relationship("UserORM", back_populates="inscriptions", foreign_keys=[participant_id])
    validateur  = relationship("UserORM", foreign_keys=[validated_by])
    messages    = relationship("MessageORM", back_populates="inscription")
    certification = relationship("CertificationORM", back_populates="inscription", uselist=False)
