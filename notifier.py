"""
Notificatore Telegram per admin bot con retry automatico
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any
from utils.logging import log_with_context
from utils.backoff import calculate_backoff
import asyncio

logger = logging.getLogger(__name__)


async def send_notification_with_retry(
    message: str,
    notification_id: str,
    correlation_id: Optional[str] = None,
    max_retries: int = 10
) -> Dict[str, Any]:
    """
    Invia messaggio Telegram all'admin con retry automatico.
    
    Args:
        message: Testo del messaggio da inviare
        notification_id: ID notifica per logging
        correlation_id: ID correlazione per tracciamento
        max_retries: Numero massimo tentativi
    
    Returns:
        Dict con:
            - status: "sent" o "error"
            - error: Messaggio errore (se status="error")
    """
    admin_bot_token = os.getenv("ADMIN_BOT_TOKEN")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    
    if not admin_bot_token:
        error_msg = "ADMIN_BOT_TOKEN non configurato"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
    
    if not admin_chat_id:
        error_msg = "ADMIN_CHAT_ID non configurato"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
    
    url = f"https://api.telegram.org/bot{admin_bot_token}/sendMessage"
    
    payload = {
        "chat_id": admin_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    # Retry loop
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        log_with_context(
                            "info",
                            f"Notifica {notification_id} inviata con successo",
                            correlation_id=correlation_id,
                            notification_id=notification_id,
                            attempt=attempt + 1
                        )
                        return {"status": "sent"}
                    else:
                        error_desc = result.get("description", "Unknown error")
                        
                        # Gestione errori specifici Telegram
                        if "429" in error_desc or response.status_code == 429:
                            # Rate limit - retry con backoff
                            if attempt < max_retries:
                                backoff_seconds = calculate_backoff(attempt, base_seconds=10)
                                logger.warning(
                                    f"Rate limit Telegram per notifica {notification_id}, "
                                    f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})"
                                )
                                await asyncio.sleep(backoff_seconds)
                                continue
                        
                        elif "400" in error_desc or response.status_code == 400:
                            # Bad request - non retry
                            error_msg = f"Bad request Telegram: {error_desc}"
                            logger.error(
                                f"Errore Telegram per notifica {notification_id}: {error_msg}",
                                correlation_id=correlation_id
                            )
                            return {"status": "error", "error": error_msg}
                        
                        elif "401" in error_desc or response.status_code == 401:
                            # Unauthorized - errore critico
                            error_msg = f"Token Telegram invalido: {error_desc}"
                            logger.critical(
                                f"Errore critico Telegram per notifica {notification_id}: {error_msg}",
                                correlation_id=correlation_id
                            )
                            return {"status": "error", "error": error_msg}
                        
                        else:
                            # Altri errori - retry
                            if attempt < max_retries:
                                backoff_seconds = calculate_backoff(attempt, base_seconds=10)
                                logger.warning(
                                    f"Errore Telegram per notifica {notification_id}: {error_desc}, "
                                    f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})"
                                )
                                await asyncio.sleep(backoff_seconds)
                                continue
                            else:
                                error_msg = f"Telegram API error: {error_desc}"
                                return {"status": "error", "error": error_msg}
                
                elif response.status_code == 429:
                    # Rate limit HTTP
                    if attempt < max_retries:
                        backoff_seconds = calculate_backoff(attempt, base=10)
                        logger.warning(
                            f"Rate limit HTTP per notifica {notification_id}, "
                            f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(backoff_seconds)
                        continue
                    else:
                        error_msg = "Rate limit Telegram raggiunto dopo max retry"
                        return {"status": "error", "error": error_msg}
                
                else:
                    # Altri errori HTTP
                    if attempt < max_retries:
                        backoff_seconds = calculate_backoff(attempt, base=10)
                        logger.warning(
                            f"Errore HTTP {response.status_code} per notifica {notification_id}, "
                            f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(backoff_seconds)
                        continue
                    else:
                        error_msg = f"HTTP error {response.status_code}: {response.text[:200]}"
                        return {"status": "error", "error": error_msg}
        
        except httpx.TimeoutException:
            if attempt < max_retries:
                backoff_seconds = calculate_backoff(attempt, base=10)
                logger.warning(
                    f"Timeout invio notifica {notification_id}, "
                    f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(backoff_seconds)
                continue
            else:
                error_msg = "Timeout dopo max retry"
                return {"status": "error", "error": error_msg}
        
        except Exception as e:
            if attempt < max_retries:
                backoff_seconds = calculate_backoff(attempt, base=10)
                logger.warning(
                    f"Errore generico invio notifica {notification_id}: {e}, "
                    f"retry dopo {backoff_seconds}s (tentativo {attempt + 1}/{max_retries})",
                    exc_info=True
                )
                await asyncio.sleep(backoff_seconds)
                continue
            else:
                error_msg = f"Errore generico: {str(e)}"
                logger.error(
                    f"Errore definitivo invio notifica {notification_id}: {error_msg}",
                    correlation_id=correlation_id,
                    exc_info=True
                )
                return {"status": "error", "error": error_msg}
    
    # Se arriviamo qui, abbiamo esaurito i tentativi
    error_msg = f"Max retry ({max_retries}) raggiunto per notifica {notification_id}"
    logger.error(
        f"Impossibile inviare notifica {notification_id} dopo {max_retries} tentativi",
        correlation_id=correlation_id
    )
    return {"status": "error", "error": error_msg}
