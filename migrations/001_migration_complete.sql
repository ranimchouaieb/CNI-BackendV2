-- ============================================================
-- MIGRATION CNI COMPLÈTE - À appliquer avec psql :
-- psql -U <user> -d <database> -f 001_migration_complete.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. MODIFIER TABLE INSCRIPTIONS
-- ============================================================

-- Supprimer l'ancien check constraint statut
ALTER TABLE inscriptions DROP CONSTRAINT IF EXISTS check_statut_inscription;

-- Ajouter nouveau check avec tous les statuts
ALTER TABLE inscriptions ADD CONSTRAINT check_statut_inscription
    CHECK (statut IN (
        'en_attente_validation',
        'confirme',
        'inscrit',
        'present',
        'absent',
        'annule',
        'rejete'
    ));

-- Colonnes preuve de paiement
ALTER TABLE inscriptions
    ADD COLUMN IF NOT EXISTS preuve_paiement_path VARCHAR(255),
    ADD COLUMN IF NOT EXISTS preuve_paiement_type VARCHAR(10),
    ADD COLUMN IF NOT EXISTS preuve_paiement_uploaded_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS validation_motif TEXT,
    ADD COLUMN IF NOT EXISTS validated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP;

-- ============================================================
-- 2. MODIFIER TABLE USERS — 2FA TOTP
-- ============================================================

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32),
    ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS totp_verified_at TIMESTAMP;

-- ============================================================
-- 3. TABLE MESSAGES
-- ============================================================

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    inscription_id INTEGER REFERENCES inscriptions(id) ON DELETE SET NULL,
    contenu TEXT NOT NULL,
    lu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_messages_receiver ON messages(receiver_id, lu);
CREATE INDEX IF NOT EXISTS ix_messages_sender ON messages(sender_id);

-- ============================================================
-- 4. TABLE NOTIFICATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    -- Types : inscription_soumise | inscription_validee | inscription_rejetee |
    --         nouveau_message | rapport_absence_soumis | certification_emise
    titre VARCHAR(200) NOT NULL,
    contenu TEXT,
    lu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_lu ON notifications(user_id, lu);

-- ============================================================
-- 5. TABLE RAPPORTS ABSENCE
-- ============================================================

CREATE TABLE IF NOT EXISTS rapports_absence (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    formateur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_rapport DATE NOT NULL DEFAULT CURRENT_DATE,
    contenu TEXT,
    participants_absents JSONB DEFAULT '[]',
    -- Format : [{"participant_id": 1, "nom": "...", "jours": [1, 3]}, ...]
    statut VARCHAR(20) DEFAULT 'brouillon',
    -- statut : brouillon | soumis | vu_admin
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_statut_rapport CHECK (statut IN ('brouillon', 'soumis', 'vu_admin'))
);

CREATE INDEX IF NOT EXISTS ix_rapports_absence_cycle ON rapports_absence(cycle_id);
CREATE INDEX IF NOT EXISTS ix_rapports_absence_formateur ON rapports_absence(formateur_id);

-- ============================================================
-- 6. TABLE CERTIFICATIONS INFALSIFIABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS certifications (
    id SERIAL PRIMARY KEY,
    inscription_id INTEGER NOT NULL UNIQUE REFERENCES inscriptions(id) ON DELETE RESTRICT,
    participant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE RESTRICT,
    hash_verification VARCHAR(64) NOT NULL UNIQUE,
    -- SHA256(participant_id:cycle_id:date_emission:SECRET_KEY)
    date_emission TIMESTAMP NOT NULL DEFAULT NOW(),
    pdf_path VARCHAR(255),
    est_valide BOOLEAN DEFAULT TRUE,
    revocation_motif TEXT,
    revoque_at TIMESTAMP,
    revoque_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_certifications_hash ON certifications(hash_verification);
CREATE INDEX IF NOT EXISTS ix_certifications_participant ON certifications(participant_id);

-- ============================================================
-- 7. TRIGGER — nb_inscrits automatique (remplace le manuel)
-- ============================================================

CREATE OR REPLACE FUNCTION update_nb_inscrits()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.statut NOT IN ('annule', 'rejete') THEN
            UPDATE cycles SET nb_inscrits = nb_inscrits + 1 WHERE id = NEW.cycle_id;
        END IF;

    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.statut NOT IN ('annule', 'rejete') THEN
            UPDATE cycles SET nb_inscrits = GREATEST(0, nb_inscrits - 1) WHERE id = OLD.cycle_id;
        END IF;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Passage vers annule/rejete : décrémenter
        IF OLD.statut NOT IN ('annule', 'rejete') AND NEW.statut IN ('annule', 'rejete') THEN
            UPDATE cycles SET nb_inscrits = GREATEST(0, nb_inscrits - 1) WHERE id = NEW.cycle_id;
        -- Retour depuis annule/rejete : incrémenter
        ELSIF OLD.statut IN ('annule', 'rejete') AND NEW.statut NOT IN ('annule', 'rejete') THEN
            UPDATE cycles SET nb_inscrits = nb_inscrits + 1 WHERE id = NEW.cycle_id;
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_nb_inscrits ON inscriptions;
CREATE TRIGGER trg_nb_inscrits
    AFTER INSERT OR UPDATE OR DELETE ON inscriptions
    FOR EACH ROW EXECUTE FUNCTION update_nb_inscrits();

-- ============================================================
-- 8. TRIGGER — updated_at automatique
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_messages_updated_at ON messages;
CREATE TRIGGER trg_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_rapports_updated_at ON rapports_absence;
CREATE TRIGGER trg_rapports_updated_at
    BEFORE UPDATE ON rapports_absence
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;

-- ============================================================
-- VÉRIFICATION (à lancer après)
-- ============================================================
-- \dt         → liste toutes les tables
-- \d inscriptions  → voir les nouvelles colonnes
-- SELECT * FROM certifications LIMIT 0;
-- SELECT * FROM messages LIMIT 0;
-- SELECT * FROM notifications LIMIT 0;
-- SELECT * FROM rapports_absence LIMIT 0;