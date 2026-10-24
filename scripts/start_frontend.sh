#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "Установка npm зависимостей frontend..."
    npm install
fi

echo "Запуск Second Brain AI Frontend (http://127.0.0.1:5173)..."
exec npm run dev -- --host 127.0.0.1 --port 5173
