#!/usr/bin/env bash
set -e

echo "Остановка публичного интернет-туннеля..."
pkill -f "cloudflared tunnel --url" 2>/dev/null || true
echo "✓ Публичный доступ через интернет отключен."
echo "Сайт по-прежнему доступен локально: http://127.0.0.1:8000"
