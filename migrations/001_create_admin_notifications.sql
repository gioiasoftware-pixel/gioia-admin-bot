-- Migration: Crea tabella admin_notifications per bot admin
-- Esegui con: psql $DATABASE_URL -f migrations/001_create_admin_notifications.sql
-- Oppure tramite Railway dashboard → Database → Connect → Query

CREATE TABLE IF NOT EXISTS admin_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT now(),
    status TEXT DEFAULT 'pending',
    event_type TEXT NOT NULL,
    telegram_id BIGINT NOT NULL,
    correlation_id TEXT,
    payload JSONB NOT NULL,
    retry_count INTEGER DEFAULT 0,
    next_attempt_at TIMESTAMP DEFAULT now()
);

-- Indice per query pending (worker legge da qui)
CREATE INDEX IF NOT EXISTS idx_admin_pending
    ON admin_notifications (status, next_attempt_at)
    WHERE status = 'pending';

-- Indice per query per utente (anti-spam)
CREATE INDEX IF NOT EXISTS idx_admin_user_created
    ON admin_notifications (telegram_id, created_at DESC);

-- Indice per correlation_id (debugging)
CREATE INDEX IF NOT EXISTS idx_admin_correlation
    ON admin_notifications (correlation_id)
    WHERE correlation_id IS NOT NULL;

-- Commenti per documentazione
COMMENT ON TABLE admin_notifications IS 'Coda notifiche per bot admin - letta da gioia-admin-bot';
COMMENT ON COLUMN admin_notifications.status IS 'pending, sent, failed';
COMMENT ON COLUMN admin_notifications.event_type IS 'onboarding_completed, inventory_uploaded, error';
COMMENT ON COLUMN admin_notifications.payload IS 'JSON con dettagli evento (business_name, file_type, error_message, ecc.)';

