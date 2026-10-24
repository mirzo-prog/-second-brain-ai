#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$PROJECT_ROOT/data/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

URL="http://127.0.0.1:8000"

# Check if server is already running
if curl -s "$URL/api/health" > /dev/null 2>&1; then
    echo "✓ Сервер Second Brain AI уже запущен."
else
    echo "Запуск сервера веб-сайта Second Brain AI..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG_DIR/server.log" 2>&1 &
    
    # Wait for server to become responsive
    for i in {1..20}; do
        if curl -s "$URL/api/health" > /dev/null 2>&1; then
            echo "✓ Сервер успешно запущен!"
            break
        fi
        sleep 0.3
    done
fi

echo "--------------------------------------------------------"
echo "🌐 Сайт Second Brain AI доступен по адресу:"
echo "👉 $URL"
echo "--------------------------------------------------------"

# Open in default browser
if which xdg-open > /dev/null 2>&1; then
    xdg-open "$URL" > /dev/null 2>&1 &
    echo "✓ Браузер открыт."
fi
