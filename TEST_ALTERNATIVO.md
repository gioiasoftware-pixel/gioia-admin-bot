# 🧪 Test Alternativo - Script SQL

Poiché `asyncpg` richiede compilazione C++ su Windows, puoi testare il bot admin usando direttamente SQL.

## Metodo 1: Usa Railway Database Dashboard

1. Vai su Railway Dashboard
2. Apri il database PostgreSQL
3. Vai alla tab **"Data"** o **"Query"**
4. Copia e incolla il contenuto di `test_admin_bot.sql`
5. Esegui lo script

## Metodo 2: Usa un client SQL (pgAdmin, DBeaver, etc.)

1. Connettiti al database PostgreSQL usando `DATABASE_URL` da Railway
2. Esegui lo script `test_admin_bot.sql`

## Metodo 3: Usa Railway CLI con SQL

```bash
railway connect
# Poi esegui lo script SQL
```

## Verifica

Dopo aver eseguito lo script SQL:

1. ✅ 3 notifiche dovrebbero essere inserite con `status='pending'`
2. ✅ Il bot admin su Railway le processerà entro 5-10 secondi
3. ✅ Controlla il bot Telegram per i 3 messaggi:
   - 🎉 Onboarding completato
   - 📦 Inventario caricato
   - 🚨 Errore
4. ✅ Le notifiche nel database dovrebbero avere `status='sent'` dopo l'invio

## Verifica Database

```sql
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
```

