from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models.associations import cycle_formateurs


class UserORM(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String(100), unique=True, nullable=False, index=True)
    password_hash    = Column(String(255), nullable=False)
    role             = Column(String(20), nullable=False, index=True)
    nom              = Column(String(100), nullable=False)
    prenom           = Column(String(100), nullable=False)
    numero_cin       = Column(String(20), unique=True)
    telephone        = Column(String(20))
    is_active        = Column(Boolean, default=True)
    #authentification a deux facteurs (2FA) avec TOTP (Time-based One-Time Password)
    totp_secret      = Column(String(32), nullable=True)
    totp_enabled     = Column(Boolean, default=False)
    totp_verified_at = Column(DateTime, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'formateur', 'participant')", name="check_role"),
    )

    cycles_formateur   = relationship("CycleORM", secondary=cycle_formateurs, back_populates="formateurs")
    inscriptions       = relationship("InscriptionORM", back_populates="participant", foreign_keys="InscriptionORM.participant_id")
    profile_participant = relationship("ProfileParticipantORM", back_populates="user", uselist=False)
    profile_formateur  = relationship("ProfileFormateurORM", back_populates="user", uselist=False)
    messages_envoyes   = relationship("MessageORM", back_populates="sender", foreign_keys="MessageORM.sender_id")
    messages_recus     = relationship("MessageORM", back_populates="receiver", foreign_keys="MessageORM.receiver_id")
    notifications      = relationship("NotificationORM", back_populates="user")
    certifications     = relationship("CertificationORM", back_populates="participant", foreign_keys="CertificationORM.participant_id")
    rapports_absence   = relationship("RapportAbsenceORM", back_populates="formateur")

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_formateur(self) -> bool:
        return self.role == "formateur"

    def is_participant(self) -> bool:
        return self.role == "participant"
