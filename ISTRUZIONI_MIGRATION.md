# 🗄️ Istruzioni Esecuzione Migration

## Opzione 1: Railway CLI (Consigliato - Nessuna password esposta)

Se hai Railway CLI installato:

```bash
railway connect Postgres-Wyfk
railway run python run_migration.py
```

Oppure:
```bash
railway connect Postgres-Wyfk
railway run psql -f migrations/001_create_admin_notifications.sql
```

---

## Opzione 2: Script Python (Sicuro - Usa DATABASE_URL)

Lo script `run_migration.py` legge automaticamente `DATABASE_URL` da Railway.

**Su Railway:**
1. Vai al servizio che contiene il database
2. Tab "Variables"
3. Copia il valore di `DATABASE_URL`
4. Esporta localmente (solo per test):
   ```bash
   export DATABASE_URL="postgresql://postgres:PASSWORD@gondola.proxy.rlwy.net:14020/railway"
   ```
5. Esegui:
   ```bash
   cd Gioiadmin_bot
   pip install -r requirements.txt
   python run_migration.py
   ```

**⚠️ IMPORTANTE:** Non committare mai la password nel codice! Usa sempre variabili ambiente.

---

## Opzione 3: psql Diretto (Richiede password)

Se preferisci usare psql direttamente:

1. **Copia il Connection URL completo** da Railway (clicca "show" per vedere la password)
2. Esegui:
   ```bash
   psql "postgresql://postgres:PASSWORD@gondola.proxy.rlwy.net:14020/railway" -f migrations/001_create_admin_notifications.sql
   ```

**⚠️ SICUREZZA:** Non eseguire questo comando in un terminale condiviso o con history visibile!

---

## Opzione 4: Railway Dashboard SQL Editor

1. Railway Dashboard → Database → "Connect" → "Query"
2. Apri `migrations/001_create_admin_notifications.sql`
3. Copia tutto il contenuto
4. Incolla nell'editor SQL
5. Clicca "Execute"

---

## ✅ Verifica

Dopo la migration, verifica:

```sql
-- Verifica tabella
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'admin_notifications';

-- Verifica colonne
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'admin_notifications'
ORDER BY ordinal_position;

-- Verifica indici
SELECT indexname 
FROM pg_indexes
WHERE tablename = 'admin_notifications';
```

---

## 🎯 Raccomandazione

**Usa Opzione 1 (Railway CLI)** o **Opzione 4 (Dashboard SQL Editor)** per evitare di esporre password.

