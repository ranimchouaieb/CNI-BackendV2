-- ============================================================
-- Migration 010 — Simplification statuts inscription (2026-04-12)
-- ============================================================
-- Avant : en_attente_validation | confirme | inscrit | present | absent | annule | rejete
-- Après : en_attente_validation | confirme | rejete
-- ============================================================

-- 1. Convertir les statuts supprimés vers leur équivalent
UPDATE inscriptions SET statut = 'confirme' WHERE statut IN ('inscrit', 'present', 'absent');
UPDATE inscriptions SET statut = 'rejete'   WHERE statut = 'annule';

-- 2. Mettre à jour la contrainte CHECK
ALTER TABLE inscriptions DROP CONSTRAINT IF EXISTS check_statut_inscription;
ALTER TABLE inscriptions ADD CONSTRAINT check_statut_inscription
    CHECK (statut IN ('en_attente_validation', 'confirme', 'rejete'));
