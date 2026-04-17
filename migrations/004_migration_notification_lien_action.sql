-- ============================================================
-- Migration 004 : Ajout colonne lien_action dans notifications
-- Date : 2026-04-04
-- Description : Permet aux notifications d'être cliquables
--               en stockant le lien de redirection frontend.
-- ============================================================

-- Ajouter la colonne lien_action
ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS lien_action VARCHAR(255) DEFAULT NULL;

-- Commentaire descriptif
COMMENT ON COLUMN notifications.lien_action IS
    'URL relative frontend pour navigation depuis la cloche de notifications. Ex: /mes-certifications, /admin/inscriptions/en-attente';

-- Vérification
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'notifications'
  AND column_name = 'lien_action';
