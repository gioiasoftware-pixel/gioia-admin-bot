"""
Logging strutturato con correlation_id per gioia-admin-bot
"""
import json
import logging
import uuid
from typing import Optional
from datetime import datetime

logger = logging.getLogger("app")


def log_with_context(
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    notification_id: Optional[str] = None,
    **extra
):
    """
    Log strutturato JSON con contesto notifica.
    
    Args:
        level: 'info', 'warning', 'error', 'debug'
        message: Messaggio log
        correlation_id: ID correlazione request (genera se None)
        notification_id: ID notifica admin
        **extra: Campi aggiuntivi per log
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    payload = {
        "level": level.upper(),
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": correlation_id,
        **extra
    }
    
    if notification_id:
        payload["notification_id"] = notification_id
    
    # Log come JSON per parsing strutturato
    logger.log(
        getattr(logging, level.upper(), logging.INFO),
        json.dumps(payload)
    )

