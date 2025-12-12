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

# URL del processor per chiamate API (usa PROCESSOR_URL se disponibile, altrimenti default)
def _normalize_processor_url(url: str) -> str:
    """Normalizza URL aggiungendo https:// se manca il protocollo"""
    if not url:
        return "https://gioia-processor-production.up.railway.app"
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url

_processor_url_raw = os.getenv("PROCESSOR_URL") or os.getenv("PROCESSOR_API_URL", "https://gioia-processor-production.up.railway.app")
PROCESSOR_API_URL = _normalize_processor_url(_processor_url_raw)


async def get_all_users() -> List[Dict[str, Any]]:
    """Recupera tutti gli utenti dal database"""
    pool = await get_db_pool()
    users = []
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT telegram_id, username, first_name, last_name, business_name, onboarding_completed
            FROM users
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


def is_authorized(update: Update) -> bool:
    """
    Verifica se l'utente/canale è autorizzato a usare i comandi admin.
    
    Supporta:
    - Utente privato (ADMIN_CHAT_ID = telegram_id utente)
    - Canale/Gruppo (ADMIN_CHAT_ID = chat_id canale/gruppo, negativo)
    - Tutti i membri del canale/gruppo possono usare i comandi
    """
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if not admin_chat_id:
        return False
    
    # Se ADMIN_CHAT_ID è negativo, è un canale/gruppo
    try:
        admin_chat_id_int = int(admin_chat_id)
        is_channel_or_group = admin_chat_id_int < 0
    except ValueError:
        is_channel_or_group = False
    
    if is_channel_or_group:
        # Verifica che il messaggio venga dal canale/gruppo configurato
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id and str(chat_id) == str(admin_chat_id):
            # Permetti a tutti i membri del canale/gruppo di usare i comandi
            return True
        return False
    else:
        # Comportamento originale: solo l'utente admin può usare i comandi
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and str(user_id) == str(admin_chat_id):
            return True
        return False


async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /all - invia messaggio a tutti gli utenti"""
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
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
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
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
    
    # Estrai messaggio (tutto dopo il comando)
    message_parts = update.message.text.split(maxsplit=1)
    if len(message_parts) < 2:
        await update.message.reply_text(
            f"📨 **Invio Messaggio a Utente**\n\n"
            f"ID: `{telegram_id}`\n\n"
            f"Uso: `/{telegram_id} <messaggio>`\n\n"
            f"Esempio: `/{telegram_id} Ciao! Questo è un messaggio per te.`",
            parse_mode='Markdown'
        )
        return
    
    message_text = message_parts[1]  # Tutto dopo il comando
    
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


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /report - invia report giornaliero manualmente"""
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo comando.")
        return
    
    # Estrai parametri (telegram_id opzionale, report_date opzionale)
    args = context.args if context.args else []
    
    telegram_id = None
    report_date = None
    
    if len(args) > 0:
        # Primo argomento: telegram_id o data
        first_arg = args[0]
        if first_arg.isdigit():
            telegram_id = int(first_arg)
            if len(args) > 1:
                report_date = args[1]  # Secondo argomento: data
        else:
            # Primo argomento è una data (formato YYYY-MM-DD)
            report_date = first_arg
    
    # Mostra info prima di inviare
    if telegram_id:
        user = await get_user_by_telegram_id(telegram_id)
        if not user:
            await update.message.reply_text(
                f"❌ **Utente non trovato**\n\n"
                f"ID Telegram `{telegram_id}` non esiste nel database."
            )
            return
        
        user_info = f"ID: {telegram_id}"
        if user.get("business_name"):
            user_info += f"\nBusiness: {user['business_name']}"
        
        await update.message.reply_text(
            f"⏳ **Invio report in corso...**\n\n"
            f"👤 **Utente:**\n{user_info}\n"
            f"📅 **Data:** {report_date or 'Oggi (default)'}\n\n"
            f"Attendere..."
        )
    else:
        await update.message.reply_text(
            f"⏳ **Invio report a tutti gli utenti...**\n\n"
            f"📅 **Data:** {report_date or 'Oggi (default)'}\n\n"
            f"Attendere..."
        )
    
    try:
        # Normalizza formato data se fornita (supporta DD/MM/YY o YYYY-MM-DD)
        if report_date:
            # Prova a convertire formato DD/MM/YY a YYYY-MM-DD
            try:
                if "/" in report_date:
                    parts = report_date.split("/")
                    if len(parts) == 3:
                        day, month, year = parts
                        # Se anno è 2 cifre, assume 20XX
                        if len(year) == 2:
                            year = f"20{year}"
                        report_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except Exception as date_error:
                logger.warning(f"[ADMIN_REPORT] Errore parsing data {report_date}: {date_error}")
                # Continua con formato originale, il server lo gestirà
        
        # Chiama endpoint processor
        url = f"{PROCESSOR_API_URL}/admin/trigger-daily-report"
        payload = {}
        
        if telegram_id:
            payload["telegram_id"] = telegram_id
        if report_date:
            payload["report_date"] = report_date
        
        logger.info(f"[ADMIN_REPORT] Chiamata endpoint: {url}")
        logger.info(f"[ADMIN_REPORT] Payload: {payload}")
        logger.info(f"[ADMIN_REPORT] PROCESSOR_API_URL configurato: {PROCESSOR_API_URL}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # Timeout 5 minuti
            response = await client.post(url, json=payload)
            logger.info(f"[ADMIN_REPORT] Response status: {response.status_code}")
            logger.info(f"[ADMIN_REPORT] Response text: {response.text[:500]}")
            response.raise_for_status()
            result = response.json()
        
        # Report risultato
        report_text = (
            f"✅ **Report Inviato**\n\n"
            f"📅 **Data:** {result.get('report_date', 'N/A')}\n"
            f"👤 **Utente:** {result.get('telegram_id', 'Tutti')}\n\n"
            f"📊 **Statistiche:**\n"
            f"• ✅ Inviati: {result.get('sent_count', 0)}\n"
            f"• ⏭️ Saltati: {result.get('skipped_count', 0)}\n"
            f"• ❌ Errori: {result.get('error_count', 0)}\n"
        )
        
        errors = result.get('errors', [])
        if errors:
            report_text += f"\n**Errori:**\n"
            for error in errors[:5]:  # Max 5 errori
                report_text += f"• {error[:100]}\n"
            if len(errors) > 5:
                report_text += f"\n... e altri {len(errors) - 5} errori"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
    
    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if e.response.text else "Nessun dettaglio disponibile"
        error_msg = f"HTTP {e.response.status_code}: {error_text}"
        logger.error(f"[ADMIN_REPORT] Errore HTTP comando /report: {error_msg}")
        logger.error(f"[ADMIN_REPORT] URL chiamato: {url}")
        logger.error(f"[ADMIN_REPORT] PROCESSOR_API_URL: {PROCESSOR_API_URL}")
        
        # Messaggio più dettagliato per 404 (senza Markdown complesso per evitare errori parsing)
        if e.response.status_code == 404:
            detail_msg = (
                "❌ Endpoint non trovato (404)\n\n"
                "L'endpoint /admin/trigger-daily-report non è stato trovato.\n\n"
                "Possibili cause:\n"
                "• Il deploy del processor non è ancora completato\n"
                "• L'URL del processor non è corretto\n"
                "• L'endpoint non è stato deployato\n\n"
                f"URL chiamato: {url}\n\n"
                "Verifica:\n"
                "• Che il processor sia deployato su Railway\n"
                "• Che la variabile PROCESSOR_URL sia corretta\n"
                "• Che l'endpoint esista nel codice del processor"
            )
        else:
            detail_msg = f"❌ Errore durante l'invio\n\nErrore: {error_msg}"
        
        await update.message.reply_text(detail_msg)
    except Exception as e:
        logger.error(f"Errore comando /report: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Errore durante l'invio**\n\n"
            f"Errore: {str(e)[:200]}"
        )


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /info - mostra tutti i comandi disponibili"""
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo comando.")
        return
    
    help_text = (
        "🤖 **Gioia Admin Bot - Comandi Disponibili**\n\n"
        "📢 **Invio Messaggi:**\n"
        "• `/all <messaggio>` - Invia messaggio a tutti gli utenti\n"
        "  Esempio: `/all Ciao a tutti! Questo è un messaggio di test.`\n\n"
        "• `/<telegram_id> <messaggio>` - Invia messaggio a un utente specifico\n"
        "  Esempio: `/927230913 Ciao, questo è un messaggio personalizzato`\n\n"
        "📊 **Report:**\n"
        "• `/report` - Genera report giornaliero per oggi a tutti gli utenti\n"
        "• `/report <telegram_id>` - Genera report per oggi a un utente specifico\n"
        "• `/report all <data>` - Genera report per una data specifica a tutti\n"
        "  Formato data: YYYY-MM-DD (es. 2025-12-11)\n"
        "  Esempi:\n"
        "  - `/report` - Report per oggi a tutti\n"
        "  - `/report 927230913` - Report per oggi a un utente\n"
        "  - `/report all 2025-12-11` - Report per il 11 dicembre a tutti\n\n"
        "👥 **Utenti:**\n"
        "• `/users` - Mostra lista di tutti gli utenti registrati\n\n"
        "ℹ️ **Info:**\n"
        "• `/info` - Mostra questo messaggio di aiuto\n"
        "• `/start` - Messaggio di benvenuto\n\n"
        "💡 **Note:**\n"
        "• I report includono consumi e ricavi del giorno\n"
        "• Gli utenti devono aver completato l'onboarding per ricevere messaggi"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /users - mostra lista di tutti gli utenti registrati"""
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo comando.")
        return
    
    try:
        users = await get_all_users()
        
        if not users:
            await update.message.reply_text(
                "📋 **Nessun utente trovato**\n\n"
                "Non ci sono utenti registrati nel database."
            )
            return
        
        # Formatta lista utenti
        message_parts = [f"👥 **Lista Utenti ({len(users)} totali)**\n"]
        
        # Limita a 50 utenti per messaggio (Telegram ha limite di 4096 caratteri)
        users_to_show = users[:50]
        
        for i, user in enumerate(users_to_show, 1):
            telegram_id = user.get("telegram_id", "N/A")
            username = user.get("username")
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            business_name = user.get("business_name", "N/A")
            onboarding_completed = user.get("onboarding_completed", False)
            
            # Costruisci nome completo
            name_parts = []
            if first_name:
                name_parts.append(first_name)
            if last_name:
                name_parts.append(last_name)
            full_name = " ".join(name_parts) if name_parts else "N/A"
            
            # Emoji stato onboarding
            status_emoji = "✅" if onboarding_completed else "⏳"
            
            # Formatta riga utente
            user_line = (
                f"{i}. {status_emoji} **ID:** `{telegram_id}`\n"
                f"   👤 **Nome:** {full_name}\n"
            )
            
            if username:
                user_line += f"   📱 **Username:** @{username}\n"
            
            user_line += f"   🏢 **Business:** {business_name}\n"
            
            message_parts.append(user_line)
        
        # Se ci sono più di 50 utenti, aggiungi nota
        if len(users) > 50:
            message_parts.append(f"\n... e altri {len(users) - 50} utenti")
        
        # Unisci tutte le parti
        full_message = "\n".join(message_parts)
        
        # Telegram ha limite di 4096 caratteri per messaggio
        # Se il messaggio è troppo lungo, dividilo in più messaggi
        max_length = 4000  # Lascia margine per formattazione
        if len(full_message) <= max_length:
            await update.message.reply_text(full_message, parse_mode='Markdown')
        else:
            # Dividi in più messaggi
            current_message = message_parts[0] + "\n"
            for part in message_parts[1:]:
                if len(current_message) + len(part) + 1 > max_length:
                    await update.message.reply_text(current_message, parse_mode='Markdown')
                    current_message = part + "\n"
                else:
                    current_message += part + "\n"
            
            # Invia ultimo messaggio
            if current_message.strip():
                await update.message.reply_text(current_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Errore recupero lista utenti: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Errore durante il recupero degli utenti**\n\n"
            f"Errore: {str(e)[:200]}"
        )


async def start_admin_cmd(update, context):
    """Comando /start per l'admin bot."""
    # Verifica autorizzazione (supporta utente privato e canale/gruppo)
    if not is_authorized(update):
        await update.message.reply_text("❌ Solo l'amministratore può usare questo bot.")
        return
    
    welcome_text = (
        "🤖 **Gioia Admin Bot**\n\n"
        "Benvenuto! Questo bot ti permette di gestire gli utenti e generare report.\n\n"
        "📋 **Comandi principali:**\n"
        "• `/info` - Mostra tutti i comandi disponibili\n"
        "• `/users` - Lista di tutti gli utenti registrati\n"
        "• `/all <messaggio>` - Invia messaggio a tutti\n"
        "• `/report` - Genera report giornaliero\n\n"
        "💡 Usa `/info` per vedere la guida completa!"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


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
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    
    # Handler per comandi numerici (telegram_id) - cattura messaggi che iniziano con / seguito da solo numeri
    async def handle_numeric_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce comandi numerici come /927230913"""
        if not update.message or not update.message.text:
            return
        
        # Estrai comando (prima parola)
        parts = update.message.text.split(maxsplit=1)
        command_text = parts[0]
        
        # Verifica che sia un comando numerico (es. /927230913)
        if command_text.startswith('/') and len(command_text) > 1:
            telegram_id_str = command_text[1:]  # Rimuovi /
            if telegram_id_str.isdigit():
                await user_id_cmd(update, context)
    
    # Cattura messaggi che iniziano con / seguito da solo numeri (non lettere)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^/\d+(\s|$)'), 
        handle_numeric_command
    ))
    
    logger.info("✅ Telegram bot configurato con comandi /start, /info, /users, /all, /report e /<telegram_id>")
    
    return app
