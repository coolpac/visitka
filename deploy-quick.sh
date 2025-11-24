#!/bin/bash
# Быстрый деплой только измененных файлов для исправления белого пространства

SERVER="root@81.200.153.155"
REMOTE_DIR="/var/www/annaivaschenko.ru"

echo "🚀 Быстрый деплой исправлений..."
echo "Сервер: $SERVER"
echo ""

# Обновляем версию файлов для обхода кеша
echo "🔄 Обновление версии файлов..."
./update-version.sh

# Копируем только измененные файлы
echo "📦 Копирование файлов..."
scp styles.css "$SERVER:$REMOTE_DIR/styles.css"
scp telegram-webapp.js "$SERVER:$REMOTE_DIR/telegram-webapp.js"
scp debug-panel.js "$SERVER:$REMOTE_DIR/debug-panel.js"
scp index.html "$SERVER:$REMOTE_DIR/index.html"

# Настройка прав
echo "🔐 Настройка прав доступа..."
ssh "$SERVER" "chown www-data:www-data $REMOTE_DIR/styles.css $REMOTE_DIR/telegram-webapp.js $REMOTE_DIR/debug-panel.js $REMOTE_DIR/index.html"
ssh "$SERVER" "chmod 644 $REMOTE_DIR/styles.css $REMOTE_DIR/telegram-webapp.js $REMOTE_DIR/debug-panel.js $REMOTE_DIR/index.html"

# Обновление nginx конфигурации (если изменилась)
echo "🌐 Проверка конфигурации Nginx..."
if [ -f "deploy/nginx.conf" ]; then
    echo "📝 Копирование обновленной конфигурации Nginx..."
    scp deploy/nginx.conf "$SERVER:/tmp/annaivaschenko.ru.conf"
    ssh "$SERVER" << 'ENDSSH'
        sudo mv /tmp/annaivaschenko.ru.conf /etc/nginx/sites-available/annaivaschenko.ru
        sudo nginx -t && sudo systemctl reload nginx
        echo "✅ Nginx конфигурация обновлена"
ENDSSH
fi

echo ""
echo "✅ Деплой завершен!"
echo ""
echo "Проверьте сайт: https://annaivaschenko.ru"
echo "Проверьте мини-приложение в Telegram - белое пространство должно исчезнуть!"
echo ""
echo "🐛 Debug Panel доступна:"
echo "   - Кнопка 🐛 в правом нижнем углу (всегда видна)"
echo "   - Тройной тап по экрану"
echo "   - Добавьте ?debug=1 в URL для автоматического открытия"

