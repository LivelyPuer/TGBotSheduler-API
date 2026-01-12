#!/bin/bash

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# Определение пользователя и путей
REAL_USER=${SUDO_USER:-$USER}
# Если скрипт запущен через sudo, но SUDO_USER не определен, берем владельца текущей папки
if [ -z "$REAL_USER" ]; then
    REAL_USER=$(ls -ld . | awk '{print $3}')
fi

PROJECT_DIR=$(pwd)
SERVICE_NAME="bot_scheduler"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
ENV_FILE="$PROJECT_DIR/.env"

echo "🔧 Setting up systemd service for $SERVICE_NAME..."
echo "   User: $REAL_USER"
echo "   Dir:  $PROJECT_DIR"

# 1. Проверка наличия python в venv
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found at $PYTHON_PATH"
    echo "   Please run ./deploy.sh first"
    exit 1
fi

# 2. Проверка наличия .env
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  WARNING: .env file not found at $ENV_FILE"
    echo "   Creating a template .env file..."
    echo "BOT_TOKEN=your_token_here" > "$ENV_FILE"
    echo "   Please edit $ENV_FILE before using the bot."
fi

# 3. Создание файла службы
# Примечание: Убрали Group, чтобы systemd использовал группу по умолчанию для пользователя
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOL
[Unit]
Description=Telegram Bot Scheduler API
After=network.target

[Service]
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/main.py
Restart=always
RestartSec=5
EnvironmentFile=$ENV_FILE
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

# 4. Перезагрузка и запуск
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

echo "▶️ Enabling and starting service..."
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

# 5. Проверка статуса
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service installed and started successfully!"
else
    echo "❌ Service failed to start. Checking logs..."
    journalctl -u $SERVICE_NAME -n 10 --no-pager
    echo "---------------------------------------------------"
    echo "👉 Check the error logs above."
    echo "👉 Make sure your .env file is correct."
    echo "👉 Make sure $REAL_USER has permissions to access $PROJECT_DIR"
fi
