-- ============================================================
-- MIGRATION 002 — Mise à jour CNI Formations v2
-- Nouvelles colonnes + correction trigger nb_inscrits
-- psql -U <user> -d <database> -f 002_migration_update.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CORRECTION TRIGGER nb_inscrits
-- Le trigger original incrémentait à l'INSERT (en_attente_validation),
-- ce qui est incorrect. Le nb_inscrits doit s'incrémenter uniquement
-- quand l'admin confirme l'inscription (statut -> 'confirme').
-- On supprime le trigger et on gère tout en Python (inscriptions.py).
-- ============================================================

DROP TRIGGER IF EXISTS trg_nb_inscrits ON inscriptions;
DROP TRIGGER IF EXISTS trg_update_nb_inscrits ON inscriptions;
DROP FUNCTION IF EXISTS update_nb_inscrits() CASCADE;

-- Nouveau trigger: uniquement quand statut passe à 'confirme' ou quand annulé
CREATE OR REPLACE FUNCTION update_nb_inscrits_v2()
RETURNS TRIGGER AS $$
BEGIN
    -- confirme → annule/rejete : décrémenter
    IF OLD.statut = 'confirme' AND NEW.statut IN ('annule', 'rejete') THEN
        UPDATE cycles SET nb_inscrits = GREATEST(0, nb_inscrits - 1) WHERE id = NEW.cycle_id;

    -- annule/rejete → confirme : incrémenter (remise en état)
    ELSIF OLD.statut IN ('annule', 'rejete') AND NEW.statut = 'confirme' THEN
        UPDATE cycles SET nb_inscrits = nb_inscrits + 1 WHERE id = NEW.cycle_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_nb_inscrits_v2 ON inscriptions;
CREATE TRIGGER trg_nb_inscrits_v2
    AFTER UPDATE ON inscriptions
    FOR EACH ROW EXECUTE FUNCTION update_nb_inscrits_v2();

-- ============================================================
-- 2. TABLE certifications — ajouter numero_certification
-- ============================================================

ALTER TABLE certifications
    ADD COLUMN IF NOT EXISTS numero_certification VARCHAR(20);

-- Générer des numéros pour les certifications existantes
DO $$
DECLARE
    rec RECORD;
    counter INT := 1;
    current_year INT := EXTRACT(YEAR FROM NOW())::INT;
BEGIN
    FOR rec IN SELECT id FROM certifications WHERE numero_certification IS NULL ORDER BY id LOOP
        UPDATE certifications
        SET numero_certification = 'CNI-' || current_year || '-' || LPAD(counter::TEXT, 6, '0')
        WHERE id = rec.id;
        counter := counter + 1;
    END LOOP;
END;
$$;

-- Rendre la colonne obligatoire et unique
ALTER TABLE certifications
    ALTER COLUMN numero_certification SET NOT NULL;

-- Ajouter contrainte unique si pas déjà là
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'certifications_numero_certification_key'
    ) THEN
        ALTER TABLE certifications ADD CONSTRAINT certifications_numero_certification_key
            UNIQUE (numero_certification);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS ix_certifications_numero ON certifications(numero_certification);

-- ============================================================
-- 3. TABLE profiles_formateur — ajouter note_moyenne, nb_evaluations
--    + corriger annees_experience (JSONB → INTEGER)
-- ============================================================

-- Ajouter colonnes si absentes
ALTER TABLE profiles_formateur
    ADD COLUMN IF NOT EXISTS note_moyenne NUMERIC(3,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS nb_evaluations INTEGER DEFAULT 0;

-- Migration annees_experience JSONB → INTEGER (si la colonne existe en JSONB)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles_formateur'
          AND column_name = 'annees_experience'
          AND data_type = 'jsonb'
    ) THEN
        ALTER TABLE profiles_formateur DROP COLUMN annees_experience;
        ALTER TABLE profiles_formateur ADD COLUMN annees_experience INTEGER DEFAULT 0;
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles_formateur'
          AND column_name = 'annees_experience'
    ) THEN
        ALTER TABLE profiles_formateur ADD COLUMN annees_experience INTEGER DEFAULT 0;
    END IF;
END;
$$;

-- ============================================================
-- 4. TABLE profiles_participant — créer si inexistante
-- ============================================================

CREATE TABLE IF NOT EXISTS profiles_participant (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    poste_actuel VARCHAR(100),
    domaine VARCHAR(100),
    annees_experience INTEGER DEFAULT 0,
    competences_manuelles JSONB DEFAULT '{}',
    competences_ia JSONB DEFAULT '{}',
    objectif_carriere VARCHAR(200),
    horizon_temporel VARCHAR(50),
    budget_disponible VARCHAR(50),
    cv_path VARCHAR(255),
    cv_uploaded_at TIMESTAMP,
    parcours_ia_genere JSONB,
    parcours_ia_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_annees_exp CHECK (annees_experience >= 0)
);

CREATE INDEX IF NOT EXISTS ix_profiles_participant_user ON profiles_participant(user_id);

-- ============================================================
-- 5. TABLE profiles_formateur — créer si inexistante
-- ============================================================

CREATE TABLE IF NOT EXISTS profiles_formateur (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    cv_path VARCHAR(255),
    cv_uploaded_at TIMESTAMP,
    competences_detectees JSONB DEFAULT '{}',
    annees_experience INTEGER DEFAULT 0,
    statut_validation VARCHAR(20) DEFAULT 'en_attente',
    date_validation TIMESTAMP,
    validation_commentaire TEXT,
    themes_compatibles JSONB,
    bio TEXT,
    specialites VARCHAR(200),
    note_moyenne NUMERIC(3,2) DEFAULT 0,
    nb_evaluations INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_statut_validation CHECK (
        statut_validation IN ('en_attente', 'valide', 'rejete', 'suspendu')
    )
);

CREATE INDEX IF NOT EXISTS ix_profiles_formateur_user ON profiles_formateur(user_id);
CREATE INDEX IF NOT EXISTS ix_profiles_formateur_statut ON profiles_formateur(statut_validation);

-- ============================================================
-- 6. TABLE competences et cycle_competences — créer si inexistantes
-- ============================================================

CREATE TABLE IF NOT EXISTS competences (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    categorie VARCHAR(50),
    niveau_requis_defaut INTEGER DEFAULT 3,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cycle_competences (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    competence_id INTEGER NOT NULL REFERENCES competences(id) ON DELETE CASCADE,
    est_prerequis BOOLEAN DEFAULT FALSE,
    niveau_enseigne INTEGER,
    poids INTEGER DEFAULT 10,
    CONSTRAINT unique_cycle_competence UNIQUE (cycle_id, competence_id)
);

-- ============================================================
-- 7. TABLE recommandations — créer si inexistante
-- ============================================================

CREATE TABLE IF NOT EXISTS recommandations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    score INTEGER,
    raison TEXT,
    priorite INTEGER,
    est_dans_parcours BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_recommandations_user ON recommandations(user_id);

-- ============================================================
-- 8. TRIGGER updated_at pour profiles
-- ============================================================

DROP TRIGGER IF EXISTS trg_profiles_participant_updated_at ON profiles_participant;
CREATE TRIGGER trg_profiles_participant_updated_at
    BEFORE UPDATE ON profiles_participant
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_profiles_formateur_updated_at ON profiles_formateur;
CREATE TRIGGER trg_profiles_formateur_updated_at
    BEFORE UPDATE ON profiles_formateur
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 9. NOTIFICATIONS — ajouter type certification_revoquee si besoin
-- (pas de modification de structure nécessaire, juste doc)
-- Types valides: inscription_soumise | inscription_validee | inscription_rejetee |
--                preuve_paiement_soumise | nouveau_message | rapport_absence_soumis |
--                certification_emise | certification_revoquee | profil_valide |
--                profil_rejete | profil_suspendu
-- ============================================================

-- ============================================================
-- VÉRIFICATION
-- ============================================================
-- SELECT column_name, data_type FROM information_schema.columns
--   WHERE table_name = 'certifications' AND column_name = 'numero_certification';
-- SELECT column_name, data_type FROM information_schema.columns
--   WHERE table_name = 'profiles_formateur';
-- \d profiles_participant
-- \d profiles_formateur

COMMIT;
