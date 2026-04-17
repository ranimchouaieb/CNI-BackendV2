from datetime import date, datetime
from calendar import month_abbr

from sqlalchemy import func, extract, or_
from sqlalchemy.orm import Session, joinedload

from models.user import UserORM
from models.cycle import CycleORM
from models.inscription import InscriptionORM
from models.certification import CertificationORM
from models.formation import FormationORM
from models.profile import ProfileFormateurORM
from schemas.dashboard import (
    DashboardStats, StatsMensuel, FormationPopulaire,
    UsersStats, CyclesStats, InscriptionsStats, RevenusStats, TauxStats,
    AgendaResponse, AgendaCycle,
)


class DashboardService:

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> DashboardStats:
        today = date.today()
        now = datetime.utcnow()

        # Utilisateurs — COUNT SQL direct
        total_participants   = self.db.query(func.count(UserORM.id)).filter(UserORM.role == "participant").scalar() or 0
        total_formateurs     = self.db.query(func.count(UserORM.id)).filter(UserORM.role == "formateur").scalar() or 0
        total_admins         = self.db.query(func.count(UserORM.id)).filter(UserORM.role == "admin").scalar() or 0
        total_formateurs_valides = self.db.query(func.count(ProfileFormateurORM.id)).filter(
            ProfileFormateurORM.statut_validation == "valide"
        ).scalar() or 0

        # Cycles — COUNT SQL avec filtres de date
        cycles_actifs   = self.db.query(func.count(CycleORM.id)).filter(
            CycleORM.is_cancelled == False, CycleORM.date_debut <= today, CycleORM.date_fin >= today
        ).scalar() or 0
        cycles_planifies = self.db.query(func.count(CycleORM.id)).filter(
            CycleORM.is_cancelled == False, CycleORM.date_debut > today
        ).scalar() or 0
        cycles_termines  = self.db.query(func.count(CycleORM.id)).filter(
            CycleORM.is_cancelled == False, CycleORM.date_fin < today
        ).scalar() or 0
        cycles_annules   = self.db.query(func.count(CycleORM.id)).filter(CycleORM.is_cancelled == True).scalar() or 0

        taux_remplissage_moyen = self.db.query(
            func.avg(CycleORM.nb_inscrits * 100.0 / func.nullif(CycleORM.capacite_max, 0))
        ).filter(CycleORM.is_cancelled == False).scalar() or 0.0

        # Revenus
        revenus_mois  = self._revenus_periode(now.year, now.month)
        revenus_annee = self._revenus_periode(now.year)

        # Satisfaction — AVG SQL
        satisfaction_moyenne = self.db.query(func.avg(InscriptionORM.note_evaluation)).filter(
            InscriptionORM.statut == "confirme",
            InscriptionORM.note_evaluation.isnot(None),
        ).scalar()
        satisfaction_moyenne = round(float(satisfaction_moyenne), 2) if satisfaction_moyenne else None

        # Taux complétion — COUNT SQL avec filtre OR sur les jours
        total_confirmes = self.db.query(func.count(InscriptionORM.id)).filter(
            InscriptionORM.statut == "confirme"
        ).scalar() or 0
        avec_presence = self.db.query(func.count(InscriptionORM.id)).filter(
            InscriptionORM.statut == "confirme",
            or_(
                InscriptionORM.emargement_jour_1 == True,
                InscriptionORM.emargement_jour_2 == True,
                InscriptionORM.emargement_jour_3 == True,
                InscriptionORM.emargement_jour_4 == True,
                InscriptionORM.emargement_jour_5 == True,
            )
        ).scalar() or 0
        taux_completion = round((avec_presence / total_confirmes * 100), 1) if total_confirmes > 0 else 0.0

        # Inscriptions
        inscriptions_en_attente  = self.db.query(func.count(InscriptionORM.id)).filter(InscriptionORM.statut == "en_attente_validation").scalar() or 0
        inscriptions_confirmees  = self.db.query(func.count(InscriptionORM.id)).filter(InscriptionORM.statut == "confirme").scalar() or 0
        attestations_emises      = self.db.query(func.count(CertificationORM.id)).scalar() or 0

        return DashboardStats(
            users=UsersStats(
                total=total_participants + total_formateurs + total_admins,
                participants=total_participants,
                formateurs=total_formateurs,
                formateurs_valides=total_formateurs_valides,
            ),
            cycles=CyclesStats(
                planifies=cycles_planifies,
                actifs=cycles_actifs,
                termines=cycles_termines,
                annules=cycles_annules,
                taux_remplissage_moyen=round(taux_remplissage_moyen, 1),
            ),
            inscriptions=InscriptionsStats(
                en_attente=inscriptions_en_attente,
                confirmees=inscriptions_confirmees,
            ),
            revenus=RevenusStats(
                mois_courant=round(revenus_mois, 2),
                annee_courante=round(revenus_annee, 2),
            ),
            taux=TauxStats(
                satisfaction_moyenne=satisfaction_moyenne,
                completion=taux_completion,
            ),
            certifications_emises=attestations_emises,
        )

    def get_analytics(self) -> list[StatsMensuel]:
        return self._stats_mensuelles_12_mois()

    def get_formations_populaires(self, limit: int = 10) -> list[FormationPopulaire]:
        return self._formations_populaires()[:limit]

    def get_agenda(self, mois: int, annee: int) -> AgendaResponse:
        debut = date(annee, mois, 1)
        fin   = date(annee + 1, 1, 1) if mois == 12 else date(annee, mois + 1, 1)
        cycles = (
            self.db.query(CycleORM)
            .filter(
                CycleORM.is_cancelled == False,
                CycleORM.date_debut < fin,
                CycleORM.date_fin >= debut,
            )
            .order_by(CycleORM.date_debut)
            .all()
        )
        result = [
            AgendaCycle(
                id=c.id,
                theme_formation=c.theme_formation,
                date_debut=str(c.date_debut),
                date_fin=str(c.date_fin),
                lieu=c.lieu,
                statut=c.statut,
                nb_inscrits=c.nb_inscrits,
                capacite_max=c.capacite_max,
                formateur=f"{c.formateurs[0].prenom} {c.formateurs[0].nom}" if c.formateurs else None,
            )
            for c in cycles
        ]
        return AgendaResponse(cycles=result, total_cycles=len(result))

    def get_agenda_participant(self, user_id: int) -> dict:
        today = date.today()
        debut_mois = today.replace(day=1)
        fin_mois   = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)

        inscriptions = (
            self.db.query(InscriptionORM)
            .join(CycleORM, InscriptionORM.cycle_id == CycleORM.id)
            .options(joinedload(InscriptionORM.cycle).joinedload(CycleORM.formateurs))
            .filter(
                InscriptionORM.participant_id == user_id,
                InscriptionORM.statut == "confirme",
                CycleORM.date_debut < fin_mois,
                CycleORM.date_fin >= debut_mois,
                CycleORM.is_cancelled == False,
            )
            .all()
        )
        return {
            "mois": today.strftime("%Y-%m"),
            "formations": [
                {
                    "inscription_id": i.id,
                    "cycle_id": i.cycle.id,
                    "theme_formation": i.cycle.theme_formation,
                    "date_debut": i.cycle.date_debut,
                    "date_fin": i.cycle.date_fin,
                    "lieu": i.cycle.lieu,
                    "horaire_debut": i.cycle.horaire_debut,
                    "horaire_fin": i.cycle.horaire_fin,
                    "formateur": ", ".join(f"{f.prenom} {f.nom}" for f in i.cycle.formateurs) if i.cycle.formateurs else None,
                    "statut": i.statut,
                }
                for i in inscriptions
            ],
        }

    def _revenus_periode(self, annee: int, mois: int = None) -> float:
        q = (
            self.db.query(func.sum(CycleORM.prix * CycleORM.nb_inscrits))
            .filter(
                CycleORM.is_cancelled == False,
                extract("year", CycleORM.date_debut) == annee,
            )
        )
        if mois:
            q = q.filter(extract("month", CycleORM.date_debut) == mois)
        result = q.scalar()
        return float(result) if result else 0.0

    def _stats_mensuelles_12_mois(self) -> list[StatsMensuel]:
        now = datetime.utcnow()
        stats = []
        for i in range(11, -1, -1):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)

            nb_participants = (
                self.db.query(func.count(InscriptionORM.id))
                .join(CycleORM)
                .filter(
                    InscriptionORM.statut == "confirme",
                    extract("year", CycleORM.date_debut) == y,
                    extract("month", CycleORM.date_debut) == m,
                )
                .scalar() or 0
            )
            revenus = self._revenus_periode(y, m)
            nb_cycles = (
                self.db.query(func.count(CycleORM.id))
                .filter(
                    CycleORM.is_cancelled == False,
                    extract("year", CycleORM.date_debut) == y,
                    extract("month", CycleORM.date_debut) == m,
                )
                .scalar() or 0
            )
            notes = (
                self.db.query(InscriptionORM.note_evaluation)
                .join(CycleORM)
                .filter(
                    InscriptionORM.statut == "confirme",
                    InscriptionORM.note_evaluation.isnot(None),
                    extract("year", CycleORM.date_debut) == y,
                    extract("month", CycleORM.date_debut) == m,
                )
                .all()
            )
            satisfaction = round(sum(n[0] for n in notes) / len(notes), 2) if notes else 0.0

            stats.append(StatsMensuel(
                mois=f"{month_abbr[m]} {y}",
                participants=nb_participants,
                revenus=round(revenus, 2),
                cycles=nb_cycles,
                satisfaction=satisfaction,
            ))

        return stats

    def _formations_populaires(self) -> list[FormationPopulaire]:
        formations = (
            self.db.query(FormationORM)
            .options(
                joinedload(FormationORM.cycles).joinedload(CycleORM.inscriptions)
            )
            .all()
        )
        result = []
        for f in formations:
            cycles_actifs = [c for c in f.cycles if not c.is_cancelled]
            if not cycles_actifs:
                continue
            nb_participants = sum(c.nb_inscrits for c in cycles_actifs)
            revenus = sum(float(c.prix or 0) * c.nb_inscrits for c in cycles_actifs)
            notes = [
                insc.note_evaluation
                for c in cycles_actifs
                for insc in c.inscriptions
                if insc.note_evaluation is not None
            ]
            result.append(FormationPopulaire(
                id=f.id,
                theme_formation=f.titre,
                nb_cycles=len(cycles_actifs),
                nb_participants=nb_participants,
                revenus=round(revenus, 2),
                satisfaction_moyenne=round(sum(notes) / len(notes), 2) if notes else None,
            ))

        result.sort(key=lambda x: x.nb_participants, reverse=True)
        return result
