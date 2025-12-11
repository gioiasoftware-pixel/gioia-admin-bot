"""
Handler Telegram per admin bot
"""
import os
import logging
import httpx
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from db import get_db_pool
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Token del telegram-ai-bot per inviare messaggi agli utenti
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def get_all_users() -> List[Dict[str, Any]]:
    """Recupera tutti gli utenti dal database"""
    pool = await get_db_pool()
    users = []
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT telegram_id, username, first_name, last_name, business_name, onboarding_completed
            FROM users
            WHERE onboarding_completed = true
            ORDER BY telegram_id
        """)
        
        for row in rows:
            users.append({
                "telegram_id": row["telegram_id"],
                "username": row.get("username"),
                "first_name": row.get("first_name"),
                "last_name": row.get("last_name"),
                "business_name": row.get("business_name"),
                "onboarding_completed": row.get("onboarding_completed", False)
            })
    
    return users


async def get_user_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """Recupera un utente specifico dal database"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT telegram_id, username, first_name, last_name, business_name, onboarding_completed
            FROM users
            WHERE telegram_id = $1
        """, telegram_id)
        
        if row:
            return {
                "telegram_id": row["telegram_id"],
                "username": row.get("username"),
                "first_name": row.get("first_name"),
                "last_name": row.get("last_name"),
                "business_name": row.get("business_name"),
                "onboarding_completed": row.get("onboarding_completed", False)
            }
    
    return None


async def send_message_to_user(telegram_id: int, message: str) -> Dict[str, Any]:
    """
    Invia un messaggio a un utente tramite telegram-ai-bot.
    
    Args:
        telegram_id: ID Telegram dell'utente destinatario
        message: Messaggio da inviare
    
    Returns:
        Dict con status e eventuale errore
    """
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "error", "error": "TELEGRAM_BOT_TOKEN non configurato"}
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            return {"status": "sent", "telegram_id": telegram_id}
    
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"Errore invio messaggio a {telegram_id}: {error_msg}")
        return {"status": "error", "error": error_msg, "telegram_id": telegram_id}
    
    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        logger.error(f"Errore invio messaggio a {telegram_id}: {error_msg}", exc_info=True)
        return {"status": "error", "error": error_msg, "telegram_id": telegram_id}


async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /all - invia messaggio a tutti gli utenti"""
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    
    # Verifica che il comando venga da admin
    if str(update.effective_user.id) != str(admin_chat_id):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo comando.")
        return
    
    # Estrai messaggio (tutto dopo /all)
    if not context.args:
        await update.message.reply_text(
            "📢 **Invio Messaggio a Tutti**\n\n"
            "Uso: `/all <messaggio>`\n\n"
            "Esempio: `/all Ciao a tutti! Questo è un messaggio di test.`",
            parse_mode='Markdown'
        )
        return
    
    message_text = " ".join(context.args)
    
    if not message_text.strip():
        await update.message.reply_text("❌ Messaggio vuoto. Usa: `/all <messaggio>`", parse_mode='Markdown')
        return
    
    # Conferma invio
    await update.message.reply_text(
        f"⏳ **Invio in corso...**\n\n"
        f"Messaggio: {message_text[:100]}{'...' if len(message_text) > 100 else ''}\n\n"
        f"Recupero lista utenti..."
    )
    
    try:
        # Recupera tutti gli utenti
        users = await get_all_users()
        
        if not users:
            await update.message.reply_text("❌ Nessun utente trovato nel database.")
            return
        
        # Invia messaggio a tutti gli utenti
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        for user in users:
            result = await send_message_to_user(user["telegram_id"], message_text)
            
            if result["status"] == "sent":
                sent_count += 1
            else:
                failed_count += 1
                failed_users.append({
                    "telegram_id": user["telegram_id"],
                    "business_name": user.get("business_name", "N/A"),
                    "error": result.get("error", "Errore sconosciuto")
                })
        
        # Report finale
        report = (
            f"✅ **Invio Completato**\n\n"
            f"📊 **Statistiche:**\n"
            f"• ✅ Inviati: {sent_count}/{len(users)}\n"
            f"• ❌ Falliti: {failed_count}/{len(users)}\n\n"
        )
        
        if failed_users:
            report += f"**Errori:**\n"
            for failed in failed_users[:5]:  # Max 5 errori
                report += f"• ID {failed['telegram_id']} ({failed['business_name']}): {failed['error'][:50]}\n"
            if len(failed_users) > 5:
                report += f"\n... e altri {len(failed_users) - 5} errori"
        
        await update.message.reply_text(report, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Errore comando /all: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Errore durante l'invio**\n\n"
            f"Errore: {str(e)[:200]}"
        )


async def user_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /<telegram_id> - invia messaggio a un utente specifico"""
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    
    # Verifica che il comando venga da admin
    if str(update.effective_user.id) != str(admin_chat_id):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo comando.")
        return
    
    # Estrai telegram_id dal comando (es. /927230913)
    command = update.message.text.split()[0]  # Prendi solo il comando
    telegram_id_str = command.lstrip('/')
    
    try:
        telegram_id = int(telegram_id_str)
    except ValueError:
        await update.message.reply_text(
            "❌ **ID non valido**\n\n"
            "Uso: `/<telegram_id> <messaggio>`\n\n"
            "Esempio: `/927230913 Ciao! Questo è un messaggio per te.`",
            parse_mode='Markdown'
        )
        return
    
    # Estrai messaggio
    if not context.args:
        await update.message.reply_text(
            f"📨 **Invio Messaggio a Utente**\n\n"
            f"ID: `{telegram_id}`\n\n"
            f"Uso: `/{telegram_id} <messaggio>`\n\n"
            f"Esempio: `/{telegram_id} Ciao! Questo è un messaggio per te.`",
            parse_mode='Markdown'
        )
        return
    
    message_text = " ".join(context.args)
    
    if not message_text.strip():
        await update.message.reply_text(f"❌ Messaggio vuoto. Usa: `/{telegram_id} <messaggio>`", parse_mode='Markdown')
        return
    
    # Verifica che l'utente esista
    try:
        user = await get_user_by_telegram_id(telegram_id)
        
        if not user:
            await update.message.reply_text(
                f"❌ **Utente non trovato**\n\n"
                f"ID Telegram `{telegram_id}` non esiste nel database."
            )
            return
        
        # Mostra info utente
        user_info = f"ID: {telegram_id}"
        if user.get("business_name"):
            user_info += f"\nBusiness: {user['business_name']}"
        if user.get("first_name") or user.get("last_name"):
            name_parts = [p for p in [user.get("first_name"), user.get("last_name")] if p]
            user_info += f"\nNome: {' '.join(name_parts)}"
        if user.get("username"):
            user_info += f"\nUsername: @{user['username']}"
        
        await update.message.reply_text(
            f"⏳ **Invio messaggio...**\n\n"
            f"👤 **Utente:**\n{user_info}\n\n"
            f"📝 **Messaggio:**\n{message_text[:200]}{'...' if len(message_text) > 200 else ''}"
        )
        
        # Invia messaggio
        result = await send_message_to_user(telegram_id, message_text)
        
        if result["status"] == "sent":
            await update.message.reply_text(
                f"✅ **Messaggio inviato con successo**\n\n"
                f"👤 Utente: `{telegram_id}`\n"
                f"📝 Messaggio: {message_text[:100]}{'...' if len(message_text) > 100 else ''}",
                parse_mode='Markdown'
            )
        else:
            error_msg = result.get("error", "Errore sconosciuto")
            await update.message.reply_text(
                f"❌ **Errore durante l'invio**\n\n"
                f"👤 Utente: `{telegram_id}`\n"
                f"❌ Errore: {error_msg[:200]}",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        logger.error(f"Errore comando /{telegram_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Errore durante l'invio**\n\n"
            f"Errore: {str(e)[:200]}"
        )


async def start_admin_cmd(update, context):
    """Comando /start per l'admin bot."""
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    
    # Verifica che il comando venga da admin
    if str(update.effective_user.id) != str(admin_chat_id):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo bot.")
        return
    
    help_text = (
        "🤖 **Gioia Admin Bot**\n\n"
        "**Comandi disponibili:**\n\n"
        "📢 **Invio Messaggi:**\n"
        "• `/all <messaggio>` - Invia messaggio a tutti gli utenti\n"
        "• `/<telegram_id> <messaggio>` - Invia messaggio a un utente specifico\n\n"
        "**Esempi:**\n"
        "• `/all Ciao a tutti! Questo è un messaggio di test.`\n"
        "• `/927230913 Ciao! Questo è un messaggio per te.`\n\n"
        "💡 Riceverai qui le notifiche automatiche del sistema."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


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
    
    # Aggiungi handler per comandi
    app.add_handler(CommandHandler("start", start_admin_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    
    # Handler per comandi numerici (telegram_id) - cattura messaggi che iniziano con / seguito da numero
    async def handle_numeric_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce comandi numerici come /927230913"""
        # Verifica che sia un comando numerico
        command_text = update.message.text.split()[0] if update.message.text else ""
        if command_text.startswith('/') and command_text[1:].isdigit():
            await user_id_cmd(update, context)
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/\d+'), handle_numeric_command))
    
    logger.info("✅ Telegram bot configurato con comandi /all e /<telegram_id>")
    
    return app
