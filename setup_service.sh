#!/bin/bash

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# Определение пользователя и путей
REAL_USER=${SUDO_USER:-$USER}
PROJECT_DIR=$(pwd)
SERVICE_NAME="bot_scheduler"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"

echo "🔧 Setting up systemd service for $SERVICE_NAME..."
echo "   User: $REAL_USER"
echo "   Dir:  $PROJECT_DIR"

# Проверка наличия python в venv
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found at $PYTHON_PATH"
    echo "   Please run ./deploy.sh first"
    exit 1
fi

# Создание файла службы
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOL
[Unit]
Description=Telegram Bot Scheduler API
After=network.target

[Service]
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/main.py
Restart=always
RestartSec=5
EnvironmentFile=$PROJECT_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка и запуск
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

echo "▶️ Enabling and starting service..."
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "✅ Service installed and started!"
echo "---------------------------------------------------"
echo "📊 Status: systemctl status $SERVICE_NAME"
echo "📜 Logs:   journalctl -u $SERVICE_NAME -f"
echo "🛑 Stop:   sudo systemctl stop $SERVICE_NAME"
echo "---------------------------------------------------"
