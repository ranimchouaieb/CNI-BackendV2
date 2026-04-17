-- ============================================================
-- Migration 008 — Refactoring fonctionnel (2026-04-12)
-- ============================================================
-- 1. Suppression PropositionCycle
-- 2. Formation : suppression is_active, ajout tva_pct
-- 3. Cycle : ajout tva_pct
-- 4. Certification : suppression est_valide, revocation_motif, revoque_at, revoque_by
-- ============================================================

-- ------------------------------------------------------------
-- 1. SUPPRIMER LA TABLE propositions_cycles
-- ------------------------------------------------------------
DROP TABLE IF EXISTS propositions_cycles CASCADE;

-- ------------------------------------------------------------
-- 2. FORMATION — supprimer is_active, ajouter tva_pct
-- ------------------------------------------------------------
ALTER TABLE formations DROP COLUMN IF EXISTS is_active;
ALTER TABLE formations ADD COLUMN IF NOT EXISTS tva_pct NUMERIC(5,2);

-- ------------------------------------------------------------
-- 3. CYCLE — ajouter tva_pct
-- ------------------------------------------------------------
ALTER TABLE cycles ADD COLUMN IF NOT EXISTS tva_pct NUMERIC(5,2);

-- ------------------------------------------------------------
-- 4. CERTIFICATION — supprimer champs révocation
-- ------------------------------------------------------------
ALTER TABLE certifications DROP COLUMN IF EXISTS est_valide;
ALTER TABLE certifications DROP COLUMN IF EXISTS revocation_motif;
ALTER TABLE certifications DROP COLUMN IF EXISTS revoque_at;
ALTER TABLE certifications DROP COLUMN IF EXISTS revoque_by;
