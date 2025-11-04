"""
Modelli per tabella admin_notifications
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import json


@dataclass
class AdminNotification:
    """Modello per notifica admin"""
    id: uuid.UUID
    created_at: datetime
    status: str  # 'pending', 'sent', 'failed'
    event_type: str  # 'onboarding_completed', 'inventory_uploaded', 'error'
    telegram_id: int
    correlation_id: Optional[str]
    payload: Dict[str, Any]
    retry_count: int
    next_attempt_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'AdminNotification':
        """Crea AdminNotification da row database"""
        # Parse payload se è una stringa (asyncpg può restituire JSONB come stringa)
        payload = row['payload']
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                # Se non è JSON valido, usa dict vuoto
                payload = {}
        elif payload is None:
            payload = {}
        
        return cls(
            id=row['id'],
            created_at=row['created_at'],
            status=row['status'],
            event_type=row['event_type'],
            telegram_id=row['telegram_id'],
            correlation_id=row.get('correlation_id'),
            payload=payload,
            retry_count=row.get('retry_count', 0),
            next_attempt_at=row['next_attempt_at']
        )

