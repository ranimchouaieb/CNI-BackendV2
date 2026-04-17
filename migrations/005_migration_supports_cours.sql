-- ============================================================
-- Migration 005 : Table supports_cours
-- Date : 2026-04-05
-- Description : Supports de cours uploadés par les formateurs
--               par cycle (PDF, PPTX, DOCX, ZIP...)
-- ============================================================

CREATE TABLE IF NOT EXISTS supports_cours (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    formateur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    fichier_path VARCHAR(500) NOT NULL,
    fichier_type VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supports_cycle ON supports_cours(cycle_id);

COMMENT ON TABLE supports_cours IS
    'Supports de cours uploadés par les formateurs pour leurs cycles.';

-- Vérification
SELECT COUNT(*) as nb_supports FROM supports_cours;
