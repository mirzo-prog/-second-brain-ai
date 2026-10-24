#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_ROOT/data/second_brain.db"
BACKUP_DIR="$PROJECT_ROOT/data/backups"

if [ -z "$1" ]; then
    echo "Использование: $0 <путь_к_файлу_резервной_копии>"
    echo "Доступные резервные копии в $BACKUP_DIR:"
    ls -lh "$BACKUP_DIR"/*.db 2>/dev/null || echo "Резервных копий нет."
    exit 1
fi

RESTORE_FILE="$1"
if [ ! -f "$RESTORE_FILE" ]; then
    echo "Ошибка: Файл $RESTORE_FILE не найден."
    exit 1
fi

python3 -c "
import sqlite3
src = sqlite3.connect('$RESTORE_FILE')
dst = sqlite3.connect('$DB_PATH')
src.backup(dst)
dst.close()
src.close()
print('✓ База данных успешно восстановлена из: $RESTORE_FILE')
"
