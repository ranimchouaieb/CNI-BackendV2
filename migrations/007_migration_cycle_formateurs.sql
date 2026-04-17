-- ============================================================
-- MIGRATION 007 — Relation Many-to-Many : Cycle ↔ Formateurs
-- Un cycle peut être animé par plusieurs formateurs
-- psql -U <user> -d <database> -f 007_migration_cycle_formateurs.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CRÉER LA TABLE D'ASSOCIATION cycle_formateurs
-- ============================================================

CREATE TABLE IF NOT EXISTS cycle_formateurs (
    cycle_id INTEGER NOT NULL REFERENCES cycles(id)  ON DELETE CASCADE,
    user_id  INTEGER NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    PRIMARY KEY (cycle_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_cycle_formateurs_cycle   ON cycle_formateurs(cycle_id);
CREATE INDEX IF NOT EXISTS idx_cycle_formateurs_user    ON cycle_formateurs(user_id);

-- ============================================================
-- 2. MIGRER LES DONNÉES DE L'ANCIEN FORMATEUR_ID (si la colonne existe)
--    Transfère le formateur unique déjà assigné vers la nouvelle table
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'cycles' AND column_name = 'formateur_id'
    ) THEN
        INSERT INTO cycle_formateurs (cycle_id, user_id)
        SELECT id, formateur_id
        FROM cycles
        WHERE formateur_id IS NOT NULL
        ON CONFLICT DO NOTHING;

        RAISE NOTICE 'Données migrées depuis cycles.formateur_id vers cycle_formateurs.';
    ELSE
        RAISE NOTICE 'Colonne cycles.formateur_id absente — aucune donnée à migrer.';
    END IF;
END;
$$;

-- ============================================================
-- 3. SUPPRIMER L'ANCIENNE COLONNE formateur_id DE cycles (si elle existe)
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'cycles' AND column_name = 'formateur_id'
    ) THEN
        -- Supprimer la FK associée avant de dropper la colonne
        ALTER TABLE cycles DROP COLUMN formateur_id;
        RAISE NOTICE 'Colonne cycles.formateur_id supprimée.';
    ELSE
        RAISE NOTICE 'Colonne cycles.formateur_id déjà absente — rien à supprimer.';
    END IF;
END;
$$;

-- ============================================================
-- 4. VÉRIFICATION FINALE
-- ============================================================

DO $$
DECLARE
    nb_liens INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_liens FROM cycle_formateurs;
    RAISE NOTICE 'Table cycle_formateurs créée avec % lien(s) cycle-formateur.', nb_liens;
END;
$$;

COMMIT;
