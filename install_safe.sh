#!/bin/bash

# Terminal Chat - Установка для систем с защищенным Python (PEP 668)
# Автор: LORDx0001
# Версия: 1.0

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка прав суперпользователя
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен запускаться с правами root (sudo)"
   exit 1
fi

# Заголовок
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     Terminal Chat - Безопасная установка           ║"
echo "║          для систем с PEP 668                     ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

log "Начинаем установку Terminal Chat..."

# Определение переменных
INSTALL_DIR="/opt/terminal-chat"
SERVICE_USER="terminalchat"
SERVICE_FILE="/etc/systemd/system/terminal-chat.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Проверка наличия необходимых файлов
log "Проверка файлов проекта..."

required_files=("server_production.py" "terminal-chat.service")
missing_files=()

for file in "${required_files[@]}"; do
    if [[ -f "$SCRIPT_DIR/$file" ]]; then
        success "Файл $file найден"
    else
        error "Файл $file отсутствует в $SCRIPT_DIR"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    error "Отсутствуют обязательные файлы: ${missing_files[*]}"
    error "Убедитесь, что вы запускаете скрипт из корневой директории проекта"
    exit 1
fi

# Проверка Python и стандартных библиотек
log "Проверка Python окружения..."

if ! command -v python3 >/dev/null 2>&1; then
    error "Python 3 не установлен"
    log "Установка Python 3..."
    
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        apt-get install -y python3 python3-full
    elif command -v yum >/dev/null 2>&1; then
        yum install -y python3
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y python3
    else
        error "Неподдерживаемый пакетный менеджер"
        exit 1
    fi
fi

success "Python 3 доступен: $(python3 --version)"

# Проверка стандартных библиотек (они должны быть всегда)
log "Проверка стандартных Python библиотек..."
if python3 -c "import socket, threading, json, datetime, time, sys, os" >/dev/null 2>&1; then
    success "Все необходимые модули доступны"
else
    error "Критическая ошибка: недоступны стандартные Python модули"
    exit 1
fi

# НЕ ПЫТАЕМСЯ устанавливать пакеты через pip - они не нужны!
log "Terminal Chat использует ТОЛЬКО стандартные библиотеки Python"
success "Никаких дополнительных зависимостей не требуется!"

# Создание пользователя сервиса
log "Создание пользователя сервиса..."
if id "$SERVICE_USER" &>/dev/null; then
    success "Пользователь $SERVICE_USER уже существует"
else
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    success "Пользователь $SERVICE_USER создан"
fi

# Создание директорий
log "Создание директорий..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"

# Копирование файлов
log "Копирование файлов проекта..."
cp "$SCRIPT_DIR/server_production.py" "$INSTALL_DIR/server.py"
chmod +x "$INSTALL_DIR/server.py"

# Создание конфигурационных файлов
log "Создание конфигурации..."

# Создаем простой конфиг если нужно
if [[ ! -f "$INSTALL_DIR/config.py" ]]; then
    cat > "$INSTALL_DIR/config.py" << 'EOF'
# Terminal Chat Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 12345
MAX_CONNECTIONS = 100
LOG_LEVEL = "INFO"
DATA_DIR = "/opt/terminal-chat/data"
LOGS_DIR = "/opt/terminal-chat/logs"
EOF
    success "Создан файл конфигурации"
fi

# Установка прав доступа
log "Установка прав доступа..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR/server.py" "$INSTALL_DIR/config.py"
chmod 755 "$INSTALL_DIR/data" "$INSTALL_DIR/logs"

# Установка systemd сервиса
log "Установка systemd сервиса..."
cp "$SCRIPT_DIR/terminal-chat.service" "$SERVICE_FILE"

# Перезагрузка systemd и запуск сервиса
log "Настройка сервиса..."
systemctl daemon-reload
systemctl enable terminal-chat

# Настройка файрвола
log "Настройка файрвола..."
if command -v ufw >/dev/null 2>&1; then
    ufw --force enable
    ufw allow 12345/tcp
    success "Порт 12345 открыт через ufw"
elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=12345/tcp
    firewall-cmd --reload
    success "Порт 12345 открыт через firewalld"
else
    warning "Файрвол не обнаружен, убедитесь что порт 12345 открыт"
fi

# Запуск сервиса
log "Запуск Terminal Chat сервиса..."
systemctl start terminal-chat

# Проверка статуса
sleep 2
if systemctl is-active --quiet terminal-chat; then
    success "Сервис Terminal Chat успешно запущен!"
else
    error "Не удалось запустить сервис"
    log "Проверьте логи: journalctl -u terminal-chat"
    exit 1
fi

# Финальная информация
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║            🎉 УСТАНОВКА ЗАВЕРШЕНА! 🎉              ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "📍 Сервер запущен на порту: 12345"
echo "📁 Установлен в: $INSTALL_DIR"
echo "👤 Пользователь сервиса: $SERVICE_USER"
echo ""
echo "🔧 Управление сервисом:"
echo "   sudo systemctl start terminal-chat    # запуск"
echo "   sudo systemctl stop terminal-chat     # остановка" 
echo "   sudo systemctl restart terminal-chat  # перезапуск"
echo "   sudo systemctl status terminal-chat   # статус"
echo ""
echo "📊 Мониторинг:"
echo "   sudo journalctl -u terminal-chat -f   # логи в реальном времени"
echo "   sudo netstat -tulpn | grep :12345     # проверка порта"
echo ""
echo "🚀 Подключение клиентов:"
echo "   python3 client.py"
echo "   Адрес: $(hostname -I | awk '{print $1}'):12345"
echo ""
success "Terminal Chat готов к работе!"