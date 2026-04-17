-- Migration 006 : Table propositions_cycles
-- Permet aux formateurs de proposer un cycle avec document de qualification
-- L'admin valide ou rejette la proposition

CREATE TABLE IF NOT EXISTS propositions_cycles (
    id                  SERIAL PRIMARY KEY,
    formateur_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    formation_id        INTEGER REFERENCES formations(id) ON DELETE SET NULL,
    theme_propose       VARCHAR(200) NOT NULL,
    justification       TEXT,
    document_path       VARCHAR(500),
    document_type       VARCHAR(10),
    statut              VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                            CHECK (statut IN ('en_attente', 'approuve', 'rejete')),
    motif_rejet         TEXT,
    cycle_cree_id       INTEGER REFERENCES cycles(id) ON DELETE SET NULL,
    traite_par          INTEGER REFERENCES users(id) ON DELETE SET NULL,
    traite_at           TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_propositions_formateur ON propositions_cycles(formateur_id);
CREATE INDEX IF NOT EXISTS idx_propositions_statut    ON propositions_cycles(statut);
