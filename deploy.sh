#!/bin/bash
set -e

echo "🚀 Starting deployment setup..."

# 1. Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists."
fi

# 2. Установка зависимостей
echo "⬇️ Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Создание папки для медиа
mkdir -p media

echo "✅ Deployment setup complete!"
echo "---------------------------------------------------"
echo "👉 To run manually: ./run.sh"
echo "👉 To setup autostart (Linux systemd): sudo ./setup_service.sh"
echo "---------------------------------------------------"
