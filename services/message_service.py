from sqlalchemy.orm import Session, joinedload

from models.message import MessageORM
from models.notification import NotificationORM
from models.user import UserORM
from schemas.message import MessageCreate


class MessageService:

    def __init__(self, db: Session):
        self.db = db

    def envoyer(self, sender: UserORM, data: MessageCreate) -> MessageORM:
        receiver = self.db.get(UserORM, data.receiver_id)
        if not receiver:
            raise LookupError(f"Destinataire {data.receiver_id} introuvable")
        if not receiver.is_active:
            raise ValueError("Ce destinataire n'est plus actif")

        msg = MessageORM(
            sender_id=sender.id,
            receiver_id=data.receiver_id,
            inscription_id=data.inscription_id,
            contenu=data.contenu,
        )
        self.db.add(msg)
        self.db.flush()

        self.db.add(NotificationORM(
            user_id=data.receiver_id,
            type="nouveau_message",
            titre=f"Nouveau message de {sender.prenom} {sender.nom}",
            lien_action="/messages",
        ))

        self.db.commit()
        self.db.refresh(msg)
        return self._get_with_users(msg.id)

    def get_inbox(self, user_id: int) -> list[MessageORM]:
        return (
            self.db.query(MessageORM)
            .options(joinedload(MessageORM.sender))
            .filter(MessageORM.receiver_id == user_id)
            .order_by(MessageORM.created_at.desc())
            .all()
        )

    def get_sent(self, user_id: int) -> list[MessageORM]:
        return (
            self.db.query(MessageORM)
            .options(joinedload(MessageORM.receiver))
            .filter(MessageORM.sender_id == user_id)
            .order_by(MessageORM.created_at.desc())
            .all()
        )

    def get_conversation(self, user_id: int, other_id: int) -> list[MessageORM]:
        msgs = (
            self.db.query(MessageORM)
            .options(joinedload(MessageORM.sender), joinedload(MessageORM.receiver))
            .filter(
                ((MessageORM.sender_id == user_id) & (MessageORM.receiver_id == other_id)) |
                ((MessageORM.sender_id == other_id) & (MessageORM.receiver_id == user_id))
            )
            .order_by(MessageORM.created_at.asc())
            .all()
        )
        # Marquer lu
        self.db.query(MessageORM).filter(
            MessageORM.sender_id == other_id,
            MessageORM.receiver_id == user_id,
            MessageORM.lu == False,
        ).update({"lu": True})
        self.db.commit()
        return msgs

    def count_unread(self, user_id: int) -> int:
        return self.db.query(MessageORM).filter(
            MessageORM.receiver_id == user_id,
            MessageORM.lu == False,
        ).count()

    def marquer_lu(self, message_id: int, user_id: int) -> MessageORM:
        msg = self.db.query(MessageORM).filter(MessageORM.id == message_id).first()
        if not msg:
            raise LookupError(f"Message {message_id} introuvable")
        if msg.receiver_id != user_id:
            raise ValueError("Accès non autorisé")
        msg.lu = True
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_notifications(self, user_id: int, limit: int = 50) -> list[NotificationORM]:
        return (
            self.db.query(NotificationORM)
            .filter(NotificationORM.user_id == user_id)
            .order_by(NotificationORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_unread_notifications(self, user_id: int) -> int:
        return self.db.query(NotificationORM).filter(
            NotificationORM.user_id == user_id,
            NotificationORM.lu == False,
        ).count()

    def marquer_notif_lue(self, notif_id: int, user_id: int) -> None:
        notif = self.db.query(NotificationORM).filter(
            NotificationORM.id == notif_id,
            NotificationORM.user_id == user_id,
        ).first()
        if not notif:
            raise LookupError(f"Notification {notif_id} introuvable")
        notif.lu = True
        self.db.commit()

    def marquer_toutes_notifications_lues(self, user_id: int) -> None:
        self.db.query(NotificationORM).filter(
            NotificationORM.user_id == user_id,
            NotificationORM.lu == False,
        ).update({"lu": True})
        self.db.commit()

    def _get_with_users(self, message_id: int) -> MessageORM:
        return (
            self.db.query(MessageORM)
            .options(joinedload(MessageORM.sender), joinedload(MessageORM.receiver))
            .filter(MessageORM.id == message_id)
            .first()
        )
