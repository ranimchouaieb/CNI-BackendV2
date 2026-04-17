"""
Service IA — CV Matcher (admin) et Career Pathfinder (participant).
Utilise l'API Claude (Anthropic).
"""
import os
from typing import Optional

from sqlalchemy.orm import Session

from models.user import UserORM
from models.profile import ProfileFormateurORM, ProfileParticipantORM
from models.formation import FormationORM
from models.inscription import InscriptionORM
from models.cycle import CycleORM


class AiService:

    def __init__(self, db: Session):
        self.db = db

    def cv_matcher(self, formation_id: int) -> dict:
        """
        Trouve le meilleur formateur pour une formation donnée.
        Compare les CVs des formateurs validés au contenu de la formation.
        """
        formation = self.db.get(FormationORM, formation_id)
        if not formation:
            raise LookupError(f"Formation {formation_id} introuvable")

        formateurs_profiles = (
            self.db.query(ProfileFormateurORM)
            .filter(
                ProfileFormateurORM.statut_validation == "valide",
                ProfileFormateurORM.cv_path.isnot(None),
            )
            .all()
        )

        if not formateurs_profiles:
            raise ValueError("Aucun formateur validé avec CV disponible")

        formation_context = (
            f"Formation: {formation.titre}\n"
            f"Domaine: {formation.domaine or 'Non spécifié'}\n"
            f"Description: {formation.description or 'Non disponible'}\n"
            f"Objectifs: {formation.objectifs or 'Non spécifiés'}\n"
            f"Programme: {formation.programme or 'Non disponible'}"
        )

        formateurs_info = []
        for profile in formateurs_profiles:
            user = self.db.get(UserORM, profile.user_id)
            if not user:
                continue
            formateurs_info.append({
                "id": user.id,
                "nom": f"{user.prenom} {user.nom}",
                "specialites": profile.specialites or "",
                "bio": profile.bio or "",
                "competences": profile.competences_detectees or {},
                "note_moyenne": float(profile.note_moyenne or 0),
                "nb_evaluations": profile.nb_evaluations,
                "annees_experience": profile.annees_experience,
            })

        prompt = self._build_cv_matcher_prompt(formation_context, formateurs_info)
        response = self._call_claude(prompt)

        return {
            "formation": formation.titre,
            "analyse": response,
            "formateurs_disponibles": len(formateurs_info),
        }

    def career_pathfinder(self, participant_id: int) -> dict:
        """
        Génère un parcours de formations personnalisé pour le participant.
        """
        user = self.db.get(UserORM, participant_id)
        if not user:
            raise LookupError(f"Participant {participant_id} introuvable")

        profile = self.db.query(ProfileParticipantORM).filter(
            ProfileParticipantORM.user_id == participant_id
        ).first()

        formations_suivies = (
            self.db.query(FormationORM.titre)
            .join(CycleORM)
            .join(InscriptionORM)
            .filter(
                InscriptionORM.participant_id == participant_id,
                InscriptionORM.statut == "confirme",
            )
            .all()
        )

        catalogue = self.db.query(FormationORM).all()

        participant_context = (
            f"Nom: {user.prenom} {user.nom}\n"
            f"Poste actuel: {profile.poste_actuel if profile else 'Non renseigné'}\n"
            f"Domaine: {profile.domaine if profile else 'Non renseigné'}\n"
            f"Années d'expérience: {profile.annees_experience if profile else 0}\n"
            f"Objectif carrière: {profile.objectif_carriere if profile else 'Non renseigné'}\n"
            f"Horizon temporel: {profile.horizon_temporel if profile else 'Non renseigné'}\n"
            f"Budget disponible: {profile.budget_disponible if profile else 'Non renseigné'}\n"
            f"Formations déjà suivies: {', '.join([f[0] for f in formations_suivies]) or 'Aucune'}"
        )

        catalogue_context = "\n".join([
            f"- {f.titre} ({f.domaine or 'Général'}): {(f.description or '')[:100]}"
            for f in catalogue[:20]
        ])

        prompt = self._build_pathfinder_prompt(participant_context, catalogue_context)
        response = self._call_claude(prompt)

        if profile:
            import json
            from datetime import datetime
            profile.parcours_ia_genere = {"parcours": response}
            profile.parcours_ia_date = datetime.utcnow()
            self.db.commit()

        return {
            "participant": f"{user.prenom} {user.nom}",
            "parcours": response,
        }

    def _build_cv_matcher_prompt(self, formation: str, formateurs: list) -> str:
        formateurs_text = "\n".join([
            f"Formateur {i+1}: {f['nom']}\n"
            f"  Spécialités: {f['specialites']}\n"
            f"  Bio: {f['bio'][:200] if f['bio'] else 'Non disponible'}\n"
            f"  Expérience: {f['annees_experience']} ans\n"
            f"  Note moyenne: {f['note_moyenne']:.1f}/5 ({f['nb_evaluations']} évaluations)"
            for i, f in enumerate(formateurs)
        ])

        return (
            f"Tu es un expert en ressources humaines pour le Centre National de l'Informatique (CNI) en Tunisie.\n\n"
            f"FORMATION À POURVOIR:\n{formation}\n\n"
            f"FORMATEURS DISPONIBLES:\n{formateurs_text}\n\n"
            f"Analyse les profils et recommande le formateur le plus adapté. "
            f"Explique pourquoi en 3-5 points clés. "
            f"Réponds en français, de manière structurée et professionnelle."
        )

    def _build_pathfinder_prompt(self, participant: str, catalogue: str) -> str:
        return (
            f"Tu es un conseiller en formation professionnelle pour le CNI (Centre National de l'Informatique) en Tunisie.\n\n"
            f"PROFIL DU PARTICIPANT:\n{participant}\n\n"
            f"CATALOGUE DES FORMATIONS DISPONIBLES:\n{catalogue}\n\n"
            f"Génère un parcours de formation personnalisé en 3 étapes pour ce participant. "
            f"Pour chaque étape: nomme la formation recommandée, explique pourquoi elle est adaptée, "
            f"et précise l'impact attendu sur sa carrière. "
            f"Termine par un conseil général. "
            f"Réponds en français, de manière claire et motivante."
        )

    def _call_claude(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            raise ValueError(f"Erreur API Claude : {str(e)}")
