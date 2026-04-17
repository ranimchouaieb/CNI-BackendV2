-- ============================================================
-- MIGRATION 003 — Ajout table formations (catalogue)
-- + formation_id FK dans cycles
-- psql -U <user> -d <database> -f 003_migration_formations.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. TABLE formations — catalogue des programmes de formation
-- ============================================================

CREATE TABLE IF NOT EXISTS formations (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(200) NOT NULL,
    domaine VARCHAR(100),
    description TEXT,
    objectifs TEXT,
    programme TEXT,
    duree_jours INTEGER DEFAULT 5,
    prix_base NUMERIC(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_formations_titre ON formations(titre);
CREATE INDEX IF NOT EXISTS ix_formations_domaine ON formations(domaine);

-- Trigger updated_at
DROP TRIGGER IF EXISTS trg_formations_updated_at ON formations;
CREATE TRIGGER trg_formations_updated_at
    BEFORE UPDATE ON formations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 2. Ajouter formation_id à cycles (FK nullable)
-- ============================================================

ALTER TABLE cycles
    ADD COLUMN IF NOT EXISTS formation_id INTEGER REFERENCES formations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_cycles_formation_id ON cycles(formation_id);

-- ============================================================
-- 3. Peupler formations à partir des themes existants dans cycles
--    (optionnel — crée une formation par theme_formation distinct)
-- ============================================================

INSERT INTO formations (titre, domaine, description, duree_jours, created_at, updated_at)
SELECT DISTINCT
    theme_formation,
    'Informatique & Digital',
    'Formation professionnelle sur ' || theme_formation || '.',
    GREATEST(1, (date_fin - date_debut + 1)),
    NOW(),
    NOW()
FROM cycles
WHERE theme_formation IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM formations WHERE titre = cycles.theme_formation
  )
ORDER BY theme_formation;

-- Lier les cycles existants à leur formation correspondante
UPDATE cycles c
SET formation_id = f.id
FROM formations f
WHERE f.titre = c.theme_formation
  AND c.formation_id IS NULL;

-- ============================================================
-- VERIFICATION
-- ============================================================
-- SELECT COUNT(*) FROM formations;
-- SELECT COUNT(*) FROM cycles WHERE formation_id IS NOT NULL;
-- \d formations

COMMIT;
