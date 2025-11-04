# 🚀 Guida Setup Gioia Admin Bot

## ✅ Dati Configurazione

**ADMIN_BOT_TOKEN:** `8455675311:AAHkwtkB3W4o8TQ8taEilu8XQ3Z51YPvSFU`  
**ADMIN_CHAT_ID:** `987654321`

---

## 📋 Checklist Pre-Implementazione

- [x] Bot Telegram creato con BotFather
- [x] TOKEN ottenuto
- [x] ADMIN_CHAT_ID ottenuto
- [ ] Migration database eseguita
- [ ] Tabella `admin_notifications` verificata

---

## 🗄️ Passo 3: Eseguire Migration Database

### Opzione A: Railway Dashboard (Consigliato)

1. Vai su [Railway Dashboard](https://railway.app)
2. Seleziona il tuo progetto
3. Clicca sul servizio **PostgreSQL** (o il servizio che contiene DATABASE_URL)
4. Vai alla tab **"Data"** o **"Connect"**
5. Clicca **"Connect"** o **"Query"**
6. Si aprirà un editor SQL o pannello connessione
7. Copia il contenuto di `migrations/001_create_admin_notifications.sql`
8. Incolla nell'editor
9. Clicca **"Execute"** o **"Run"**

### Opzione B: psql da Terminale

1. Railway Dashboard → Database → **"Connect"**
2. Copia la **Connection String** (es. `postgresql://user:pass@host:port/db`)
3. Esegui:
   ```bash
   psql "postgresql://user:pass@host:port/db" -f migrations/001_create_admin_notifications.sql
   ```

### Opzione C: Script Python (se preferisci)

Esegui:
```bash
cd Gioiadmin_bot
python run_migration.py
```
*(Script da creare se necessario)*

---

## ✅ Verifica Migration

Dopo aver eseguito la migration, verifica che tutto sia corretto:

1. Esegui il contenuto di `verify_migration.sql` nel database
2. Dovresti vedere:
   - Tabella `admin_notifications` esiste
   - 10 colonne (id, created_at, status, event_type, telegram_id, correlation_id, payload, retry_count, next_attempt_at)
   - 3 indici creati
   - Test insert funziona

---

## 📝 Note

- La tabella `admin_notifications` è **condivisa** tra bot principale, processor e admin bot
- Il bot admin legge da questa tabella e invia notifiche
- I servizi esistenti scrivono in questa tabella tramite helper `enqueue_admin_notification()`

---

## 🎯 Prossimi Passi

Dopo la migration:
1. Verifica che la tabella sia stata creata ✅
2. Procedi con l'implementazione del bot admin
3. Configura Railway con variabili ambiente

