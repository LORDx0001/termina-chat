#!/bin/bash
# Скрипт для быстрого деплоя через SSH (без GitHub Actions)

set -e

# Конфигурация
SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22}"
DEPLOY_PATH="/opt/terminal-chat"
SERVICE_NAME="terminal-chat"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ -z "$SERVER_IP" ]; then
    read -p "IP адрес сервера: " SERVER_IP
fi

if [ -z "$SERVER_USER" ]; then
    read -p "Пользователь SSH (по умолчанию: root): " INPUT_USER
    SERVER_USER=${INPUT_USER:-root}
fi

print_status "Деплой на $SERVER_USER@$SERVER_IP:$SERVER_PORT"

# Создать архив
print_status "Создание архива..."
tar -czf terminal-chat.tar.gz \
    server.py server_production.py client.py \
    config_example.py .env.example requirements.txt \
    terminal-chat.service manage_service.sh \
    docker-compose.yml Dockerfile \
    --exclude='.git' --exclude='*.log' --exclude='chat_data.json'

# Копировать на сервер
print_status "Копирование файлов на сервер..."
scp -P "$SERVER_PORT" terminal-chat.tar.gz "$SERVER_USER@$SERVER_IP:/tmp/"

# Выполнить деплой
print_status "Выполнение деплоя на сервере..."
ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_IP" << 'EOF'
    set -e
    
    # Создать резервную копию
    if [ -d "/opt/terminal-chat" ]; then
        sudo cp -r /opt/terminal-chat /opt/terminal-chat.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Создать директорию
    sudo mkdir -p /opt/terminal-chat
    
    # Распаковать
    cd /tmp
    tar -xzf terminal-chat.tar.gz
    
    # Остановить сервис
    sudo systemctl stop terminal-chat 2>/dev/null || true
    
    # Копировать файлы
    sudo cp *.py /opt/terminal-chat/
    sudo cp requirements.txt /opt/terminal-chat/ 2>/dev/null || true
    
    # Создать конфиг если не существует
    if [ ! -f "/opt/terminal-chat/config.py" ]; then
        sudo cp config_example.py /opt/terminal-chat/config.py
    fi
    
    if [ ! -f "/opt/terminal-chat/.env" ]; then
        sudo cp .env.example /opt/terminal-chat/.env 2>/dev/null || true
    fi
    
    # Создать пользователя
    if ! id chatuser >/dev/null 2>&1; then
        sudo useradd --system --home-dir /opt/terminal-chat --shell /bin/false chatuser
    fi
    
    # Права доступа
    sudo chown -R chatuser:chatuser /opt/terminal-chat
    sudo chmod 755 /opt/terminal-chat
    sudo chmod 644 /opt/terminal-chat/*.py
    
    # Systemd сервис
    sudo cp terminal-chat.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable terminal-chat
    sudo systemctl start terminal-chat
    
    # Проверка
    sleep 2
    if sudo systemctl is-active --quiet terminal-chat; then
        echo "✅ Сервис запущен успешно"
    else
        echo "❌ Ошибка запуска сервиса"
        sudo journalctl -u terminal-chat --no-pager -n 10
    fi
    
    # Очистка
    rm -f /tmp/terminal-chat.tar.gz /tmp/*.py /tmp/*.service
    
    echo "🎉 Деплой завершен!"
EOF

# Очистка локального архива
rm -f terminal-chat.tar.gz

print_success "Деплой завершен!"
print_status "Подключение к чату: python3 client.py $SERVER_IP 12345"