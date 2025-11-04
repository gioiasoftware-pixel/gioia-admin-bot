# 📋 Guida: Dove Incollare lo Script SQL su Railway

## 🎯 Passo per Passo

### STEP 1: Apri Railway Dashboard
1. Vai su https://railway.app
2. Accedi al tuo account
3. Apri il progetto che contiene il database PostgreSQL

### STEP 2: Trova il Database
1. Nel progetto Railway, cerca il servizio **PostgreSQL** (o il nome del tuo database)
2. Clicca sul servizio database

### STEP 3: Apri Query Editor
Hai 3 opzioni possibili (dipende dalla versione di Railway):

**Opzione A: Tab "Query"**
- Clicca sulla tab **"Query"** in alto
- Vedrai un editor SQL con una textarea/campo di testo

**Opzione B: Tab "Data" → "Query"**
- Clicca sulla tab **"Data"**
- Cerca un pulsante **"Query"** o **"SQL Editor"**
- Clicca per aprire l'editor SQL

**Opzione C: Tab "Settings" → "Connect"**
- Se non vedi "Query", vai su **"Settings"** o **"Connect"**
- Copia la stringa di connessione
- Usa un client SQL esterno (vedi alternativa sotto)

### STEP 4: Incolla lo Script
1. **Apri il file `test_admin_bot.sql`** dalla cartella `Gioiadmin_bot`
2. **Copia tutto il contenuto** (Ctrl+A, Ctrl+C)
3. **Incolla nell'editor SQL** di Railway (Ctrl+V)
4. **Clicca "Run"** o "Execute" o premi F5

### STEP 5: Verifica
Dovresti vedere:
- ✅ 3 righe inserite
- ✅ Una query SELECT che mostra le 3 notifiche con `status='pending'`

---

## 🔄 Alternativa: Se Non Trovi Query Editor

Se Railway non ha un editor SQL integrato, usa **Railway CLI**:

```bash
# Nella cartella Gioiadmin_bot
railway connect
# Poi incolla lo script SQL direttamente nel terminale PostgreSQL
```

Oppure usa un client SQL esterno (pgAdmin, DBeaver, TablePlus) con `DATABASE_URL` da Railway Variables.

---

## 📝 Contenuto Script da Incollare

Lo script si trova in: `Gioiadmin_bot/test_admin_bot.sql`

Contiene:
- 3 INSERT per creare notifiche di test
- 1 SELECT per verificare gli inserimenti

