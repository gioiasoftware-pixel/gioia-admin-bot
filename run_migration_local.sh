#!/bin/bash
# Script per eseguire migration localmente con psql
# Usa questo se hai DATABASE_URL configurata

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERRORE: DATABASE_URL non configurata"
    echo "   Esporta DATABASE_URL prima di eseguire:"
    echo "   export DATABASE_URL='postgresql://user:pass@host:port/db'"
    exit 1
fi

echo "🚀 Esecuzione migration admin_notifications..."
echo "🔗 Connessione a database..."

psql "$DATABASE_URL" -f migrations/001_create_admin_notifications.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration eseguita con successo!"
    echo ""
    echo "🔍 Verifica tabella:"
    psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_notifications';"
else
    echo "❌ Migration fallita"
    exit 1
fi

