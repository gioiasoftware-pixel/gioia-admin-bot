"""
Rate limiter globale e per utente per notifiche admin
"""
import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimiter:
    """Rate limiter per notifiche admin"""
    
    def __init__(
        self,
        global_limit_per_min: int = 20,
        min_error_interval_sec: int = 180
    ):
        self.global_limit_per_min = global_limit_per_min
        self.min_error_interval_sec = min_error_interval_sec
        
        # Track globale: lista timestamp ultimi invii
        self._global_sends: list = []
        
        # Track per utente: ultimo errore notificato per telegram_id
        self._last_error_notified: Dict[int, datetime] = {}
        
        # Track batch errori: errori accumulati per utente
        self._pending_errors: Dict[int, list] = defaultdict(list)
    
    def can_send_globally(self) -> bool:
        """
        Verifica se possiamo inviare una notifica (limite globale).
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        
        # Rimuovi timestamp vecchi (> 1 minuto)
        self._global_sends = [ts for ts in self._global_sends if ts > cutoff]
        
        # Verifica limite
        if len(self._global_sends) >= self.global_limit_per_min:
            return False
        
        return True
    
    def record_send(self):
        """Registra un invio (per limite globale)"""
        self._global_sends.append(datetime.utcnow())
    
    def can_notify_error(self, telegram_id: int) -> bool:
        """
        Verifica se possiamo notificare un errore per questo utente.
        Implementa anti-spam: 1 errore ogni MIN_ERROR_INTERVAL secondi.
        """
        now = datetime.utcnow()
        last_notified = self._last_error_notified.get(telegram_id)
        
        if last_notified is None:
            return True
        
        elapsed = (now - last_notified).total_seconds()
        return elapsed >= self.min_error_interval_sec
    
    def record_error_notification(self, telegram_id: int):
        """Registra che abbiamo notificato un errore per questo utente"""
        self._last_error_notified[telegram_id] = datetime.utcnow()
    
    def add_pending_error(self, telegram_id: int, error_data: dict):
        """Aggiungi errore in batch (per accumulo)"""
        self._pending_errors[telegram_id].append(error_data)
    
    def get_pending_errors(self, telegram_id: int) -> list:
        """Ottieni errori in batch per utente"""
        errors = self._pending_errors.get(telegram_id, [])
        self._pending_errors[telegram_id] = []  # Pulisci dopo lettura
        return errors
    
    def clear_pending_errors(self, telegram_id: int):
        """Pulisci errori in batch per utente"""
        self._pending_errors.pop(telegram_id, None)


