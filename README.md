🧠 README — gioia-admin-bot

📌 Obiettivo



Creare un bot Telegram privato dedicato all’amministratore per ricevere:



🎉 Notifiche di onboarding completato



📦 Conferme di import inventario



🚨 Segnalazioni di errori (con ultimo messaggio utente + errore mostrato)



Il bot deve essere isolato dagli altri servizi, leggendo gli eventi da una tabella condivisa admin\_notifications nel database PostgreSQL.



🧩 Struttura del progetto

gioia-admin-bot/

│

├── main.py                # entrypoint principale

├── worker.py              # task scheduler per invio notifiche

├── db.py                  # gestione connessione Postgres async

├── models.py              # definizione tabella admin\_notifications

├── notifier.py            # logica invio messaggi Telegram

├── templates.py           # formattazione messaggi

├── utils/

│   ├── rate\_limiter.py    # rate limit globale + anti spam

│   ├── backoff.py         # backoff con jitter per retry

│   └── logging.py         # logging strutturato

│

├── migrations/

│   └── 001\_create\_admin\_notifications.sql

│

└── README.md



⚙️ Funzionamento

1️⃣ Sorgente eventi



Il telegram-ai-bot e il gioia-processor scrivono eventi nella tabella:



INSERT INTO admin\_notifications

(event\_type, telegram\_id, payload, correlation\_id)

VALUES ('onboarding\_completed', 12345, '{"business\_name":"Enoteca X"}', 'abc-123');





Event types previsti:



onboarding\_completed



inventory\_uploaded



error



2️⃣ Coda notifiche



Il bot legge ogni N secondi gli eventi status='pending' dalla tabella e invia i messaggi via sendMessage a ADMIN\_CHAT\_ID.



Dopo l’invio:



✅ status='sent'



❌ in caso di errore → retry\_count++, next\_attempt\_at=now()+backoff



se retry\_count > 10 → status='failed'



3️⃣ Rate limit \& Anti-spam



Globale: max ADMIN\_NOTIFY\_RATE\_LIMIT\_PER\_MIN invii/minuto



Per utente: 1 errore notificato ogni ADMIN\_NOTIFY\_MIN\_ERROR\_INTERVAL\_SEC secondi



Batch automatico se più errori arrivano nello stesso intervallo



4️⃣ Formati messaggi

🎉 Onboarding completato

🎉 ONBOARDING COMPLETATO

👤 Utente: 123456789 — Mario Rossi

🏪 Business: Enoteca X

⏱️ Durata: 5m 12s

🔗 CorrID: abc-123



📦 Inventario caricato

📦 INVENTARIO IMPORTATO (DAY 0)

👤 Utente: 123456789 — Mario Rossi

📄 File: CSV (524 righe, 2 scartate)

⏱️ Tempo: 18.3s

🔗 CorrID: abc-123



🚨 Errore

🚨 ERRORE

👤 Utente: 123456789 — Mario Rossi

📥 Ultimo messaggio: “Carica inventario”

📤 Errore mostrato: “Formato file non valido”

💻 Codice: E\_INV\_002 — Sorgente: processor

🔗 CorrID: abc-123



🧱 Database Schema

migrations/001\_create\_admin\_notifications.sql

CREATE TABLE IF NOT EXISTS admin\_notifications (

&nbsp;   id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

&nbsp;   created\_at TIMESTAMP DEFAULT now(),

&nbsp;   status TEXT DEFAULT 'pending',

&nbsp;   event\_type TEXT NOT NULL,

&nbsp;   telegram\_id BIGINT NOT NULL,

&nbsp;   correlation\_id TEXT,

&nbsp;   payload JSONB NOT NULL,

&nbsp;   retry\_count INTEGER DEFAULT 0,

&nbsp;   next\_attempt\_at TIMESTAMP DEFAULT now()

);



CREATE INDEX IF NOT EXISTS idx\_admin\_pending

&nbsp;   ON admin\_notifications (status, next\_attempt\_at);



CREATE INDEX IF NOT EXISTS idx\_admin\_user\_created

&nbsp;   ON admin\_notifications (telegram\_id, created\_at DESC);



🌍 Variabili d’ambiente

\# Telegram Bot (admin)

ADMIN\_BOT\_TOKEN=123456:ABCDEF...

ADMIN\_CHAT\_ID=987654321

ADMIN\_NOTIFY\_ENABLED=true



\# Database condiviso

DATABASE\_URL=postgresql+asyncpg://user:pass@host:port/db



\# Rate limit

ADMIN\_NOTIFY\_RATE\_LIMIT\_PER\_MIN=20

ADMIN\_NOTIFY\_MIN\_ERROR\_INTERVAL\_SEC=180



\# Backoff \& Retry

ADMIN\_MAX\_RETRY=10

ADMIN\_BACKOFF\_BASE=10



🚀 Esecuzione

**⚠️ IMPORTANTE:** Il bot esegue automaticamente la migration all'avvio!
Non serve eseguire manualmente la migration - quando deployi su Railway, il bot crea automaticamente la tabella `admin_notifications` usando la `DATABASE_URL` già configurata.

Localmente:

pip install -r requirements.txt

python main.py

*(Se DATABASE_URL non è configurata, esportala: `export DATABASE_URL="..."`)*



Su Railway:



1. Crea nuovo servizio "gioia-admin-bot"

2. Collegalo allo stesso database PostgreSQL (usa "Add Service" → "Database" → seleziona database esistente)

3. Railway configurerà automaticamente `DATABASE_URL`

4. Imposta variabili ambiente:
   - `ADMIN_BOT_TOKEN=8455675311:AAHkwtkB3W4o8TQ8taEilu8XQ3Z51YPvSFU`
   - `ADMIN_CHAT_ID=987654321`
   - `ADMIN_NOTIFY_ENABLED=true`
   - `ADMIN_NOTIFY_RATE_LIMIT_PER_MIN=20`
   - `ADMIN_NOTIFY_MIN_ERROR_INTERVAL_SEC=180`
   - `ADMIN_MAX_RETRY=10`
   - `ADMIN_BACKOFF_BASE=10`

5. Deploy da GitHub con auto-restart on fail

6. ✅ La tabella `admin_notifications` verrà creata automaticamente al primo avvio!



🧩 Integrazione con gli altri servizi

In telegram-ai-bot e gioia-processor:



Aggiungere helper (una riga comune di enqueue):



await enqueue\_admin\_notification(

&nbsp;   event\_type="error",

&nbsp;   telegram\_id=user.telegram\_id,

&nbsp;   correlation\_id=corr\_id,

&nbsp;   payload={

&nbsp;       "last\_user\_message": message\_text,

&nbsp;       "user\_visible\_error": user\_error,

&nbsp;       "source": "bot",

&nbsp;       "error\_code": "E\_AI\_002"

&nbsp;   }

)





L’helper scrive nella tabella condivisa, il gioia-admin-bot pensa al resto.



🧪 Test Checklist

Test	Aspettato

Onboarding completato	🎉 notifica con nome + business

Upload inventario	📦 notifica con righe e tempo

Errore utente	🚨 con ultimo messaggio + errore mostrato

Rate limit	non più di 1 errore per utente/180s

Retry Telegram 429	invio riuscito dopo retry

Disattivato	ADMIN\_NOTIFY\_ENABLED=false → nessuna notifica

🧰 Cosa deve fare Cursor (AI)



Creare nuova directory gioia-admin-bot/ con struttura indicata



Implementare:



main.py → ciclo async che avvia worker



db.py → connessione asyncpg



notifier.py → invio messaggi Telegram



worker.py → loop lettura admin\_notifications



Aggiungere migrations/001\_create\_admin\_notifications.sql



Creare helper condiviso enqueue\_admin\_notification() (per bot e processor)



Integrare la chiamata negli eventi di successo/errore



Scrivere log strutturato per ogni invio con correlation\_id



📋 Cosa deve fare l'utente (Azioni Manuali)

✅ **COMPLETATE:**

1. ✅ **Bot Telegram creato** - TOKEN: `8455675311:AAHkwtkB3W4o8TQ8taEilu8XQ3Z51YPvSFU`
2. ✅ **ADMIN_CHAT_ID ottenuto** - `987654321`
3. ✅ **DATABASE_URL già configurata** - Railway la gestisce automaticamente

📋 **Prossimi Passi (quando implementazione pronta):**

4. **Configurare Railway**

   - Crea nuovo servizio "gioia-admin-bot"
   - Collegalo allo stesso database PostgreSQL (Railway lo trova automaticamente)
   - Railway configurerà automaticamente `DATABASE_URL`
   - Imposta variabili ambiente:
     - `ADMIN_BOT_TOKEN=8455675311:AAHkwtkB3W4o8TQ8taEilu8XQ3Z51YPvSFU`
     - `ADMIN_CHAT_ID=987654321`
     - `ADMIN_NOTIFY_ENABLED=true`
     - `ADMIN_NOTIFY_RATE_LIMIT_PER_MIN=20`
     - `ADMIN_NOTIFY_MIN_ERROR_INTERVAL_SEC=180`
     - `ADMIN_MAX_RETRY=10`
     - `ADMIN_BACKOFF_BASE=10`
   - Deploy da GitHub
   - ✅ **La tabella `admin_notifications` verrà creata automaticamente al primo avvio!**

**⚠️ NOTA:** Non serve eseguire manualmente la migration! Il bot ha auto-migration all'avvio (come il processor).



🔧 Dettagli Implementazione



**1. Recupero informazioni utente**

Il bot admin deve recuperare informazioni utente dal database per formattare i messaggi. Usa la tabella `users`:

```python
# Esempio query per recuperare username
SELECT telegram_id, username, first_name, last_name, business_name, created_at
FROM users
WHERE telegram_id = :telegram_id
```

**2. Calcolo durata onboarding**

Per calcolare la durata onboarding:
- Recuperare `created_at` dalla tabella `users` quando `onboarding_completed=True`
- Calcolare differenza con timestamp evento `onboarding_completed`
- Formattare: "5m 12s" o "2h 15m" se > 1 ora

**3. Codici errore**

Definire codici errore standardizzati:
- `E_BOT_001` - Errore AI (bot)
- `E_BOT_002` - Errore database (bot)
- `E_BOT_003` - Errore processor (bot)
- `E_PROC_001` - Errore parsing file (processor)
- `E_PROC_002` - Errore validazione dati (processor)
- `E_PROC_003` - Errore database (processor)
- `E_INV_001` - File non supportato
- `E_INV_002` - File formato non valido
- `E_INV_003` - Dati mancanti obbligatori

**4. Helper condiviso**

Creare helper comune in `telegram-ai-bot/src/admin_notifications.py` e `gioia-processor/admin_notifications.py`:

```python
async def enqueue_admin_notification(
    event_type: str,
    telegram_id: int,
    correlation_id: str,
    payload: dict
):
    """
    Helper per aggiungere notifica admin alla coda.
    Può essere chiamato da bot o processor.
    """
    # INSERT nella tabella admin_notifications
    # Usa asyncpg direttamente o tramite sessione condivisa
```

**5. Integrazione eventi**

**Nel bot (`telegram-ai-bot/src/new_onboarding.py`):**
- Quando onboarding completato → `enqueue_admin_notification('onboarding_completed', ...)`
- Payload: `{"business_name": "...", "duration_seconds": 312}`

**Nel bot (`telegram-ai-bot/src/file_upload.py`):**
- Quando inventario caricato → `enqueue_admin_notification('inventory_uploaded', ...)`
- Payload: `{"file_type": "csv", "rows_processed": 524, "rows_rejected": 2, "processing_time": 18.3}`

**Nel bot (`telegram-ai-bot/src/bot.py` o `ai.py`):**
- Quando errore mostrato all'utente → `enqueue_admin_notification('error', ...)`
- Payload: `{"last_user_message": "...", "user_visible_error": "...", "source": "bot", "error_code": "E_BOT_001"}`

**Nel processor (`gioia-processor/main.py`):**
- Quando errore durante processing → `enqueue_admin_notification('error', ...)`
- Payload: `{"error_message": "...", "source": "processor", "error_code": "E_PROC_001", "job_id": "..."}`

**6. Structured logging**

Il sistema già usa `structured_logging.py` con `correlation_id`. Il bot admin deve:
- Loggare ogni invio notifica con `correlation_id`
- Loggare ogni retry con backoff
- Loggare errori finali dopo max retry

**7. Rate limiting per utente**

Per evitare spam di errori dello stesso utente:
- Mantenere track degli ultimi errori per `telegram_id`
- Se errore già notificato entro `ADMIN_NOTIFY_MIN_ERROR_INTERVAL_SEC`, aggiornare notifica esistente invece di crearne una nuova
- Oppure batchare errori multipli in un singolo messaggio

**8. Formato messaggi dettagliato**

**Onboarding completato:**
```
🎉 ONBOARDING COMPLETATO

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
🏪 Business: Enoteca X
⏱️ Durata: 5m 12s
🔗 CorrID: abc-123
📅 Timestamp: 2025-11-03 18:42:46 UTC
```

**Inventario caricato:**
```
📦 INVENTARIO IMPORTATO (DAY 0)

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
📄 File: CSV (524 righe, 2 scartate)
⏱️ Tempo: 18.3s
✅ Vini salvati: 522
🔗 CorrID: abc-123
📅 Timestamp: 2025-11-03 18:42:46 UTC
```

**Errore:**
```
🚨 ERRORE

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
📥 Ultimo messaggio: "Carica inventario"
📤 Errore mostrato: "Formato file non valido"
💻 Codice: E_INV_002
📍 Sorgente: processor
🔗 CorrID: abc-123
📅 Timestamp: 2025-11-03 18:42:46 UTC
```

**9. Gestione retry e backoff**

- Primo tentativo: immediato
- Retry 1-3: backoff 10s, 20s, 40s
- Retry 4-6: backoff 80s, 160s, 320s
- Retry 7-10: backoff 600s (10 min)
- Dopo 10 retry: `status='failed'`, logga errore finale

**10. Polling interval**

Il worker deve leggere la tabella ogni **5 secondi** per garantire notifiche in meno di 5s come da requisito.

**11. Gestione Telegram API errors**

- `429 Too Many Requests`: applicare backoff esponenziale
- `400 Bad Request`: log errore, marcare come `failed` (non retry)
- `401 Unauthorized`: log errore critico, fermare bot (token invalido)
- Altri errori: retry con backoff

**12. Isolamento**

Il bot admin deve essere completamente isolato:
- Non condividere codice con bot principale
- Usare solo tabella `admin_notifications` per comunicazione
- Non fare chiamate dirette a processor o bot principale
- Database è l'unica fonte di verità



✅ Criteri di accettazione



Bot privato funzionante solo per l’amministratore



Tutti gli eventi importanti notificati in meno di 5s



Anti-spam operativo



Nessun impatto sui bot pubblici



Tutti i log con correlation\_id

 
 