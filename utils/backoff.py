"""
Backoff con jitter per retry notifiche
"""
import random
import math
from typing import Optional


def calculate_backoff(retry_count: int, base_seconds: int = 10) -> int:
    """
    Calcola backoff esponenziale con jitter.
    
    Args:
        retry_count: Numero di retry (0 = primo tentativo)
        base_seconds: Base per calcolo esponenziale (default 10)
    
    Returns:
        Secondi di attesa prima del prossimo tentativo
    """
    if retry_count == 0:
        return 0  # Primo tentativo immediato
    
    # Backoff esponenziale: base * 2^(retry_count-1)
    # Retry 1-3: 10s, 20s, 40s
    # Retry 4-6: 80s, 160s, 320s
    # Retry 7-10: 600s (10 min) fisso
    if retry_count <= 3:
        exponential = base_seconds * (2 ** (retry_count - 1))
    elif retry_count <= 6:
        exponential = base_seconds * (2 ** (retry_count - 1))
    else:
        # Retry 7-10: max 10 minuti
        exponential = 600
    
    # Aggiungi jitter ±20% per evitare thundering herd
    jitter_range = exponential * 0.2
    jitter = random.uniform(-jitter_range, jitter_range)
    
    backoff = max(1, int(exponential + jitter))  # Minimo 1 secondo
    
    return backoff


def get_next_attempt_delay(retry_count: int, base_seconds: int = 10) -> int:
    """Alias per calculate_backoff (compatibilità)"""
    return calculate_backoff(retry_count, base_seconds)



Backoff con jitter per retry notifiche
"""
import random
import math
from typing import Optional


def calculate_backoff(retry_count: int, base_seconds: int = 10) -> int:
    """
    Calcola backoff esponenziale con jitter.
    
    Args:
        retry_count: Numero di retry (0 = primo tentativo)
        base_seconds: Base per calcolo esponenziale (default 10)
    
    Returns:
        Secondi di attesa prima del prossimo tentativo
    """
    if retry_count == 0:
        return 0  # Primo tentativo immediato
    
    # Backoff esponenziale: base * 2^(retry_count-1)
    # Retry 1-3: 10s, 20s, 40s
    # Retry 4-6: 80s, 160s, 320s
    # Retry 7-10: 600s (10 min) fisso
    if retry_count <= 3:
        exponential = base_seconds * (2 ** (retry_count - 1))
    elif retry_count <= 6:
        exponential = base_seconds * (2 ** (retry_count - 1))
    else:
        # Retry 7-10: max 10 minuti
        exponential = 600
    
    # Aggiungi jitter ±20% per evitare thundering herd
    jitter_range = exponential * 0.2
    jitter = random.uniform(-jitter_range, jitter_range)
    
    backoff = max(1, int(exponential + jitter))  # Minimo 1 secondo
    
    return backoff


def get_next_attempt_delay(retry_count: int, base_seconds: int = 10) -> int:
    """Alias per calculate_backoff (compatibilità)"""
    return calculate_backoff(retry_count, base_seconds)


"""
Backoff con jitter per retry notifiche
"""
import random
import math
from typing import Optional


def calculate_backoff(retry_count: int, base_seconds: int = 10) -> int:
    """
    Calcola backoff esponenziale con jitter.
    
    Args:
        retry_count: Numero di retry (0 = primo tentativo)
        base_seconds: Base per calcolo esponenziale (default 10)
    
    Returns:
        Secondi di attesa prima del prossimo tentativo
    """
    if retry_count == 0:
        return 0  # Primo tentativo immediato
    
    # Backoff esponenziale: base * 2^(retry_count-1)
    # Retry 1-3: 10s, 20s, 40s
    # Retry 4-6: 80s, 160s, 320s
    # Retry 7-10: 600s (10 min) fisso
    if retry_count <= 3:
        exponential = base_seconds * (2 ** (retry_count - 1))
    elif retry_count <= 6:
        exponential = base_seconds * (2 ** (retry_count - 1))
    else:
        # Retry 7-10: max 10 minuti
        exponential = 600
    
    # Aggiungi jitter ±20% per evitare thundering herd
    jitter_range = exponential * 0.2
    jitter = random.uniform(-jitter_range, jitter_range)
    
    backoff = max(1, int(exponential + jitter))  # Minimo 1 secondo
    
    return backoff


def get_next_attempt_delay(retry_count: int, base_seconds: int = 10) -> int:
    """Alias per calculate_backoff (compatibilità)"""
    return calculate_backoff(retry_count, base_seconds)



Backoff con jitter per retry notifiche
"""
import random
import math
from typing import Optional


def calculate_backoff(retry_count: int, base_seconds: int = 10) -> int:
    """
    Calcola backoff esponenziale con jitter.
    
    Args:
        retry_count: Numero di retry (0 = primo tentativo)
        base_seconds: Base per calcolo esponenziale (default 10)
    
    Returns:
        Secondi di attesa prima del prossimo tentativo
    """
    if retry_count == 0:
        return 0  # Primo tentativo immediato
    
    # Backoff esponenziale: base * 2^(retry_count-1)
    # Retry 1-3: 10s, 20s, 40s
    # Retry 4-6: 80s, 160s, 320s
    # Retry 7-10: 600s (10 min) fisso
    if retry_count <= 3:
        exponential = base_seconds * (2 ** (retry_count - 1))
    elif retry_count <= 6:
        exponential = base_seconds * (2 ** (retry_count - 1))
    else:
        # Retry 7-10: max 10 minuti
        exponential = 600
    
    # Aggiungi jitter ±20% per evitare thundering herd
    jitter_range = exponential * 0.2
    jitter = random.uniform(-jitter_range, jitter_range)
    
    backoff = max(1, int(exponential + jitter))  # Minimo 1 secondo
    
    return backoff


def get_next_attempt_delay(retry_count: int, base_seconds: int = 10) -> int:
    """Alias per calculate_backoff (compatibilità)"""
    return calculate_backoff(retry_count, base_seconds)


