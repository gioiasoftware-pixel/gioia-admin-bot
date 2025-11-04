# 🧪 Test Gioia Admin Bot

## Come testare il bot prima di collegarlo agli altri servizi

### Prerequisiti

1. ✅ Bot admin configurato su Railway con variabili d'ambiente:
   - `ADMIN_BOT_TOKEN`
   - `ADMIN_CHAT_ID`
   - `DATABASE_URL`
   - `ADMIN_NOTIFY_ENABLED=true`

2. ✅ Bot admin in esecuzione su Railway

3. ✅ Database PostgreSQL accessibile

### Passi per il test

1. **Configura le variabili d'ambiente localmente** (opzionale, se testi in locale):
   ```bash
   # Crea file .env nella cartella Gioiadmin_bot
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Esegui lo script di test**:
   ```bash
   cd Gioiadmin_bot
   python test_admin_bot.py
   ```

3. **Controlla i risultati**:
   - ✅ Lo script inserisce 3 notifiche di test nella tabella `admin_notifications`
   - ✅ Il bot admin dovrebbe processarle entro 5-10 secondi
   - ✅ Controlla il bot Telegram per i messaggi ricevuti
   - ✅ Controlla i log Railway del bot admin per eventuali errori

### Tipi di test

Lo script testa 3 scenari:

1. **Onboarding completato** - Notifica quando un nuovo utente completa l'onboarding
2. **Inventario caricato** - Notifica quando un utente carica un file inventario
3. **Errore** - Notifica quando si verifica un errore nel sistema

### Verifica nel database

Puoi verificare le notifiche nel database:

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

Lo `status` dovrebbe essere:
- `pending` - In attesa di essere processata
- `sent` - Inviata con successo
- `failed` - Invio fallito (dopo retry)

### Troubleshooting

**Il bot non riceve messaggi:**
- Verifica che il bot sia in esecuzione su Railway
- Controlla i log Railway per errori
- Verifica che `ADMIN_BOT_TOKEN` e `ADMIN_CHAT_ID` siano corretti
- Controlla che `ADMIN_NOTIFY_ENABLED=true`

**Errore "DATABASE_URL non configurata":**
- Crea un file `.env` con `DATABASE_URL=...`
- Oppure esporta la variabile: `export DATABASE_URL=...`

**Notifiche rimangono in "pending":**
- Controlla i log del worker per errori
- Verifica che il bot abbia accesso al database
- Controlla che la tabella `admin_notifications` esista

