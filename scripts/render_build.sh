#!/usr/bin/env bash
set -e

# Render Native Python build script
echo "=== 1. Установка backend зависимостей ==="
pip install -r backend/requirements.txt

echo "=== 2. Сборка frontend (Vite React) ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 3. Подготовка директорий хранения ==="
mkdir -p data/uploads data/backups data/logs

echo "✓ Сборка для Render успешно завершена!"
