#!/bin/bash
# Скрипт для управления Docker контейнерами чата

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен"
        print_status "Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        print_status "Установите Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

build_images() {
    print_status "Сборка Docker образов..."
    docker-compose build --no-cache
    print_success "Образы собраны!"
}

start_services() {
    print_status "Запуск сервисов..."
    
    # Создать конфигурационный файл если его нет
    if [ ! -f "config.py" ]; then
        print_status "Создание конфигурационного файла..."
        cp config_example.py config.py
    fi
    
    docker-compose up -d
    print_success "Сервисы запущены!"
    
    # Показать статус
    echo
    print_status "Статус сервисов:"
    docker-compose ps
    
    echo
    print_status "Для подключения к чату используйте:"
    echo "python3 client.py <IP_сервера> 12345"
}

stop_services() {
    print_status "Остановка сервисов..."
    docker-compose down
    print_success "Сервисы остановлены!"
}

restart_services() {
    print_status "Перезапуск сервисов..."
    docker-compose restart
    print_success "Сервисы перезапущены!"
}

show_logs() {
    if [ "$1" = "follow" ] || [ "$1" = "-f" ]; then
        docker-compose logs -f terminal-chat-server
    else
        docker-compose logs --tail=50 terminal-chat-server
    fi
}

show_status() {
    echo "=== Статус контейнеров ==="
    docker-compose ps
    echo
    echo "=== Использование ресурсов ==="
    docker stats --no-stream terminal-chat-server 2>/dev/null || echo "Контейнер не запущен"
}

cleanup() {
    print_warning "Это удалит все контейнеры, образы и данные!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Остановка и удаление контейнеров..."
        docker-compose down -v --rmi all
        
        print_status "Удаление неиспользуемых образов..."
        docker image prune -f
        
        print_success "Очистка завершена!"
    else
        print_status "Очистка отменена"
    fi
}

backup_data() {
    BACKUP_DIR="./backups"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/chat_backup_$TIMESTAMP.tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    print_status "Создание резервной копии данных..."
    
    # Найти том данных
    VOLUME_NAME=$(docker-compose config --volumes | grep chat_data || echo "terminal-chat_chat_data")
    
    # Создать временный контейнер для доступа к данным
    docker run --rm \
        -v "$VOLUME_NAME:/data" \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine:latest \
        tar -czf "/backup/chat_backup_$TIMESTAMP.tar.gz" -C /data .
    
    print_success "Резервная копия создана: $BACKUP_FILE"
}

restore_data() {
    if [ -z "$1" ]; then
        print_error "Укажите файл резервной копии"
        print_status "Использование: $0 restore <файл_резервной_копии>"
        return 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Файл резервной копии не найден: $1"
        return 1
    fi
    
    print_warning "Это перезапишет все текущие данные!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Восстановление данных из $1..."
        
        # Найти том данных
        VOLUME_NAME=$(docker-compose config --volumes | grep chat_data || echo "terminal-chat_chat_data")
        
        # Восстановить данные
        docker run --rm \
            -v "$VOLUME_NAME:/data" \
            -v "$(realpath $1):/backup.tar.gz" \
            alpine:latest \
            sh -c "cd /data && tar -xzf /backup.tar.gz"
        
        print_success "Данные восстановлены!"
        print_status "Перезапустите сервисы: $0 restart"
    else
        print_status "Восстановление отменено"
    fi
}

update_services() {
    print_status "Обновление сервисов..."
    
    # Остановить сервисы
    docker-compose down
    
    # Пересобрать образы
    docker-compose build --no-cache
    
    # Запустить сервисы
    docker-compose up -d
    
    print_success "Сервисы обновлены и запущены!"
}

show_help() {
    echo "Скрипт управления Docker сервисами терминального чата"
    echo
    echo "Использование: $0 {команда} [параметры]"
    echo
    echo "Команды:"
    echo "  build       - Собрать Docker образы"
    echo "  start       - Запустить сервисы"
    echo "  stop        - Остановить сервисы"
    echo "  restart     - Перезапустить сервисы"
    echo "  status      - Показать статус сервисов"
    echo "  logs        - Показать логи сервиса"
    echo "  logs follow - Показать логи в реальном времени"
    echo "  backup      - Создать резервную копию данных"
    echo "  restore     - Восстановить данные из резервной копии"
    echo "  update      - Обновить и перезапустить сервисы"
    echo "  cleanup     - Удалить все контейнеры и данные"
    echo "  help        - Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 build && $0 start    # Собрать и запустить"
    echo "  $0 logs follow          # Следить за логами"
    echo "  $0 backup               # Создать резервную копию"
    echo "  $0 restore backup.tar.gz # Восстановить данные"
}

# Проверить Docker
check_docker

# Обработка команд
case "$1" in
    build)
        build_images
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        if [ "$2" = "follow" ] || [ "$2" = "-f" ]; then
            show_logs follow
        else
            show_logs
        fi
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    update)
        update_services
        ;;
    cleanup)
        cleanup
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