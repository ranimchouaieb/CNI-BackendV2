from sqlalchemy import Table, Column, ForeignKey
from database import Base

cycle_formateurs = Table(
    "cycle_formateurs",
    Base.metadata,
    Column("cycle_id", ForeignKey("cycles.id", ondelete="CASCADE"), primary_key=True), #ondelete cascade pour supprimer les associations si un cycle ou un formateur est supprimé
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)
