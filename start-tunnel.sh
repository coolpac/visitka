#!/bin/bash

# Скрипт для запуска Cloudflare Tunnel для тестирования
# Использование: ./start-tunnel.sh [порт]

PORT=${1:-8000}

echo "🚀 Запуск Cloudflare Tunnel для тестирования..."
echo "📡 Локальный порт: $PORT"
echo ""

# Проверяем, установлен ли cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared не установлен!"
    echo ""
    echo "Установите cloudflared:"
    echo "  macOS: brew install cloudflared"
    echo "  или скачайте с: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

# Проверяем, запущен ли локальный сервер
if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Локальный сервер на порту $PORT не запущен"
    echo "Запускаю простой HTTP сервер..."
    
    # Запускаем Python HTTP сервер в фоне
    if command -v python3 &> /dev/null; then
        python3 -m http.server $PORT > /dev/null 2>&1 &
        SERVER_PID=$!
        echo "✅ HTTP сервер запущен (PID: $SERVER_PID)"
        sleep 2
    else
        echo "❌ Python3 не найден. Запустите локальный сервер вручную на порту $PORT"
        exit 1
    fi
else
    echo "✅ Локальный сервер уже запущен на порту $PORT"
    SERVER_PID=""
fi

echo ""
echo "🌐 Запуск Cloudflare Tunnel..."
echo "   (Нажмите Ctrl+C для остановки)"
echo ""

# Запускаем Cloudflare Tunnel (quick tunnel - бесплатный, без регистрации)
cloudflared tunnel --url http://localhost:$PORT

# Останавливаем локальный сервер, если мы его запустили
if [ ! -z "$SERVER_PID" ]; then
    echo ""
    echo "🛑 Остановка локального сервера..."
    kill $SERVER_PID 2>/dev/null
fi

