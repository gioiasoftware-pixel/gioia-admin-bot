# 🔔 Gio.ia Admin Bot

Bot Telegram privato per gestione notifiche admin del sistema Gio.ia.

## 📋 Panoramica

Il **Gio.ia Admin Bot** è un servizio separato che:
- Legge notifiche dalla tabella `admin_notifications` del database PostgreSQL
- Invia notifiche Telegram all'amministratore
- Gestisce rate limiting per evitare spam
- Monitora eventi critici (errori, onboarding completati, ecc.)

## 🏗️ Architettura

```
Database PostgreSQL
  ↓ (tabella admin_notifications)
Gio.ia Admin Bot (worker)
  ↓ (API Telegram)
Amministratore Telegram
```

### Flusso Notifiche

1. **Bot/Processor** inserisce notifica in `admin_notifications`
2. **Admin Bot Worker** legge notifica (status='pending')
3. **Admin Bot** formatta e invia messaggio Telegram
4. **Admin Bot** aggiorna notifica (status='sent' o 'failed')

## 📁 Struttura Progetto

```
Gioiadmin_bot/
├── main.py                    # Entry point, setup bot
├── worker.py                  # Worker per processare notifiche
├── telegram_handler.py        # Handler comandi Telegram
├── templates.py               # Template messaggi notifiche
├── db.py                      # Database connection e utilities
├── models.py                  # Modelli dati (AdminNotification)
├── utils/
│   ├── logging.py            # Logging strutturato
│   ├── rate_limiter.py       # Rate limiting notifiche
│   └── backoff.py            # Exponential backoff per retry
├── migrations/
│   └── 001_create_admin_notifications.sql
├── Procfile                   # Railway deployment
├── railway.json               # Railway config
└── requirements.txt           # Dipendenze Python
```

## 🔧 Configurazione

### Variabili Ambiente

```env
# Telegram Bot Token (bot admin privato)
TELEGRAM_ADMIN_BOT_TOKEN=your_admin_bot_token

# Database PostgreSQL (condiviso con bot e processor)
DATABASE_URL=postgresql://user:pass@host:port/db

# Admin Telegram ID (chi riceve le notifiche)
ADMIN_TELEGRAM_ID=927230913

# Opzionali
LOG_LEVEL=INFO
POLL_INTERVAL=5  # Secondi tra polling notifiche
MAX_RETRIES=3    # Tentativi massimi per notifica
```

### Database

Il bot richiede la tabella `admin_notifications`:

```sql
CREATE TABLE admin_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT now(),
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'failed'
    event_type TEXT NOT NULL,       -- 'onboarding_completed', 'error', ecc.
    telegram_id BIGINT NOT NULL,
    correlation_id TEXT,
    payload JSONB NOT NULL,
    retry_count INTEGER DEFAULT 0,
    next_attempt_at TIMESTAMP DEFAULT now()
);
```

La tabella viene creata automaticamente all'avvio se non esiste (auto-migration).

## 🚀 Deploy

### Railway

1. **Crea nuovo servizio** su Railway
2. **Connetti repository** Git
3. **Configura variabili ambiente:**
   - `TELEGRAM_ADMIN_BOT_TOKEN`
   - `DATABASE_URL`
   - `ADMIN_TELEGRAM_ID`
4. **Deploy automatico** da `main` branch

### Procfile

```
worker: python -m worker
```

Il bot usa **polling** per leggere notifiche dal database.

## 📊 Funzionalità

### Eventi Monitorati

- ✅ **Onboarding Completato:** Notifica quando un utente completa l'onboarding
- ⚠️ **Errori Sistema:** Notifica errori critici dal bot o processor
- 📦 **Upload Inventario:** Notifica quando un inventario viene caricato
- 🔄 **Movimenti Inventario:** Notifica movimenti significativi

### Comandi Telegram

- `/test` - Mostra l'ultima notifica dalla tabella
- `/status` - Mostra stato worker e statistiche
- `/pending` - Mostra notifiche in attesa

### Rate Limiting

- **Globale:** Max 10 notifiche/minuto
- **Per Tipo:** Max 3 notifiche/minuto per tipo evento
- **Per Utente:** Max 1 notifica/2 minuti per utente

### Retry Logic

- **Tentativi:** Max 3 tentativi per notifica
- **Backoff:** Exponential backoff (1s, 2s, 4s)
- **Timeout:** 30 secondi per tentativo

## 🔍 Logging

Il bot usa logging strutturato con:
- **Correlation ID:** Per tracciare notifiche
- **Event Type:** Tipo evento
- **Telegram ID:** ID utente che ha generato l'evento
- **Status:** Stato notifica (pending, sent, failed)

## 🛠️ Sviluppo

### Test Locale

```bash
# Setup ambiente
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configura .env
TELEGRAM_ADMIN_BOT_TOKEN=your_token
DATABASE_URL=postgresql://...
ADMIN_TELEGRAM_ID=927230913

# Avvia worker
python -m worker
```

### Test Database

```python
# Inserisci notifica test
from db import get_db_pool
import json

async def test_notification():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO admin_notifications 
            (event_type, telegram_id, payload, status)
            VALUES ($1, $2, $3, 'pending')
        """, 'test', 123456, json.dumps({"message": "Test notification"}))
```

## 📈 Monitoraggio

### Metriche Importanti

- **Notifiche Processate:** Numero notifiche inviate con successo
- **Notifiche Fallite:** Numero notifiche che hanno fallito dopo retry
- **Tempo Medio Processing:** Tempo medio per processare una notifica
- **Rate Limit Hits:** Numero di volte che rate limiting ha bloccato notifiche

### Health Check

Il bot non ha endpoint HTTP. Verifica stato tramite:
- **Logs Railway:** Controlla che worker stia processando
- **Database:** Controlla tabella `admin_notifications` per notifiche pending
- **Telegram:** Verifica che bot risponda a `/test`

## 🔒 Sicurezza

- **Bot Privato:** Solo amministratore può usare il bot
- **Token Separato:** Token diverso dal bot principale
- **Database Isolato:** Usa stessa DB ma solo tabella `admin_notifications`
- **Rate Limiting:** Previene spam di notifiche

## 🐛 Troubleshooting

### Bot Non Invia Notifiche

1. **Verifica token:** `TELEGRAM_ADMIN_BOT_TOKEN` configurato?
2. **Verifica database:** `DATABASE_URL` corretto?
3. **Verifica notifiche:** Ci sono notifiche `status='pending'`?
4. **Verifica logs:** Worker sta processando?

### Notifiche Duplicate

- **Causa:** Worker avviato più volte
- **Soluzione:** Verifica che solo un worker sia in esecuzione

### Rate Limiting Troppo Aggressivo

- **Causa:** Troppe notifiche in poco tempo
- **Soluzione:** Aumentare limit in `utils/rate_limiter.py`

## 📝 Note

- Il bot è **sempre in esecuzione** (worker continuo)
- Non richiede webhook (solo polling database)
- Compatibile con Railway, Heroku, qualsiasi hosting Python
- Non ha dipendenze da altri servizi (solo database)

## 🔗 Integrazione

### Da Bot/Processor

```python
# Inserisci notifica (esempio da bot)
await enqueue_admin_notification(
    event_type="onboarding_completed",
    telegram_id=user_id,
    payload={
        "business_name": "Nome Locale",
        "user_name": "Nome Utente",
        "stage": "completed"
    },
    correlation_id="uuid-here"
)
```

L'admin bot processerà automaticamente la notifica.

---

**Versione:** 1.0  
**Data:** 2025-11-04  
**Status:** ✅ Funzionante
