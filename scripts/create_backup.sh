#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_ROOT/data/second_brain.db"
BACKUP_DIR="$PROJECT_ROOT/data/backups"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
    echo "Ошибка: База данных $DB_PATH еще не создана."
    exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.db"

# Atomic SQLite online backup via sqlite3 command
python3 -c "
import sqlite3
src = sqlite3.connect('$DB_PATH')
dst = sqlite3.connect('$BACKUP_FILE')
src.backup(dst)
dst.close()
src.close()
print('✓ Резервная копия создана: $BACKUP_FILE')
"
