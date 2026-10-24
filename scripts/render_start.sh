#!/usr/bin/env bash
set -e

PORT="${PORT:-8000}"
echo "Запуск Second Brain AI на порту $PORT (Render.com)..."

cd backend
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
