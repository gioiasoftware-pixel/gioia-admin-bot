-- Script SQL per testare il bot admin
-- Inserisce 3 notifiche di test nella tabella admin_notifications
-- Esegui questo script direttamente nel database PostgreSQL

-- Test 1: Onboarding completato
INSERT INTO admin_notifications 
(id, created_at, status, event_type, telegram_id, correlation_id, payload, retry_count, next_attempt_at)
VALUES (
    gen_random_uuid(),
    NOW(),
    'pending',
    'onboarding_completed',
    123456789,
    gen_random_uuid()::text,
    '{
        "business_name": "Ristorante Test",
        "user_name": "Test User",
        "onboarding_duration_seconds": 120,
        "inventory_items_count": 25
    }'::jsonb,
    0,
    NOW()
);

-- Test 2: Inventario caricato
INSERT INTO admin_notifications 
(id, created_at, status, event_type, telegram_id, correlation_id, payload, retry_count, next_attempt_at)
VALUES (
    gen_random_uuid(),
    NOW(),
    'pending',
    'inventory_uploaded',
    123456789,
    gen_random_uuid()::text,
    '{
        "business_name": "Ristorante Test",
        "file_type": "csv",
        "file_size_bytes": 15234,
        "wines_processed": 25,
        "wines_saved": 25,
        "warnings_count": 3,
        "processing_duration_seconds": 45
    }'::jsonb,
    0,
    NOW()
);

-- Test 3: Errore
INSERT INTO admin_notifications 
(id, created_at, status, event_type, telegram_id, correlation_id, payload, retry_count, next_attempt_at)
VALUES (
    gen_random_uuid(),
    NOW(),
    'pending',
    'error',
    123456789,
    gen_random_uuid()::text,
    '{
        "business_name": "Ristorante Test",
        "error_type": "processing_error",
        "error_message": "Errore di test: file non valido",
        "error_code": "INVALID_FILE",
        "component": "processor",
        "correlation_id": "test-correlation-id"
    }'::jsonb,
    0,
    NOW()
);

-- Verifica inserimenti
SELECT 
    id,
    created_at,
    status,
    event_type,
    telegram_id,
    retry_count
FROM admin_notifications
WHERE telegram_id = 123456789
ORDER BY created_at DESC
LIMIT 3;

