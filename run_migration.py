#!/usr/bin/env python3
"""
Script per eseguire la migration admin_notifications.
Legge DATABASE_URL da variabili ambiente (Railway o .env).
"""
import os
import asyncio
import asyncpg
from pathlib import Path

async def run_migration():
    """Esegue la migration SQL"""
    # Carica DATABASE_URL da ambiente
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERRORE: DATABASE_URL non trovata nelle variabili ambiente")
        print("   Assicurati di avere DATABASE_URL configurata")
        return False
    
    # Converti postgresql:// a postgresql+asyncpg:// se necessario
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # Leggi file SQL
    migration_file = Path(__file__).parent / "migrations" / "001_create_admin_notifications.sql"
    
    if not migration_file.exists():
        print(f"❌ ERRORE: File migration non trovato: {migration_file}")
        return False
    
    sql_content = migration_file.read_text(encoding='utf-8')
    
    print(f"📄 Lettura migration: {migration_file}")
    print(f"🔗 Connessione a database...")
    
    try:
        # Connetti al database
        conn = await asyncpg.connect(database_url)
        
        print("✅ Connesso al database")
        print("🔄 Esecuzione migration...")
        
        # Esegui SQL (asyncpg supporta multi-statement)
        await conn.execute(sql_content)
        
        print("✅ Migration eseguita con successo!")
        
        # Verifica
        print("🔍 Verifica tabella...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'admin_notifications'
            )
        """)
        
        if table_exists:
            print("✅ Tabella 'admin_notifications' creata correttamente")
            
            # Conta colonne
            col_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'admin_notifications'
            """)
            print(f"✅ Colonne create: {col_count}")
            
            # Conta indici
            idx_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = 'admin_notifications'
            """)
            print(f"✅ Indici creati: {idx_count}")
            
            await conn.close()
            return True
        else:
            print("❌ ERRORE: Tabella non trovata dopo migration")
            await conn.close()
            return False
            
    except Exception as e:
        print(f"❌ ERRORE durante migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Esecuzione migration admin_notifications\n")
    success = asyncio.run(run_migration())
    
    if success:
        print("\n✅ Migration completata con successo!")
        print("   Puoi procedere con l'implementazione del bot admin.")
    else:
        print("\n❌ Migration fallita. Controlla gli errori sopra.")
        exit(1)

