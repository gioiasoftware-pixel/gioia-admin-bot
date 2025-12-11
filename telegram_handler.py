"""
Handler Telegram per admin bot
"""
import logging
from telegram.ext import Application

logger = logging.getLogger(__name__)


def setup_telegram_app(bot_token: str) -> Application:
    """
    Crea e configura applicazione Telegram bot.
    
    Args:
        bot_token: Token del bot Telegram
    
    Returns:
        Application configurata
    """
    if not bot_token:
        raise ValueError("Bot token richiesto")
    
    logger.info("Configurazione Telegram bot...")
    
    # Crea applicazione
    app = Application.builder().token(bot_token).build()
    
    logger.info("✅ Telegram bot configurato")
    
    return app
