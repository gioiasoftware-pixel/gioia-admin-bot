"""
Script di test per gioia-admin-bot
Inserisce notifiche di test nella tabella admin_notifications
"""
import asyncio
import os
import sys
from datetime import datetime
import uuid
from dotenv import load_dotenv
import asyncpg

# Carica variabili d'ambiente
load_dotenv()

# Configurazione
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL non configurata")
    print("   Configura DATABASE_URL nel file .env o come variabile d'ambiente")
    sys.exit(1)

# Normalizza DATABASE_URL per asyncpg
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


async def test_notification(event_type: str, telegram_id: int, payload: dict):
    """Inserisce una notifica di test nella tabella"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        notification_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        print(f"\n📝 Inserimento notifica di test...")
        print(f"   Event Type: {event_type}")
        print(f"   Telegram ID: {telegram_id}")
        print(f"   Correlation ID: {correlation_id}")
        
        await conn.execute("""
            INSERT INTO admin_notifications 
            (id, created_at, status, event_type, telegram_id, correlation_id, payload, retry_count, next_attempt_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, 
            notification_id,
            datetime.utcnow(),
            'pending',
            event_type,
            telegram_id,
            correlation_id,
            payload,
            0,
            datetime.utcnow()
        )
        
        print(f"✅ Notifica inserita con ID: {notification_id}")
        print(f"   Il bot admin dovrebbe processarla entro pochi secondi")
        print(f"   Controlla il bot Telegram per il messaggio!")
        
    except Exception as e:
        print(f"❌ Errore inserimento: {e}")
        raise
    finally:
        await conn.close()


async def main():
    """Menu interattivo per testare il bot"""
    print("🧪 Test Gioia Admin Bot")
    print("=" * 50)
    
    # Test 1: Onboarding completato
    print("\n📋 Test 1: Onboarding completato")
    await test_notification(
        event_type="onboarding_completed",
        telegram_id=123456789,  # ID di test
        payload={
            "business_name": "Ristorante Test",
            "user_name": "Test User",
            "onboarding_duration_seconds": 120,
            "inventory_items_count": 25
        }
    )
    
    await asyncio.sleep(2)
    
    # Test 2: Inventario caricato
    print("\n📋 Test 2: Inventario caricato")
    await test_notification(
        event_type="inventory_uploaded",
        telegram_id=123456789,
        payload={
            "business_name": "Ristorante Test",
            "file_type": "csv",
            "file_size_bytes": 15234,
            "wines_processed": 25,
            "wines_saved": 25,
            "warnings_count": 3,
            "processing_duration_seconds": 45
        }
    )
    
    await asyncio.sleep(2)
    
    # Test 3: Errore
    print("\n📋 Test 3: Errore")
    await test_notification(
        event_type="error",
        telegram_id=123456789,
        payload={
            "business_name": "Ristorante Test",
            "error_type": "processing_error",
            "error_message": "Errore di test: file non valido",
            "error_code": "INVALID_FILE",
            "component": "processor",
            "correlation_id": str(uuid.uuid4())
        }
    )
    
    print("\n" + "=" * 50)
    print("✅ Test completati!")
    print("\n💡 Controlla:")
    print("   1. Il bot Telegram per i messaggi ricevuti")
    print("   2. I log del bot admin per eventuali errori")
    print("   3. La tabella admin_notifications per lo status 'sent' o 'failed'")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrotto dall'utente")
    except Exception as e:
        print(f"\n\n❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

