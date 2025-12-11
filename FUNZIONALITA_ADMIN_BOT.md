# 📋 Gioia Admin Bot - Funzionalità e Come Funziona

**Versione**: 1.0  
**Data**: 2025-01-XX  
**Scopo**: Bot Telegram privato per notifiche amministrative

---

## 🎯 Obiettivo Principale

Il **Gioia Admin Bot** è un bot Telegram privato dedicato all'amministratore per ricevere notifiche automatiche su eventi importanti del sistema.

---

## 📊 Funzionalità Principali

### **1. Comandi Admin** 🤖

Il bot supporta comandi per operazioni amministrative:

#### **Invio Messaggi:**
- `/all <messaggio>` - Invia messaggio a tutti gli utenti con onboarding completato
- `/<telegram_id> <messaggio>` - Invia messaggio a un utente specifico

#### **Report Giornaliero:**
- `/report` - Invia report consumi/rifornimenti a tutti gli utenti (data: ieri)
- `/report <telegram_id>` - Invia report a un utente specifico (data: ieri)
- `/report <telegram_id> <data>` - Invia report a un utente per una data specifica (formato: YYYY-MM-DD)

**Esempi:**
```
/report
/report 927230913
/report 927230913 2025-12-10
```

**Nota:** Il comando `/report` è utile per testare il report giornaliero senza aspettare le 10 del mattino.

---

### **2. Notifiche di Onboarding Completato** 🎉

Quando un nuovo utente completa l'onboarding:

**Cosa ricevi:**
```
🎉 ONBOARDING COMPLETATO

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
🏪 Business: Enoteca X
📊 Stato: ✅ Completato
⏱️ Durata: 5m 12s
🔗 CorrID: abc-123
📅 Timestamp: 2025-01-15 18:42:46 UTC
```

**Informazioni incluse:**
- Telegram ID utente
- Nome completo (se disponibile)
- Username Telegram (se disponibile)
- Nome business/locale
- Durata onboarding
- Correlation ID per tracciamento
- Timestamp evento

---

### **3. Notifiche di Inventario Caricato** 📦

Quando un utente carica un inventario:

**Cosa ricevi:**
```
📦 INVENTARIO IMPORTATO (DAY 0)

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
📄 File: CSV (524 righe, 2 scartate)
⏱️ Tempo: 18.3s
✅ Vini salvati: 522
🔗 CorrID: abc-123
📅 Timestamp: 2025-01-15 18:42:46 UTC
```

**Informazioni incluse:**
- Telegram ID utente
- Nome completo e username
- Tipo file (CSV, Excel, foto)
- Righe processate
- Righe scartate/rifiutate
- Tempo di elaborazione
- Numero vini salvati
- Correlation ID
- Timestamp

---

### **4. Notifiche di Errori** 🚨

Quando si verifica un errore che viene mostrato all'utente:

**Cosa ricevi:**
```
🚨 ERRORE

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
📥 Ultimo messaggio: "Carica inventario"
📤 Errore mostrato: "Formato file non valido"
💻 Dettaglio: [dettaglio tecnico se disponibile]
💻 Codice: E_INV_002
📍 Sorgente: processor
🔗 CorrID: abc-123
📅 Timestamp: 2025-01-15 18:42:46 UTC
```

**Informazioni incluse:**
- Telegram ID utente
- Ultimo messaggio inviato dall'utente
- Errore mostrato all'utente
- Dettaglio tecnico (se diverso da errore utente)
- Codice errore standardizzato
- Sorgente (bot o processor)
- Correlation ID
- Timestamp

---

### **4. Notifiche Batch Errori** 🚨📊

Se lo stesso utente ha più errori in rapida successione:

**Cosa ricevi:**
```
🚨 ERRORI MULTIPLI

👤 Utente: 123456789 — Mario Rossi (@mariorossi)
📊 Errori accumulati: 3

1. Formato file non valido
   Codice: E_INV_002
2. Errore database
   Codice: E_BOT_002
3. Timeout elaborazione
   Codice: E_PROC_003

🔗 CorrID: abc-123, def-456, ghi-789
📅 Timestamp: 2025-01-15 18:42:46 UTC
```

**Funzionalità:**
- Raggruppa fino a 5 errori per utente
- Evita spam di notifiche
- Mostra tutti i correlation ID

---

## ⚙️ Come Funziona

### **Architettura**

```
┌─────────────────┐
│ telegram-ai-bot │
│  gioia-processor│
└────────┬────────┘
         │
         │ INSERT INTO admin_notifications
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │
│ admin_notifications│
└────────┬────────┘
         │
         │ SELECT status='pending'
         │
         ▼
┌─────────────────┐
│  Admin Bot      │
│  (Worker Loop)  │
└────────┬────────┘
         │
         │ sendMessage
         │
         ▼
┌─────────────────┐
│  Telegram       │
│  Admin Chat     │
└─────────────────┘
```

---

### **Flusso Dettagliato**

#### **1. Generazione Evento**

Quando accade un evento importante (onboarding, upload, errore), il servizio (bot o processor) inserisce un record nella tabella `admin_notifications`:

```sql
INSERT INTO admin_notifications
    (event_type, telegram_id, payload, correlation_id, status, next_attempt_at)
VALUES
    ('onboarding_completed', 123456789, '{"business_name":"Enoteca X"}', 'abc-123', 'pending', NOW())
```

#### **2. Worker Loop**

Il bot admin esegue un loop continuo che:
- **Ogni 5 secondi** legge la tabella `admin_notifications`
- Cerca record con `status='pending'` e `next_attempt_at <= NOW()`
- Processa fino a 20 notifiche per ciclo

#### **3. Rate Limiting**

Prima di inviare, verifica:
- **Limite globale**: Max 20 notifiche/minuto (configurabile)
- **Anti-spam per utente**: Max 1 errore ogni 180 secondi per utente (configurabile)

#### **4. Formattazione Messaggio**

Il bot recupera informazioni utente dal database (`users` table) e formatta il messaggio usando template specifici per tipo evento.

#### **5. Invio Telegram**

Invia il messaggio all'admin chat usando Telegram Bot API.

#### **6. Aggiornamento Status**

- **Successo**: `status='sent'`
- **Errore**: `retry_count++`, `next_attempt_at=now()+backoff`, `status='pending'`
- **Max retry raggiunto**: `status='failed'`

---

## 🔧 Configurazione

### **Variabili Ambiente Obbligatorie**

```env
# Token bot Telegram admin
ADMIN_BOT_TOKEN=8455675311:AAHkwtkB3W4o8TQ8taEilu8XQ3Z51YPvSFU

# Chat ID admin (dove ricevere notifiche)
ADMIN_CHAT_ID=987654321

# Token bot Telegram principale (per inviare messaggi agli utenti)
TELEGRAM_BOT_TOKEN=your_telegram_ai_bot_token_here

# URL API del processor (per chiamate admin, opzionale)
PROCESSOR_API_URL=https://gioia-processor-production.up.railway.app

# Database condiviso
DATABASE_URL=postgresql://user:pass@host:port/db
```

### **Variabili Opzionali**

```env
# Abilita/disabilita bot (default: true)
ADMIN_NOTIFY_ENABLED=true

# Rate limit globale (default: 20/minuto)
ADMIN_NOTIFY_RATE_LIMIT_PER_MIN=20

# Intervallo minimo tra errori stesso utente (default: 180 secondi)
ADMIN_NOTIFY_MIN_ERROR_INTERVAL_SEC=180

# Max tentativi retry (default: 10)
ADMIN_MAX_RETRY=10

# Base backoff per retry (default: 10 secondi)
ADMIN_BACKOFF_BASE=10
```

---

## 📋 Tipi di Eventi Supportati

### **1. `onboarding_completed`**

**Quando**: Utente completa onboarding  
**Payload**:
```json
{
  "business_name": "Enoteca X",
  "duration_seconds": 312,
  "stage": "completed",
  "inventory_pending": false
}
```

---

### **2. `inventory_uploaded`**

**Quando**: Utente carica inventario con successo  
**Payload**:
```json
{
  "file_type": "csv",
  "rows_processed": 524,
  "rows_rejected": 2,
  "wines_saved": 522,
  "processing_time": 18.3
}
```

---

### **3. `error`**

**Quando**: Si verifica un errore mostrato all'utente  
**Payload**:
```json
{
  "last_user_message": "Carica inventario",
  "user_visible_error": "Formato file non valido",
  "error_message": "File parsing failed: invalid CSV format",
  "error_code": "E_INV_002",
  "source": "processor"
}
```

---

## 🛡️ Rate Limiting e Anti-Spam

### **Rate Limit Globale**

- **Limite**: 20 notifiche/minuto (configurabile)
- **Scopo**: Evitare rate limiting Telegram API
- **Comportamento**: Se limite raggiunto, notifica rimane `pending` e viene riprovata al ciclo successivo

### **Anti-Spam per Utente**

- **Limite**: 1 errore ogni 180 secondi per utente (configurabile)
- **Scopo**: Evitare spam di errori dello stesso utente
- **Comportamento**: Se errore già notificato recentemente, notifica viene marcata come `sent` ma non inviata (batching futuro)

---

## 🔄 Retry e Backoff

### **Strategia Retry**

Il bot implementa retry automatico con backoff esponenziale:

- **Retry 1-3**: 10s, 20s, 40s
- **Retry 4-6**: 80s, 160s, 320s
- **Retry 7-10**: 600s (10 minuti)
- **Dopo 10 retry**: `status='failed'`, non più tentativi

### **Gestione Errori Telegram API**

- **429 Too Many Requests**: Backoff esponenziale, retry
- **400 Bad Request**: Marca come `failed` (non retry)
- **401 Unauthorized**: Errore critico, ferma bot
- **Altri errori**: Retry con backoff

---

## 📊 Database Schema

### **Tabella `admin_notifications`**

```sql
CREATE TABLE admin_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT now(),
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'failed'
    event_type TEXT NOT NULL,       -- 'onboarding_completed', 'inventory_uploaded', 'error'
    telegram_id BIGINT NOT NULL,
    correlation_id TEXT,
    payload JSONB NOT NULL,
    retry_count INTEGER DEFAULT 0,
    next_attempt_at TIMESTAMP DEFAULT now()
);
```

### **Indici**

- `idx_admin_pending`: Su `(status, next_attempt_at)` per query veloci
- `idx_admin_user_created`: Su `(telegram_id, created_at DESC)` per ricerca utente
- `idx_admin_correlation`: Su `correlation_id` per tracciamento

---

## 🚀 Avvio e Funzionamento

### **Avvio Automatico**

Il bot:
1. Verifica variabili ambiente
2. Connette al database PostgreSQL
3. Esegue auto-migration (crea tabella se non esiste)
4. Avvia worker loop
5. Avvia Telegram bot polling (per comandi futuri)

### **Worker Loop**

Il worker esegue continuamente:
1. Query notifiche `pending` con `next_attempt_at <= NOW()`
2. Per ogni notifica:
   - Verifica rate limit
   - Formatta messaggio
   - Invia via Telegram
   - Aggiorna status
3. Attende 5 secondi prima del prossimo ciclo

---

## 📝 Logging

Tutti gli eventi sono loggati con:
- **Correlation ID**: Per tracciare eventi correlati
- **Notification ID**: Per identificare singole notifiche
- **Event Type**: Tipo evento
- **Telegram ID**: Utente coinvolto

**Esempio log:**
```
[INFO] Notifica 123 processata con successo
  correlation_id=abc-123
  notification_id=123
  event_type=onboarding_completed
```

---

## 🔍 Monitoraggio

### **Metriche Disponibili**

- Numero notifiche inviate/minuto
- Numero notifiche fallite
- Numero retry eseguiti
- Tempo medio elaborazione

### **Stati Notifiche**

- **`pending`**: In attesa di invio
- **`sent`**: Inviata con successo
- **`failed`**: Fallita dopo max retry

---

## ⚠️ Limitazioni e Considerazioni

### **Limitazioni**

- **Polling interval**: 5 secondi (non real-time)
- **Batch size**: Max 20 notifiche per ciclo
- **Rate limit**: 20 notifiche/minuto globale
- **Anti-spam**: 1 errore ogni 180s per utente

### **Considerazioni**

- Il bot è **isolato** dagli altri servizi
- Comunica solo tramite database
- Non fa chiamate dirette a bot/processor
- Database è l'unica fonte di verità

---

## 🧪 Test

### **Test Manuali**

1. **Onboarding**: Completa onboarding nuovo utente → Verifica notifica
2. **Upload**: Carica inventario → Verifica notifica
3. **Errore**: Genera errore → Verifica notifica
4. **Rate limit**: Genera molti eventi rapidamente → Verifica rate limiting
5. **Retry**: Simula errore Telegram → Verifica retry

---

## 📚 Integrazione con Altri Servizi

### **Come Altri Servizi Inseriscono Notifiche**

I servizi (`telegram-ai-bot` e `gioia-processor`) inseriscono notifiche nella tabella condivisa usando helper comune:

```python
await enqueue_admin_notification(
    event_type="error",
    telegram_id=user.telegram_id,
    correlation_id=corr_id,
    payload={
        "last_user_message": message_text,
        "user_visible_error": user_error,
        "source": "bot",
        "error_code": "E_BOT_001"
    }
)
```

Il bot admin pensa al resto automaticamente.

---

## ✅ Checklist Funzionalità

- [x] Notifiche onboarding completato
- [x] Notifiche inventario caricato
- [x] Notifiche errori
- [x] Rate limiting globale
- [x] Anti-spam per utente
- [x] Retry automatico con backoff
- [x] Auto-migration database
- [x] Logging strutturato
- [x] Gestione errori Telegram API
- [x] Isolamento da altri servizi

---

**Versione**: 1.0  
**Autore**: Sistema Admin Bot  
**Data**: 2025-01-XX

