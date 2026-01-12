#!/bin/bash
cd "$(dirname "$0")"

# Проверка наличия venv
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./deploy.sh first."
    exit 1
fi

source venv/bin/activate
exec python main.py
