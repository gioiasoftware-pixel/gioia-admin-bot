"""
Template per formattazione messaggi notifiche admin
"""
from datetime import datetime
from typing import Dict, Any, Optional


def format_onboarding_completed(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    business_name: str,
    duration_seconds: Optional[int],
    correlation_id: Optional[str]
) -> str:
    """Formatta messaggio onboarding completato"""
    # Costruisci nome utente
    user_display = f"{telegram_id}"
    if first_name or last_name:
        name_parts = [p for p in [first_name, last_name] if p]
        user_display = f"{telegram_id} — {' '.join(name_parts)}"
    if username:
        user_display += f" (@{username})"
    
    # Formatta durata
    duration_str = "N/A"
    if duration_seconds:
        if duration_seconds < 60:
            duration_str = f"{duration_seconds}s"
        elif duration_seconds < 3600:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration_str = f"{minutes}m {seconds}s"
        else:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            duration_str = f"{hours}h {minutes}m"
    
    message = f"""🎉 **ONBOARDING COMPLETATO**

👤 Utente: {user_display}
🏪 Business: {business_name}
⏱️ Durata: {duration_str}
🔗 CorrID: {correlation_id or 'N/A'}
📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"""
    
    return message


def format_inventory_uploaded(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    file_type: str,
    rows_processed: int,
    rows_rejected: Optional[int],
    wines_saved: Optional[int],
    processing_time: Optional[float],
    correlation_id: Optional[str]
) -> str:
    """Formatta messaggio inventario caricato"""
    # Costruisci nome utente
    user_display = f"{telegram_id}"
    if first_name or last_name:
        name_parts = [p for p in [first_name, last_name] if p]
        user_display = f"{telegram_id} — {' '.join(name_parts)}"
    if username:
        user_display += f" (@{username})"
    
    # Formatta dettagli file
    file_info = f"{file_type.upper()}"
    if rows_processed:
        file_info += f" ({rows_processed} righe"
        if rows_rejected and rows_rejected > 0:
            file_info += f", {rows_rejected} scartate"
        file_info += ")"
    
    # Formatta tempo
    time_str = "N/A"
    if processing_time:
        if processing_time < 60:
            time_str = f"{processing_time:.1f}s"
        else:
            minutes = int(processing_time // 60)
            seconds = int(processing_time % 60)
            time_str = f"{minutes}m {seconds}s"
    
    message = f"""📦 **INVENTARIO IMPORTATO (DAY 0)**

👤 Utente: {user_display}
📄 File: {file_info}
⏱️ Tempo: {time_str}"""
    
    if wines_saved:
        message += f"\n✅ Vini salvati: {wines_saved}"
    
    message += f"\n🔗 CorrID: {correlation_id or 'N/A'}"
    message += f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    return message


def format_error(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    last_user_message: Optional[str],
    user_visible_error: Optional[str],
    error_message: Optional[str],
    error_code: Optional[str],
    source: str,
    correlation_id: Optional[str]
) -> str:
    """Formatta messaggio errore"""
    # Costruisci nome utente
    user_display = f"{telegram_id}"
    if first_name or last_name:
        name_parts = [p for p in [first_name, last_name] if p]
        user_display = f"{telegram_id} — {' '.join(name_parts)}"
    if username:
        user_display += f" (@{username})"
    
    message = f"""🚨 **ERRORE**

👤 Utente: {user_display}"""
    
    if last_user_message:
        message += f"\n📥 Ultimo messaggio: \"{last_user_message}\""
    
    if user_visible_error:
        message += f"\n📤 Errore mostrato: \"{user_visible_error}\""
    
    if error_message and error_message != user_visible_error:
        message += f"\n💻 Dettaglio: {error_message[:200]}"
    
    if error_code:
        message += f"\n💻 Codice: {error_code}"
    
    message += f"\n📍 Sorgente: {source}"
    message += f"\n🔗 CorrID: {correlation_id or 'N/A'}"
    message += f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    return message


def format_batch_errors(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    errors: list,
    correlation_ids: list
) -> str:
    """Formatta messaggio batch errori multipli per stesso utente"""
    # Costruisci nome utente
    user_display = f"{telegram_id}"
    if first_name or last_name:
        name_parts = [p for p in [first_name, last_name] if p]
        user_display = f"{telegram_id} — {' '.join(name_parts)}"
    if username:
        user_display += f" (@{username})"
    
    message = f"""🚨 **ERRORI MULTIPLI**

👤 Utente: {user_display}
📊 Errori accumulati: {len(errors)}

"""
    
    for i, error in enumerate(errors[:5], 1):  # Max 5 errori
        message += f"{i}. "
        if error.get('user_visible_error'):
            message += f"{error['user_visible_error']}\n"
        elif error.get('error_message'):
            message += f"{error['error_message'][:100]}\n"
        else:
            message += "Errore sconosciuto\n"
        
        if error.get('error_code'):
            message += f"   Codice: {error['error_code']}\n"
    
    if len(errors) > 5:
        message += f"\n... e altri {len(errors) - 5} errori"
    
    message += f"\n🔗 CorrID: {', '.join(correlation_ids[:3])}"
    if len(correlation_ids) > 3:
        message += f" (+{len(correlation_ids) - 3} altri)"
    
    message += f"\n📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    
    return message

