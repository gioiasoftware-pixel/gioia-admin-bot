"""
Handler per comandi Telegram del bot admin
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import get_db_pool
import json

logger = logging.getLogger(__name__)


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test - mostra l'ultima notifica dalla tabella admin_notifications"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    # Verifica che sia l'admin
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Recupera ultima notifica
            row = await conn.fetchrow("""
                SELECT *
                FROM admin_notifications
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            if not row:
                await update.message.reply_text(
                    "📭 **Nessuna notifica trovata**\n\n"
                    "La tabella `admin_notifications` è vuota."
                )
                return
            
            # Formatta risposta
            payload = row['payload']
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            payload_str = json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, dict) else str(payload)
            
            response = f"""📋 **Ultima Notifica Admin**

🆔 **ID:** `{row['id']}`
📅 **Data:** `{row['created_at']}`
📊 **Status:** `{row['status']}`
🏷️ **Event Type:** `{row['event_type']}`
👤 **Telegram ID:** `{row['telegram_id']}`
🔗 **Correlation ID:** `{row.get('correlation_id', 'N/A')}`
🔄 **Retry Count:** `{row.get('retry_count', 0)}`
⏰ **Next Attempt:** `{row.get('next_attempt_at', 'N/A')}`

📦 **Payload:**
```
{payload_str[:1000]}
```
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Errore comando /test: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - mostra comandi disponibili"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato.")
        return
    
    help_text = """🤖 **Gioia Admin Bot - Comandi**

/test - Mostra l'ultima notifica dalla tabella admin_notifications

/help - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    await update.message.reply_text(
        "🤖 **Gioia Admin Bot**\n\n"
        "Bot privato per notifiche admin.\n"
        "Usa /help per vedere i comandi disponibili."
    )


def setup_telegram_app(token: str) -> Application:
    """Setup applicazione Telegram"""
    application = Application.builder().token(token).build()
    
    # Registra handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("test", test_cmd))
    
    return application



Handler per comandi Telegram del bot admin
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import get_db_pool
import json

logger = logging.getLogger(__name__)


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test - mostra l'ultima notifica dalla tabella admin_notifications"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    # Verifica che sia l'admin
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Recupera ultima notifica
            row = await conn.fetchrow("""
                SELECT *
                FROM admin_notifications
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            if not row:
                await update.message.reply_text(
                    "📭 **Nessuna notifica trovata**\n\n"
                    "La tabella `admin_notifications` è vuota."
                )
                return
            
            # Formatta risposta
            payload = row['payload']
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            payload_str = json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, dict) else str(payload)
            
            response = f"""📋 **Ultima Notifica Admin**

🆔 **ID:** `{row['id']}`
📅 **Data:** `{row['created_at']}`
📊 **Status:** `{row['status']}`
🏷️ **Event Type:** `{row['event_type']}`
👤 **Telegram ID:** `{row['telegram_id']}`
🔗 **Correlation ID:** `{row.get('correlation_id', 'N/A')}`
🔄 **Retry Count:** `{row.get('retry_count', 0)}`
⏰ **Next Attempt:** `{row.get('next_attempt_at', 'N/A')}`

📦 **Payload:**
```
{payload_str[:1000]}
```
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Errore comando /test: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - mostra comandi disponibili"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato.")
        return
    
    help_text = """🤖 **Gioia Admin Bot - Comandi**

/test - Mostra l'ultima notifica dalla tabella admin_notifications

/help - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    await update.message.reply_text(
        "🤖 **Gioia Admin Bot**\n\n"
        "Bot privato per notifiche admin.\n"
        "Usa /help per vedere i comandi disponibili."
    )


def setup_telegram_app(token: str) -> Application:
    """Setup applicazione Telegram"""
    application = Application.builder().token(token).build()
    
    # Registra handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("test", test_cmd))
    
    return application


"""
Handler per comandi Telegram del bot admin
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import get_db_pool
import json

logger = logging.getLogger(__name__)


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test - mostra l'ultima notifica dalla tabella admin_notifications"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    # Verifica che sia l'admin
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Recupera ultima notifica
            row = await conn.fetchrow("""
                SELECT *
                FROM admin_notifications
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            if not row:
                await update.message.reply_text(
                    "📭 **Nessuna notifica trovata**\n\n"
                    "La tabella `admin_notifications` è vuota."
                )
                return
            
            # Formatta risposta
            payload = row['payload']
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            payload_str = json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, dict) else str(payload)
            
            response = f"""📋 **Ultima Notifica Admin**

🆔 **ID:** `{row['id']}`
📅 **Data:** `{row['created_at']}`
📊 **Status:** `{row['status']}`
🏷️ **Event Type:** `{row['event_type']}`
👤 **Telegram ID:** `{row['telegram_id']}`
🔗 **Correlation ID:** `{row.get('correlation_id', 'N/A')}`
🔄 **Retry Count:** `{row.get('retry_count', 0)}`
⏰ **Next Attempt:** `{row.get('next_attempt_at', 'N/A')}`

📦 **Payload:**
```
{payload_str[:1000]}
```
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Errore comando /test: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - mostra comandi disponibili"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato.")
        return
    
    help_text = """🤖 **Gioia Admin Bot - Comandi**

/test - Mostra l'ultima notifica dalla tabella admin_notifications

/help - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    await update.message.reply_text(
        "🤖 **Gioia Admin Bot**\n\n"
        "Bot privato per notifiche admin.\n"
        "Usa /help per vedere i comandi disponibili."
    )


def setup_telegram_app(token: str) -> Application:
    """Setup applicazione Telegram"""
    application = Application.builder().token(token).build()
    
    # Registra handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("test", test_cmd))
    
    return application



Handler per comandi Telegram del bot admin
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import get_db_pool
import json

logger = logging.getLogger(__name__)


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test - mostra l'ultima notifica dalla tabella admin_notifications"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    # Verifica che sia l'admin
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Recupera ultima notifica
            row = await conn.fetchrow("""
                SELECT *
                FROM admin_notifications
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            if not row:
                await update.message.reply_text(
                    "📭 **Nessuna notifica trovata**\n\n"
                    "La tabella `admin_notifications` è vuota."
                )
                return
            
            # Formatta risposta
            payload = row['payload']
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            payload_str = json.dumps(payload, indent=2, ensure_ascii=False) if isinstance(payload, dict) else str(payload)
            
            response = f"""📋 **Ultima Notifica Admin**

🆔 **ID:** `{row['id']}`
📅 **Data:** `{row['created_at']}`
📊 **Status:** `{row['status']}`
🏷️ **Event Type:** `{row['event_type']}`
👤 **Telegram ID:** `{row['telegram_id']}`
🔗 **Correlation ID:** `{row.get('correlation_id', 'N/A')}`
🔄 **Retry Count:** `{row.get('retry_count', 0)}`
⏰ **Next Attempt:** `{row.get('next_attempt_at', 'N/A')}`

📦 **Payload:**
```
{payload_str[:1000]}
```
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Errore comando /test: {e}")
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - mostra comandi disponibili"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato.")
        return
    
    help_text = """🤖 **Gioia Admin Bot - Comandi**

/test - Mostra l'ultima notifica dalla tabella admin_notifications

/help - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    
    if chat_id != admin_chat_id:
        await update.message.reply_text("❌ Accesso negato. Solo l'admin può usare questo bot.")
        return
    
    await update.message.reply_text(
        "🤖 **Gioia Admin Bot**\n\n"
        "Bot privato per notifiche admin.\n"
        "Usa /help per vedere i comandi disponibili."
    )


def setup_telegram_app(token: str) -> Application:
    """Setup applicazione Telegram"""
    application = Application.builder().token(token).build()
    
    # Registra handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("test", test_cmd))
    
    return application






