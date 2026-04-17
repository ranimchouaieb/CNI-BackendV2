from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class NotificationORM(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type        = Column(String(50), nullable=False)
    titre       = Column(String(200), nullable=False)
    contenu     = Column(Text)
    lien_action = Column(String(255), nullable=True)
    lu          = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserORM", back_populates="notifications")
