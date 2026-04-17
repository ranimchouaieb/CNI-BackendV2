from sqlalchemy import Column, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class MessageORM(Base):
    __tablename__ = "messages"

    id            = Column(Integer, primary_key=True, index=True)
    sender_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    inscription_id = Column(Integer, ForeignKey("inscriptions.id", ondelete="SET NULL"), nullable=True)
    contenu       = Column(Text, nullable=False)
    lu            = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender     = relationship("UserORM", back_populates="messages_envoyes", foreign_keys=[sender_id])
    receiver   = relationship("UserORM", back_populates="messages_recus", foreign_keys=[receiver_id])
    inscription = relationship("InscriptionORM", back_populates="messages")
