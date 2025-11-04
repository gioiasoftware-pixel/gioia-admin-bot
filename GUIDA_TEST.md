# 🧪 Guida Test Bot Admin su Railway - Passo per Passo

## 📋 Checklist Pre-Test

### ✅ Step 1: Verifica Bot in Esecuzione su Railway

1. Vai su [Railway Dashboard](https://railway.app)
2. Apri il progetto che contiene `gioia-admin-bot`
3. Apri il servizio `gioia-admin-bot`
4. Vai alla tab **"Deployments"**
5. Verifica che l'ultimo deployment sia **"Active"** ✅
6. Vai alla tab **"Logs"**
7. Cerca questi messaggi:
   ```
   ✅ Configurazione validata
   ✅ Pool database inizializzato
   ✅ Tabella admin_notifications verificata/creata
   Bot admin avviato e pronto
   ```

### ✅ Step 2: Verifica Variabili d'Ambiente

1. Nel servizio Railway, vai alla tab **"Variables"**
2. Verifica che esistano e siano configurate:
   - ✅ `ADMIN_BOT_TOKEN` (es: `1234567890:ABCdef...`)
   - ✅ `ADMIN_CHAT_ID` (es: `123456789`)
   - ✅ `DATABASE_URL` (es: `postgresql://...`)
   - ✅ `ADMIN_NOTIFY_ENABLED` (opzionale, default `true`)

### ✅ Step 3: Test da Locale (Opzione 1 - Consigliata)

**Prerequisiti:**
- Python 3.8+ installato
- Accesso al database PostgreSQL (stesso del Railway)

**Passi:**

1. **Apri terminale e vai nella cartella:**
   ```bash
   cd "C:\Users\giova\OneDrive\Documenti\gio.ia\Gio.iaPROD\Gioiadmin_bot"
   ```

2. **Crea file `.env` con DATABASE_URL:**
   ```bash
   # Copia DATABASE_URL da Railway Variables
   # Crea file .env nella cartella Gioiadmin_bot
   ```
   File `.env`:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Installa dipendenze (se non già installate):**
   ```bash
   pip install asyncpg python-dotenv
   ```

4. **Esegui test:**
   ```bash
   python test_admin_bot.py
   ```

5. **Risultato atteso:**
   ```
   🧪 Test Gioia Admin Bot
   ==================================================
   
   📝 Inserimento notifica di test...
      Event Type: onboarding_completed
      Telegram ID: 123456789
   ✅ Notifica inserita con ID: ...
      Il bot admin dovrebbe processarla entro pochi secondi
   ```

6. **Controlla bot Telegram** - Dovresti ricevere 3 messaggi entro 10 secondi

### ✅ Step 4: Test da Railway (Opzione 2)

**Usa Railway CLI o One-off Container:**

1. **Installa Railway CLI** (se non già installato):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Link al progetto:**
   ```bash
   railway link
   ```

4. **Esegui test come one-off container:**
   ```bash
   railway run python test_admin_bot.py
   ```

   **Oppure via SSH:**
   - Vai su Railway → Servizio → Tab "Settings"
   - Clicca "Generate SSH Command"
   - Esegui il comando SSH
   - Una volta dentro il container:
     ```bash
     cd /app
     python test_admin_bot.py
     ```

### ✅ Step 5: Verifica Risultati

**1. Controlla bot Telegram:**
   - Apri il bot admin su Telegram
   - Dovresti vedere 3 messaggi:
     - 🎉 Onboarding completato
     - 📦 Inventario caricato  
     - 🚨 Errore

**2. Controlla log Railway:**
   - Vai su Railway → Servizio → Tab "Logs"
   - Cerca:
     ```
     Processing notification: ...
     Notification sent successfully
     ```

**3. Verifica database (opzionale):**
   ```sql
   SELECT 
       id,
       created_at,
       status,
       event_type,
       telegram_id,
       retry_count
   FROM admin_notifications
   ORDER BY created_at DESC
   LIMIT 10;
   ```
   
   Lo `status` dovrebbe essere `sent` per le notifiche di test.

## 🔍 Troubleshooting

### ❌ "DATABASE_URL non configurata"
- **Soluzione:** Crea file `.env` con `DATABASE_URL=...`

### ❌ "Bot non riceve messaggi"
- Verifica che il bot sia in esecuzione su Railway
- Controlla log Railway per errori
- Verifica `ADMIN_BOT_TOKEN` e `ADMIN_CHAT_ID` corretti

### ❌ "Notifiche rimangono in pending"
- Controlla log Railway del worker
- Verifica che la tabella `admin_notifications` esista
- Controlla che il bot abbia accesso al database

### ❌ "Errore connessione database"
- Verifica che `DATABASE_URL` sia corretto
- Controlla che il database sia accessibile dalla tua rete
- Se usi Railway, il database potrebbe essere accessibile solo da Railway stesso

## ✅ Test Completato con Successo

Se vedi i 3 messaggi nel bot Telegram, il test è **completato con successo**! 🎉

Ora puoi procedere con l'integrazione del bot admin negli altri servizi (telegram-ai-bot e gioia-processor).

