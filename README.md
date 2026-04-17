# CNI Smart Training Path — Backend v2

API REST pour la **Plateforme Intelligente de Gestion des Formations** du Centre National de l'Informatique (CNI).

Développée avec **FastAPI** + **PostgreSQL** + **SQLAlchemy**.
rq: les modules ia vont changer , priere de ne pas prendre la logique en compte 
---

## Fonctionnalités

- Authentification JWT + 2FA (TOTP / QR Code)(en cours de dev )
- Gestion des formations, cycles et inscriptions
- Gestion des utilisateurs et profils
- Messagerie interne et support
- Génération de certificats et PDF
- Rapports d'absence
- Module IA
- Upload de fichiers
- Dashboard statistiques

---

## Stack technique

| Technologie | Version |
|---|---|
| Python | 3.11 |
| FastAPI | 0.115 |
| SQLAlchemy | 2.0 |
| PostgreSQL | 14+ |
| Alembic | 1.14 |
| Uvicorn | 0.32 |

---

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/ton-username/ton-repo.git
cd ton-repo
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Modifier `.env` avec tes propres valeurs :

```env
DATABASE_URL=postgresql://user:password@localhost:5432/cni_formations_db
SECRET_KEY=une-cle-secrete-longue-et-aleatoire
```

### 5. Appliquer les migrations

```bash
alembic upgrade head
```

### 6. Lancer le serveur

```bash
uvicorn main:app --reload
```

L'API est disponible sur : `http://localhost:8000`

Documentation Swagger : `http://localhost:8000/docs`

---

## Structure du projet

```
BackendV2/
├── main.py              # Point d'entrée FastAPI
├── config.py            # Configuration (variables d'environnement)
├── database.py          # Connexion SQLAlchemy
├── deps.py              # Dépendances (auth, DB session)
├── models/              # Modèles SQLAlchemy
├── schemas/             # Schémas Pydantic (validation)
├── routers/             # Routes API
├── services/            # Logique métier
├── shared/              # Utilitaires partagés
├── alembic/             # Migrations de base de données
├── requirements.txt     # Dépendances Python
└── .env.example         # Modèle de configuration
```

---

## Endpoints principaux

| Méthode | Route | Description |
|---|---|---|
| POST | `/auth/login` | Connexion |
| GET | `/formations` | Liste des formations |
| GET | `/cycles` | Liste des cycles |
| POST | `/inscriptions` | Créer une inscription |
| GET | `/dashboard` | Statistiques |
| GET | `/health` | Statut de l'API |

Documentation complète : `http://localhost:8000/docs`

---

## Projet

Projet de Fin d'Études (PFE) — Plateforme intelligente de gestion des formations.
