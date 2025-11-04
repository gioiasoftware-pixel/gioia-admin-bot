"""
Logica invio messaggi Telegram per notifiche admin
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any
from utils.logging import log_with_context

logger = logging.getLogger(__name__)

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


async def send_notification(message: str, parse_mode: str = "Markdown") -> bool:
    """
    Invia messaggio Telegram all'admin.
    
    Returns:
        True se invio riuscito, False altrimenti
    """
    if not ADMIN_BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("ADMIN_BOT_TOKEN o ADMIN_CHAT_ID non configurati")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": int(ADMIN_CHAT_ID),
            "text": message,
            "parse_mode": parse_mode
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info("Notifica inviata con successo")
                return True
            else:
                logger.error(f"Errore Telegram API: {result.get('description')}")
                return False
                
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Rate limit - sarà gestito da retry con backoff
            logger.warning(f"Rate limit Telegram (429): {e.response.text}")
            raise  # Rilancia per gestione retry
        elif e.response.status_code == 400:
            # Bad request - non retry
            logger.error(f"Bad request Telegram (400): {e.response.text}")
            return False
        elif e.response.status_code == 401:
            # Unauthorized - token invalido, ferma bot
            logger.critical(f"Token Telegram invalido (401): {e.response.text}")
            raise
        else:
            logger.error(f"Errore HTTP Telegram: {e.response.status_code} - {e.response.text}")
            raise  # Rilancia per retry
    
    except Exception as e:
        logger.error(f"Errore invio notifica Telegram: {e}")
        raise  # Rilancia per retry


async def send_notification_with_retry(
    message: str,
    notification_id: str,
    correlation_id: Optional[str] = None,
    max_retries: int = 10
) -> Dict[str, Any]:
    """
    Invia notifica con gestione retry automatica.
    
    Returns:
        Dict con status: 'sent' o 'failed', retry_count, error se presente
    """
    from utils.backoff import calculate_backoff
    
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            success = await send_notification(message)
            
            if success:
                log_with_context(
                    "info",
                    f"Notifica {notification_id} inviata con successo",
                    correlation_id=correlation_id,
                    notification_id=notification_id,
                    retry_count=retry_count
                )
                return {
                    "status": "sent",
                    "retry_count": retry_count,
                    "error": None
                }
            
            # Se send_notification ritorna False (non retry), esci
            return {
                "status": "failed",
                "retry_count": retry_count,
                "error": "Telegram API returned ok=false"
            }
            
        except Exception as e:
            last_error = str(e)
            retry_count += 1
            
            if retry_count >= max_retries:
                log_with_context(
                    "error",
                    f"Notifica {notification_id} fallita dopo {max_retries} tentativi",
                    correlation_id=correlation_id,
                    notification_id=notification_id,
                    retry_count=retry_count,
                    error=last_error
                )
                return {
                    "status": "failed",
                    "retry_count": retry_count,
                    "error": last_error
                }
            
            # Calcola backoff
            backoff_seconds = calculate_backoff(retry_count)
            
            log_with_context(
                "warning",
                f"Retry {retry_count}/{max_retries} per notifica {notification_id} tra {backoff_seconds}s",
                correlation_id=correlation_id,
                notification_id=notification_id,
                retry_count=retry_count,
                backoff_seconds=backoff_seconds,
                error=last_error
            )
            
            # Attendi backoff (sarà gestito dal worker con next_attempt_at)
            # Qui non aspettiamo, il worker gestirà il timing
            raise  # Rilancia per gestione nel worker
    
    return {
        "status": "failed",
        "retry_count": retry_count,
        "error": last_error or "Max retries reached"
    }


