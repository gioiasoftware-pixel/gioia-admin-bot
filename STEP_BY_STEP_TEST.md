# 🧪 Test Bot Admin - Passo per Passo

## ⚡ Quick Start (5 minuti)

### STEP 1: Verifica Bot Attivo ✅

**Cosa fare:**
1. Vai su Railway Dashboard → Progetto → Servizio `gioia-admin-bot`
2. Tab **"Deployments"** → Verifica status "Active" ✅
3. Tab **"Logs"** → Cerca: `✅ Bot admin avviato e pronto`

**Dimmi:** Vedi il bot attivo e i log di avvio?

---

### STEP 2: Verifica Variabili ✅

**Cosa fare:**
1. Tab **"Variables"** nel servizio Railway
2. Verifica che esistano:
   - `ADMIN_BOT_TOKEN` ✅
   - `ADMIN_CHAT_ID` ✅
   - `DATABASE_URL` ✅

**Dimmi:** Hai tutte e 3 le variabili configurate?

---

### STEP 3: Prepara Test Locale ✅

**Cosa fare:**
1. Apri terminale nella cartella `Gioiadmin_bot`
2. Crea file `.env` con:
   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```
   (Copia DATABASE_URL da Railway Variables)

**Dimmi:** Hai il file `.env` pronto con DATABASE_URL?

---

### STEP 4: Esegui Test ✅

**Cosa fare:**
```bash
cd "C:\Users\giova\OneDrive\Documenti\gio.ia\Gio.iaPROD\Gioiadmin_bot"
python test_admin_bot.py
```

**Dimmi:** Cosa vedi nell'output? Ci sono errori?

---

### STEP 5: Verifica Telegram ✅

**Cosa fare:**
1. Apri il bot admin su Telegram
2. Aspetta 5-10 secondi
3. Dovresti ricevere 3 messaggi:
   - 🎉 Onboarding completato
   - 📦 Inventario caricato
   - 🚨 Errore

**Dimmi:** Hai ricevuto i messaggi?

---

## ✅ Test Completato!

Se vedi i 3 messaggi, il bot funziona! 🎉

