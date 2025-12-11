"""
Worker per leggere e processare notifiche admin dalla coda
"""
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional
from db import get_db_pool
from models import AdminNotification
from notifier import send_notification_with_retry
from templates import (
    format_onboarding_completed,
    format_inventory_uploaded,
    format_error,
    format_batch_errors
)
from utils.rate_limiter import RateLimiter
from utils.logging import log_with_context
from utils.backoff import calculate_backoff

logger = logging.getLogger(__name__)

# Polling interval (secondi)
POLLING_INTERVAL = 5


async def get_user_info(telegram_id: int) -> dict:
    """Recupera informazioni utente dal database"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT telegram_id, username, first_name, last_name, business_name, created_at
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
                "created_at": row.get("created_at")
            }
        else:
            # Utente non trovato - usa solo telegram_id
            return {
                "telegram_id": telegram_id,
                "username": None,
                "first_name": None,
                "last_name": None,
                "business_name": None,
                "created_at": None
            }


async def format_notification_message(notification: AdminNotification) -> str:
    """Formatta messaggio notifica in base al tipo evento"""
    user_info = await get_user_info(notification.telegram_id)
    payload = notification.payload
    
    # Safety check: assicura che payload sia sempre un dict
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Payload non parsabile per notifica {notification.id}: {payload}")
            payload = {}
    elif payload is None:
        payload = {}
    elif not isinstance(payload, dict):
        logger.warning(f"Payload non è dict per notifica {notification.id}: {type(payload)}")
        payload = {}
    
    if notification.event_type == "onboarding_completed":
        return format_onboarding_completed(
            telegram_id=notification.telegram_id,
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            business_name=payload.get("business_name", "N/A"),
            duration_seconds=payload.get("duration_seconds"),
            correlation_id=notification.correlation_id,
            stage=payload.get("stage"),
            inventory_pending=payload.get("inventory_pending", False)
        )
    
    elif notification.event_type == "inventory_uploaded":
        return format_inventory_uploaded(
            telegram_id=notification.telegram_id,
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            file_type=payload.get("file_type", "N/A"),
            rows_processed=payload.get("rows_processed"),
            rows_rejected=payload.get("rows_rejected"),
            wines_saved=payload.get("wines_saved") or payload.get("saved_count"),
            processing_time=payload.get("processing_time"),
            correlation_id=notification.correlation_id
        )
    
    elif notification.event_type == "error":
        return format_error(
            telegram_id=notification.telegram_id,
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            last_user_message=payload.get("last_user_message"),
            user_visible_error=payload.get("user_visible_error"),
            error_message=payload.get("error_message"),
            error_code=payload.get("error_code"),
            source=payload.get("source", "unknown"),
            correlation_id=notification.correlation_id
        )
    
    else:
        # Fallback per eventi sconosciuti
        return f"""📢 **NOTIFICA** ({notification.event_type})

👤 Utente: {notification.telegram_id}
📦 Payload: {payload}
🔗 CorrID: {notification.correlation_id or 'N/A'}"""


async def process_notification(notification: AdminNotification, rate_limiter: RateLimiter) -> bool:
    """
    Processa una singola notifica.
    
    Returns:
        True se processata con successo, False altrimenti
    """
    try:
        # Verifica rate limit globale
        if not rate_limiter.can_send_globally():
            logger.warning(f"Rate limit globale raggiunto, notifica {notification.id} in attesa")
            return False
        
        # Per errori, verifica anti-spam per utente
        if notification.event_type == "error":
            if not rate_limiter.can_notify_error(notification.telegram_id):
                logger.info(f"Anti-spam: errore per utente {notification.telegram_id} già notificato recentemente")
                # Aggiorna notifica come "sent" ma non inviare (batching futuro)
                await mark_notification_sent(notification.id)
                return True
        
        # Formatta messaggio
        message = await format_notification_message(notification)
        
        # Invia notifica
        result = await send_notification_with_retry(
            message=message,
            notification_id=str(notification.id),
            correlation_id=notification.correlation_id,
            max_retries=10
        )
        
        if result["status"] == "sent":
            # Registra invio
            rate_limiter.record_send()
            if notification.event_type == "error":
                rate_limiter.record_error_notification(notification.telegram_id)
            
            # Aggiorna status
            await mark_notification_sent(notification.id)
            
            log_with_context(
                "info",
                f"Notifica {notification.id} processata con successo",
                correlation_id=notification.correlation_id,
                notification_id=str(notification.id),
                event_type=notification.event_type
            )
            return True
        
        else:
            # Errore - aggiorna per retry
            await update_notification_retry(
                notification.id,
                notification.retry_count + 1,
                result["error"]
            )
            return False
            
    except Exception as e:
        logger.error(f"Errore processamento notifica {notification.id}: {e}", exc_info=True)
        
        # Aggiorna per retry
        await update_notification_retry(
            notification.id,
            notification.retry_count + 1,
            str(e)
        )
        return False


async def mark_notification_sent(notification_id) -> None:
    """Marca notifica come inviata"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE admin_notifications
            SET status = 'sent'
            WHERE id = $1
        """, notification_id)


async def update_notification_retry(notification_id, retry_count: int, error: Optional[str]) -> None:
    """Aggiorna notifica con retry count e next_attempt_at"""
    pool = await get_db_pool()
    
    max_retries = int(os.getenv("ADMIN_MAX_RETRY", 10))
    base_backoff = int(os.getenv("ADMIN_BACKOFF_BASE", 10))
    
    if retry_count >= max_retries:
        # Marca come failed
        status = "failed"
        next_attempt = None
    else:
        # Calcola prossimo tentativo
        backoff_seconds = calculate_backoff(retry_count, base_backoff)
        next_attempt = datetime.utcnow() + timedelta(seconds=backoff_seconds)
        status = "pending"  # Rimane pending per retry
    
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE admin_notifications
            SET retry_count = $1,
                next_attempt_at = $2,
                status = $3
            WHERE id = $4
        """, retry_count, next_attempt, status, notification_id)


async def fetch_pending_notifications(limit: int = 50) -> List[AdminNotification]:
    """Recupera notifiche pending pronte per invio"""
    pool = await get_db_pool()
    
    now = datetime.utcnow()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT *
            FROM admin_notifications
            WHERE status = 'pending'
            AND next_attempt_at <= $1
            ORDER BY created_at ASC
            LIMIT $2
        """, now, limit)
        
        return [AdminNotification.from_row(row) for row in rows]


async def worker_loop(rate_limiter: RateLimiter):
    """Loop principale worker per processare notifiche"""
    logger.info("🚀 Worker notifiche admin avviato")
    
    while True:
        try:
            # Recupera notifiche pending
            notifications = await fetch_pending_notifications(limit=20)
            
            if notifications:
                logger.info(f"Trovate {len(notifications)} notifiche pending")
                
                # Processa ogni notifica
                for notification in notifications:
                    try:
                        await process_notification(notification, rate_limiter)
                    except Exception as e:
                        logger.error(f"Errore processamento notifica {notification.id}: {e}", exc_info=True)
                        continue
            else:
                # Nessuna notifica - attesa breve
                await asyncio.sleep(POLLING_INTERVAL)
                continue
            
            # Piccola pausa tra batch
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Errore nel worker loop: {e}", exc_info=True)
            await asyncio.sleep(POLLING_INTERVAL)


async def start_worker():
    """Avvia worker notifiche"""
    # Verifica configurazione
    if not os.getenv("ADMIN_BOT_TOKEN"):
        logger.error("ADMIN_BOT_TOKEN non configurato")
        return
    
    if not os.getenv("ADMIN_CHAT_ID"):
        logger.error("ADMIN_CHAT_ID non configurato")
        return
    
    # Inizializza rate limiter
    rate_limit_per_min = int(os.getenv("ADMIN_NOTIFY_RATE_LIMIT_PER_MIN", 20))
    min_error_interval = int(os.getenv("ADMIN_NOTIFY_MIN_ERROR_INTERVAL_SEC", 180))
    
    rate_limiter = RateLimiter(
        global_limit_per_min=rate_limit_per_min,
        min_error_interval_sec=min_error_interval
    )
    
    # Avvia loop
    await worker_loop(rate_limiter)
