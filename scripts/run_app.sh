#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================================="
echo "          SECOND BRAIN AI — ЗАПУСК СИСТЕМЫ               "
echo "=========================================================="
echo "Рабочая директория: $PROJECT_ROOT"

# Ensure log directory exists
mkdir -p "$PROJECT_ROOT/data/logs"

# Trap shutdown signals to terminate both children cleanly
cleanup() {
    echo ""
    echo "Остановка процессов Second Brain AI..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "Все процессы безопасно остановлены."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start Backend
"$SCRIPT_DIR/start_backend.sh" > "$PROJECT_ROOT/data/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "✓ Backend запущен (PID: $BACKEND_PID) -> http://127.0.0.1:8000"

# Wait for backend health check
echo "Ожидание готовности backend API..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
        echo "✓ Backend API готов к работе!"
        break
    fi
    sleep 0.5
done

# Start Frontend
"$SCRIPT_DIR/start_frontend.sh" > "$PROJECT_ROOT/data/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend запущен (PID: $FRONTEND_PID) -> http://127.0.0.1:5173"

echo "----------------------------------------------------------"
echo "Приложение доступно в браузере:"
echo "👉 http://127.0.0.1:5173"
echo "API Документация (Swagger):"
echo "👉 http://127.0.0.1:8000/docs"
echo "----------------------------------------------------------"
echo "Нажмите [Ctrl+C] для остановки."

wait
