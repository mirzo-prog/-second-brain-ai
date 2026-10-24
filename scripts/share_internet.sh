#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$PROJECT_ROOT/data/logs"
CLOUDFLARED="$HOME/.local/bin/cloudflared"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

# Ensure cloudflared binary is installed
if [ ! -f "$CLOUDFLARED" ]; then
    echo "Загрузка Cloudflare Tunnel..."
    mkdir -p "$HOME/.local/bin"
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "$CLOUDFLARED"
    chmod +x "$CLOUDFLARED"
fi

# Ensure Backend Server is running
if ! curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "Запуск локального сервера Second Brain AI..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/server.log" 2>&1 &
    sleep 2
fi

# Stop previous tunnel if running
pkill -f "cloudflared tunnel --url" 2>/dev/null || true
sleep 0.5

# Start Cloudflare Tunnel
echo "Создание защищенного публичного интернет-соединения (HTTPS)..."
rm -f "$LOG_DIR/tunnel.log"
nohup "$CLOUDFLARED" tunnel --url http://127.0.0.1:8000 > "$LOG_DIR/tunnel.log" 2>&1 &

# Wait for tunnel URL
PUBLIC_URL=""
for i in {1..30}; do
    if [ -f "$LOG_DIR/tunnel.log" ]; then
        PUBLIC_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]*\.trycloudflare\.com' "$LOG_DIR/tunnel.log" | head -n 1 || true)
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
    fi
    sleep 0.5
done

LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || hostname -I | awk '{print $1}')

echo ""
echo "=========================================================================="
echo "          🎉 САЙТ SECOND BRAIN AI ПОДКЛЮЧЕН К ИНТЕРНЕТУ!                 "
echo "=========================================================================="
echo ""
if [ -n "$PUBLIC_URL" ]; then
    echo "🌍 1. ПУБЛИЧНАЯ ССЫЛКА (доступна для всех из любой точки мира):"
    echo "   👉 $PUBLIC_URL"
    echo "   (Отправьте эту ссылку друзьям, коллегам или откройте на телефоне)"
    echo ""
fi

echo "🏠 2. ЛОКАЛЬНАЯ ССЫЛКА В ВАШЕЙ СЕТИ WI-FI:"
echo "   👉 http://${LOCAL_IP}:8000"
echo "   (Для любых устройств, подключенных к вашему домашнему Wi-Fi)"
echo ""
echo "💻 3. НА ЭТОМ КОМПЬЮТЕРЕ:"
echo "   👉 http://127.0.0.1:8000"
echo ""
echo "--------------------------------------------------------------------------"
echo "Чтобы остановить общий доступ в интернет, выполните:"
echo "   $SCRIPT_DIR/stop_internet.sh"
echo "=========================================================================="
