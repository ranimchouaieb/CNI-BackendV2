-- ============================================================
-- Migration 009 — Statut cycle "termine" (2026-04-12)
-- ============================================================
-- 1. Remplacer la contrainte CHECK cycles.statut
--    pour accepter la nouvelle valeur 'termine'
-- 2. Corriger les statuts stales existants
-- ============================================================

-- 1. Contrainte CHECK mise à jour
ALTER TABLE cycles DROP CONSTRAINT IF EXISTS cycles_statut_check;
ALTER TABLE cycles ADD CONSTRAINT cycles_statut_check
    CHECK (statut IN ('vert', 'orange', 'rouge', 'termine'));

-- 2. Cycles terminés (date_fin passée, non annulés)
UPDATE cycles SET statut = 'termine'
WHERE date_fin < CURRENT_DATE AND is_cancelled = false;

-- 3. Cycles en cours (date_debut <= today <= date_fin)
UPDATE cycles SET statut = 'vert'
WHERE date_debut <= CURRENT_DATE AND date_fin >= CURRENT_DATE AND is_cancelled = false;

-- 4. Cycles planifiés (date_debut future)
UPDATE cycles SET statut = 'orange'
WHERE date_debut > CURRENT_DATE AND is_cancelled = false;
