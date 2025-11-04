"""
Gestione connessione database PostgreSQL async per gioia-admin-bot
"""
import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pool di connessioni
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Ottieni pool connessioni database (singleton)"""
    global _pool
    
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL non configurata")
        
        # Converti postgresql:// a formato asyncpg (asyncpg usa postgresql:// direttamente)
        # Rimuovi eventuali prefissi +asyncpg o +psycopg2 se presenti
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("postgresql://"):
            pass  # Già formato corretto per asyncpg
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info("Connessione al database PostgreSQL...")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("✅ Pool database creato")
    
    return _pool


async def close_db_pool():
    """Chiudi pool connessioni"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Pool database chiuso")


async def ensure_admin_notifications_table():
    """
    Crea tabella admin_notifications se non esiste (auto-migration all'avvio).
    Simile a create_tables() nel processor.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verifica se tabella esiste
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists:
                logger.info("Tabella admin_notifications già esistente")
                return
            
            # Leggi migration SQL
            from pathlib import Path
            migration_file = Path(__file__).parent / "migrations" / "001_create_admin_notifications.sql"
            
            if not migration_file.exists():
                logger.warning(f"File migration non trovato: {migration_file}")
                # Fallback: crea tabella direttamente
                await _create_table_directly(conn)
                return
            
            sql_content = migration_file.read_text(encoding='utf-8')
            
            logger.info("Esecuzione migration admin_notifications...")
            await conn.execute(sql_content)
            
            # Verifica creazione
            table_exists_after = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists_after:
                logger.info("✅ Tabella admin_notifications creata con successo")
            else:
                logger.error("❌ Tabella non creata dopo migration")
                
    except Exception as e:
        logger.error(f"Errore durante creazione tabella admin_notifications: {e}")
        raise


async def _create_table_directly(conn):
    """Crea tabella direttamente se file migration non disponibile"""
    logger.info("Creazione tabella admin_notifications (fallback)...")
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT now(),
            status TEXT DEFAULT 'pending',
            event_type TEXT NOT NULL,
            telegram_id BIGINT NOT NULL,
            correlation_id TEXT,
            payload JSONB NOT NULL,
            retry_count INTEGER DEFAULT 0,
            next_attempt_at TIMESTAMP DEFAULT now()
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_pending
            ON admin_notifications (status, next_attempt_at)
            WHERE status = 'pending'
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_user_created
            ON admin_notifications (telegram_id, created_at DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_correlation
            ON admin_notifications (correlation_id)
            WHERE correlation_id IS NOT NULL
    """)
    
    logger.info("✅ Tabella admin_notifications creata (fallback)")


"""
import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pool di connessioni
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Ottieni pool connessioni database (singleton)"""
    global _pool
    
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL non configurata")
        
        # Converti postgresql:// a formato asyncpg (asyncpg usa postgresql:// direttamente)
        # Rimuovi eventuali prefissi +asyncpg o +psycopg2 se presenti
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("postgresql://"):
            pass  # Già formato corretto per asyncpg
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info("Connessione al database PostgreSQL...")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("✅ Pool database creato")
    
    return _pool


async def close_db_pool():
    """Chiudi pool connessioni"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Pool database chiuso")


async def ensure_admin_notifications_table():
    """
    Crea tabella admin_notifications se non esiste (auto-migration all'avvio).
    Simile a create_tables() nel processor.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verifica se tabella esiste
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists:
                logger.info("Tabella admin_notifications già esistente")
                return
            
            # Leggi migration SQL
            from pathlib import Path
            migration_file = Path(__file__).parent / "migrations" / "001_create_admin_notifications.sql"
            
            if not migration_file.exists():
                logger.warning(f"File migration non trovato: {migration_file}")
                # Fallback: crea tabella direttamente
                await _create_table_directly(conn)
                return
            
            sql_content = migration_file.read_text(encoding='utf-8')
            
            logger.info("Esecuzione migration admin_notifications...")
            await conn.execute(sql_content)
            
            # Verifica creazione
            table_exists_after = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists_after:
                logger.info("✅ Tabella admin_notifications creata con successo")
            else:
                logger.error("❌ Tabella non creata dopo migration")
                
    except Exception as e:
        logger.error(f"Errore durante creazione tabella admin_notifications: {e}")
        raise


async def _create_table_directly(conn):
    """Crea tabella direttamente se file migration non disponibile"""
    logger.info("Creazione tabella admin_notifications (fallback)...")
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT now(),
            status TEXT DEFAULT 'pending',
            event_type TEXT NOT NULL,
            telegram_id BIGINT NOT NULL,
            correlation_id TEXT,
            payload JSONB NOT NULL,
            retry_count INTEGER DEFAULT 0,
            next_attempt_at TIMESTAMP DEFAULT now()
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_pending
            ON admin_notifications (status, next_attempt_at)
            WHERE status = 'pending'
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_user_created
            ON admin_notifications (telegram_id, created_at DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_correlation
            ON admin_notifications (correlation_id)
            WHERE correlation_id IS NOT NULL
    """)
    
    logger.info("✅ Tabella admin_notifications creata (fallback)")


"""
import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pool di connessioni
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Ottieni pool connessioni database (singleton)"""
    global _pool
    
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL non configurata")
        
        # Converti postgresql:// a formato asyncpg (asyncpg usa postgresql:// direttamente)
        # Rimuovi eventuali prefissi +asyncpg o +psycopg2 se presenti
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("postgresql://"):
            pass  # Già formato corretto per asyncpg
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info("Connessione al database PostgreSQL...")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("✅ Pool database creato")
    
    return _pool


async def close_db_pool():
    """Chiudi pool connessioni"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Pool database chiuso")


async def ensure_admin_notifications_table():
    """
    Crea tabella admin_notifications se non esiste (auto-migration all'avvio).
    Simile a create_tables() nel processor.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verifica se tabella esiste
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists:
                logger.info("Tabella admin_notifications già esistente")
                return
            
            # Leggi migration SQL
            from pathlib import Path
            migration_file = Path(__file__).parent / "migrations" / "001_create_admin_notifications.sql"
            
            if not migration_file.exists():
                logger.warning(f"File migration non trovato: {migration_file}")
                # Fallback: crea tabella direttamente
                await _create_table_directly(conn)
                return
            
            sql_content = migration_file.read_text(encoding='utf-8')
            
            logger.info("Esecuzione migration admin_notifications...")
            await conn.execute(sql_content)
            
            # Verifica creazione
            table_exists_after = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists_after:
                logger.info("✅ Tabella admin_notifications creata con successo")
            else:
                logger.error("❌ Tabella non creata dopo migration")
                
    except Exception as e:
        logger.error(f"Errore durante creazione tabella admin_notifications: {e}")
        raise


async def _create_table_directly(conn):
    """Crea tabella direttamente se file migration non disponibile"""
    logger.info("Creazione tabella admin_notifications (fallback)...")
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT now(),
            status TEXT DEFAULT 'pending',
            event_type TEXT NOT NULL,
            telegram_id BIGINT NOT NULL,
            correlation_id TEXT,
            payload JSONB NOT NULL,
            retry_count INTEGER DEFAULT 0,
            next_attempt_at TIMESTAMP DEFAULT now()
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_pending
            ON admin_notifications (status, next_attempt_at)
            WHERE status = 'pending'
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_user_created
            ON admin_notifications (telegram_id, created_at DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_correlation
            ON admin_notifications (correlation_id)
            WHERE correlation_id IS NOT NULL
    """)
    
    logger.info("✅ Tabella admin_notifications creata (fallback)")


"""
import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pool di connessioni
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Ottieni pool connessioni database (singleton)"""
    global _pool
    
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL non configurata")
        
        # Converti postgresql:// a formato asyncpg (asyncpg usa postgresql:// direttamente)
        # Rimuovi eventuali prefissi +asyncpg o +psycopg2 se presenti
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("postgresql://"):
            pass  # Già formato corretto per asyncpg
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info("Connessione al database PostgreSQL...")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("✅ Pool database creato")
    
    return _pool


async def close_db_pool():
    """Chiudi pool connessioni"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Pool database chiuso")


async def ensure_admin_notifications_table():
    """
    Crea tabella admin_notifications se non esiste (auto-migration all'avvio).
    Simile a create_tables() nel processor.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Verifica se tabella esiste
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists:
                logger.info("Tabella admin_notifications già esistente")
                return
            
            # Leggi migration SQL
            from pathlib import Path
            migration_file = Path(__file__).parent / "migrations" / "001_create_admin_notifications.sql"
            
            if not migration_file.exists():
                logger.warning(f"File migration non trovato: {migration_file}")
                # Fallback: crea tabella direttamente
                await _create_table_directly(conn)
                return
            
            sql_content = migration_file.read_text(encoding='utf-8')
            
            logger.info("Esecuzione migration admin_notifications...")
            await conn.execute(sql_content)
            
            # Verifica creazione
            table_exists_after = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'admin_notifications'
                )
            """)
            
            if table_exists_after:
                logger.info("✅ Tabella admin_notifications creata con successo")
            else:
                logger.error("❌ Tabella non creata dopo migration")
                
    except Exception as e:
        logger.error(f"Errore durante creazione tabella admin_notifications: {e}")
        raise


async def _create_table_directly(conn):
    """Crea tabella direttamente se file migration non disponibile"""
    logger.info("Creazione tabella admin_notifications (fallback)...")
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT now(),
            status TEXT DEFAULT 'pending',
            event_type TEXT NOT NULL,
            telegram_id BIGINT NOT NULL,
            correlation_id TEXT,
            payload JSONB NOT NULL,
            retry_count INTEGER DEFAULT 0,
            next_attempt_at TIMESTAMP DEFAULT now()
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_pending
            ON admin_notifications (status, next_attempt_at)
            WHERE status = 'pending'
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_user_created
            ON admin_notifications (telegram_id, created_at DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_correlation
            ON admin_notifications (correlation_id)
            WHERE correlation_id IS NOT NULL
    """)
    
    logger.info("✅ Tabella admin_notifications creata (fallback)")

