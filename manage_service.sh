#!/bin/bash
# Скрипт управления сервером терминального чата

SERVICE_NAME="terminal-chat"
INSTALL_DIR="/opt/terminal-chat"
USER="chatuser"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен запускаться с правами root"
        print_status "Используйте: sudo $0 $1"
        exit 1
    fi
}

check_service_exists() {
    if ! systemctl list-units --full -all | grep -Fq "$SERVICE_NAME.service"; then
        print_error "Сервис $SERVICE_NAME не установлен"
        print_status "Используйте: $0 install"
        exit 1
    fi
}

install_service() {
    check_root
    print_status "Установка сервиса терминального чата..."
    
    # Создать пользователя для сервиса
    if ! id "$USER" &>/dev/null; then
        print_status "Создание пользователя $USER..."
        useradd --system --home-dir "$INSTALL_DIR" --shell /bin/false "$USER"
    fi
    
    # Создать директорию установки
    print_status "Создание директории $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    
    # Копировать файлы
    print_status "Копирование файлов..."
    cp server.py "$INSTALL_DIR/"
    cp config_example.py "$INSTALL_DIR/config.py"
    cp .env.example "$INSTALL_DIR/.env"
    
    # Установить права
    chown -R "$USER:$USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 644 "$INSTALL_DIR"/*.py
    chmod 600 "$INSTALL_DIR/.env"
    
    # Установить systemd service
    print_status "Установка systemd service..."
    cp terminal-chat.service "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_success "Сервис успешно установлен!"
    print_status "Настройте конфигурацию в $INSTALL_DIR/config.py"
    print_status "Настройте переменные окружения в $INSTALL_DIR/.env"
    print_status "Для запуска используйте: $0 start"
}

uninstall_service() {
    check_root
    print_status "Удаление сервиса терминального чата..."
    
    # Остановить и отключить сервис
    if systemctl list-units --full -all | grep -Fq "$SERVICE_NAME.service"; then
        systemctl stop "$SERVICE_NAME" 2>/dev/null
        systemctl disable "$SERVICE_NAME" 2>/dev/null
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
    fi
    
    # Удалить файлы (с подтверждением)
    if [ -d "$INSTALL_DIR" ]; then
        read -p "Удалить директорию $INSTALL_DIR? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            print_status "Директория $INSTALL_DIR удалена"
        fi
    fi
    
    # Удалить пользователя (с подтверждением)
    if id "$USER" &>/dev/null; then
        read -p "Удалить пользователя $USER? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            userdel "$USER" 2>/dev/null
            print_status "Пользователь $USER удален"
        fi
    fi
    
    print_success "Сервис удален!"
}

start_service() {
    check_root
    check_service_exists
    print_status "Запуск сервиса..."
    systemctl start "$SERVICE_NAME"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Сервис запущен!"
    else
        print_error "Не удалось запустить сервис"
        exit 1
    fi
}

stop_service() {
    check_root
    check_service_exists
    print_status "Остановка сервиса..."
    systemctl stop "$SERVICE_NAME"
    print_success "Сервис остановлен!"
}

restart_service() {
    check_root
    check_service_exists
    print_status "Перезапуск сервиса..."
    systemctl restart "$SERVICE_NAME"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Сервис перезапущен!"
    else
        print_error "Не удалось перезапустить сервис"
        exit 1
    fi
}

status_service() {
    check_service_exists
    echo "=== Статус сервиса ==="
    systemctl status "$SERVICE_NAME" --no-pager
    echo
    echo "=== Последние логи ==="
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
}

show_logs() {
    check_service_exists
    if [ "$2" = "follow" ] || [ "$2" = "-f" ]; then
        journalctl -u "$SERVICE_NAME" -f
    else
        journalctl -u "$SERVICE_NAME" --no-pager -n 50
    fi
}

show_help() {
    echo "Скрипт управления сервером терминального чата"
    echo
    echo "Использование: $0 {команда}"
    echo
    echo "Команды:"
    echo "  install     - Установить сервис в систему"
    echo "  uninstall   - Удалить сервис из системы"
    echo "  start       - Запустить сервис"
    echo "  stop        - Остановить сервис"
    echo "  restart     - Перезапустить сервис"
    echo "  status      - Показать статус сервиса"
    echo "  logs        - Показать логи сервиса"
    echo "  logs follow - Показать логи в реальном времени"
    echo "  help        - Показать эту справку"
    echo
    echo "Примеры:"
    echo "  sudo $0 install    # Установить сервис"
    echo "  sudo $0 start      # Запустить сервис"
    echo "  $0 status          # Проверить статус"
    echo "  $0 logs follow     # Следить за логами"
}

# Обработка аргументов
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Неизвестная команда: $1"
        echo
        show_help
        exit 1
        ;;
esac