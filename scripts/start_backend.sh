#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    echo "Создание виртуального окружения Python..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Запуск Second Brain AI Backend (http://127.0.0.1:8000)..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
