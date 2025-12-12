"""
Gioia Admin Bot - Bot Telegram privato per notifiche admin
"""
import os
import asyncio
import logging
import signal
from dotenv import load_dotenv
from db import get_db_pool, close_db_pool, ensure_admin_notifications_table
from worker import start_worker
from telegram_handler import setup_telegram_app
from utils.logging import log_with_context
from logging_config import setup_colored_logging

# Carica variabili d'ambiente da .env (se presente)
load_dotenv()

# Configurazione logging colorato
setup_colored_logging("admin-bot")
logger = logging.getLogger(__name__)

# Flag per graceful shutdown
_shutdown = False


def signal_handler(signum, frame):
    """Gestione segnali per shutdown graceful"""
    global _shutdown
    logger.info(f"Ricevuto segnale {signum}, shutdown graceful...")
    _shutdown = True


async def startup():
    """Inizializzazione all'avvio"""
    logger.info("🚀 Gioia Admin Bot - Avvio...")
    
    # Verifica variabili ambiente
    admin_bot_token = os.getenv("ADMIN_BOT_TOKEN")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    admin_notify_enabled = os.getenv("ADMIN_NOTIFY_ENABLED", "true").lower() == "true"
    
    if not admin_bot_token:
        logger.error("❌ ADMIN_BOT_TOKEN non configurato")
        raise ValueError("ADMIN_BOT_TOKEN richiesto")
    
    if not admin_chat_id:
        logger.error("❌ ADMIN_CHAT_ID non configurato")
        raise ValueError("ADMIN_CHAT_ID richiesto")
    
    if not admin_notify_enabled:
        logger.warning("⚠️ ADMIN_NOTIFY_ENABLED=false - Bot disabilitato")
        return False
    
    logger.info(f"✅ Configurazione validata:")
    logger.info(f"   ADMIN_BOT_TOKEN: {'*' * 20}...{admin_bot_token[-4:]}")
    logger.info(f"   ADMIN_CHAT_ID: {admin_chat_id}")
    logger.info(f"   ADMIN_NOTIFY_ENABLED: {admin_notify_enabled}")
    
    # Inizializza database
    try:
        await get_db_pool()
        logger.info("✅ Pool database inizializzato")
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        raise
    
    # Esegui auto-migration
    try:
        await ensure_admin_notifications_table()
        logger.info("✅ Tabella admin_notifications verificata/creata")
    except Exception as e:
        logger.error(f"❌ Errore creazione tabella: {e}")
        raise
    
    logger.info("✅ Startup completato")
    return True


async def shutdown():
    """Cleanup allo shutdown"""
    logger.info("🛑 Shutdown graceful...")
    
    try:
        await close_db_pool()
        logger.info("✅ Database chiuso")
    except Exception as e:
        logger.error(f"Errore chiusura database: {e}")
    
    logger.info("✅ Shutdown completato")


async def main():
    """Entrypoint principale"""
    global _shutdown
    
    # Registra signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Startup
        if not await startup():
            logger.info("Bot disabilitato (ADMIN_NOTIFY_ENABLED=false)")
            return
        
        log_with_context("info", "Bot admin avviato e pronto")
        
        # Recupera token per Telegram bot
        admin_bot_token = os.getenv("ADMIN_BOT_TOKEN")
        
        # Setup Telegram bot per comandi
        telegram_app = setup_telegram_app(admin_bot_token)
        
        # Inizializza bot
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Verifica se siamo su Railway (usa webhook) o locale (usa polling)
        # Railway setta sempre PORT e RAILWAY_ENVIRONMENT
        is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None or os.getenv("PORT") is not None
        use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"
        
        if is_railway and not use_webhook:
            # Su Railway, prova prima a rimuovere eventuali webhook esistenti
            # Poi usa polling con gestione conflitti migliorata
            max_webhook_retries = 3
            for attempt in range(max_webhook_retries):
                try:
                    webhook_info = await telegram_app.bot.get_webhook_info()
                    logger.info(f"[WEBHOOK_CHECK] Tentativo {attempt + 1}: webhook_url={webhook_info.url}, pending_updates={webhook_info.pending_update_count}")
                    
                    if webhook_info.url:
                        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
                        logger.info(f"✅ Webhook rimosso: {webhook_info.url}")
                        await asyncio.sleep(3)  # Aspetta di più per assicurarsi che la rimozione sia completata
                    else:
                        logger.info("✅ Nessun webhook configurato")
                        break
                except Exception as webhook_error:
                    logger.warning(f"⚠️ Errore rimozione webhook (tentativo {attempt + 1}): {webhook_error}")
                    if attempt < max_webhook_retries - 1:
                        await asyncio.sleep(3)
            
            # Aspetta un po' prima di avviare polling per evitare conflitti con altre istanze
            await asyncio.sleep(5)
            logger.info("⏳ Attesa 5 secondi prima di avviare polling per evitare conflitti...")
        
        # Avvia polling Telegram in background
        # Usa allowed_updates per limitare solo ai messaggi (non callback_query per ora)
        try:
            await telegram_app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message"]  # Solo messaggi, inclusi documenti
            )
            logger.info("✅ Telegram bot polling avviato")
        except Exception as polling_error:
            logger.error(f"❌ Errore avvio polling: {polling_error}")
            # Se c'è un conflitto, aspetta e riprova
            if "Conflict" in str(polling_error):
                logger.warning("⚠️ Conflitto rilevato, attendo 10 secondi e riprovo...")
                await asyncio.sleep(10)
                await telegram_app.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message"]
                )
                logger.info("✅ Telegram bot polling avviato dopo retry")
            else:
                raise
        
        # Avvia worker in background
        worker_task = asyncio.create_task(start_worker())
        
        # Attendi shutdown o errore
        try:
            await worker_task
        except asyncio.CancelledError:
            logger.info("Worker cancellato")
        except Exception as e:
            logger.error(f"Errore nel worker: {e}")
            raise
        finally:
            # Stop Telegram bot
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("✅ Telegram bot fermato")
        
    except KeyboardInterrupt:
        logger.info("Interruzione da utente")
    except Exception as e:
        logger.error(f"Errore critico: {e}")
        raise
    finally:
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrotto")
    except Exception as e:
        logger.error(f"Errore fatale: {e}")
        exit(1)




