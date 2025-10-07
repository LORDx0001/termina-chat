#!/bin/bash
# Универсальный скрипт установки терминального чата
# Поддерживает Ubuntu/Debian, CentOS/RHEL, и другие дистрибутивы

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/terminal-chat"
SERVICE_USER="chatuser"
SERVICE_NAME="terminal-chat"

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

print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}    УСТАНОВКА ТЕРМИНАЛЬНОГО ЧАТА${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/redhat-release ]; then
        OS="Red Hat Enterprise Linux"
        VER=$(grep -oE '[0-9]+\.[0-9]+' /etc/redhat-release)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    print_status "Обнаружена ОС: $OS $VER"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен запускаться с правами root"
        print_status "Используйте: sudo $0"
        exit 1
    fi
}

install_dependencies() {
    print_status "Установка зависимостей..."
    
    case "$OS" in
        *"Ubuntu"*|*"Debian"*)
            apt-get update
            apt-get install -y python3 python3-pip git curl wget
            ;;
        *"CentOS"*|*"Red Hat"*|*"Fedora"*)
            if command -v dnf >/dev/null; then
                dnf install -y python3 python3-pip git curl wget
            else
                yum install -y python3 python3-pip git curl wget
            fi
            ;;
        *"openSUSE"*)
            zypper install -y python3 python3-pip git curl wget
            ;;
        *"Arch"*)
            pacman -S --noconfirm python python-pip git curl wget
            ;;
        *)
            print_warning "Неизвестная ОС. Попытка установки через общие команды..."
            if command -v apt-get >/dev/null; then
                apt-get update && apt-get install -y python3 python3-pip git curl wget
            elif command -v yum >/dev/null; then
                yum install -y python3 python3-pip git curl wget
            else
                print_error "Не удалось определить пакетный менеджер"
                print_status "Установите вручную: python3, python3-pip, git, curl, wget"
                exit 1
            fi
            ;;
    esac
    
    print_success "Зависимости установлены"
}

create_user() {
    print_status "Создание пользователя для сервиса..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --home-dir "$INSTALL_DIR" --shell /bin/false "$SERVICE_USER"
        print_success "Пользователь $SERVICE_USER создан"
    else
        print_status "Пользователь $SERVICE_USER уже существует"
    fi
}

install_chat_server() {
    print_status "Установка сервера чата..."
    
    # Получить абсолютный путь к директории скрипта
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    
    # Создать директорию установки
    mkdir -p "$INSTALL_DIR"
    
    # Если это Git репозиторий, клонируем его
    if [ -n "$REPO_URL" ]; then
        print_status "Клонирование из репозитория: $REPO_URL"
        cd "$INSTALL_DIR"
        git clone "$REPO_URL" .
    else
        # Иначе копируем локальные файлы
        if [ -f "$SCRIPT_DIR/server.py" ]; then
            print_status "Копирование локальных файлов из $SCRIPT_DIR..."
            cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"
            cp "$SCRIPT_DIR"/requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
            cp "$SCRIPT_DIR"/config_example.py "$INSTALL_DIR/config.py" 2>/dev/null || true
            cp "$SCRIPT_DIR"/.env.example "$INSTALL_DIR/.env" 2>/dev/null || true
        else
            print_error "Файлы сервера не найдены в $SCRIPT_DIR"
            print_status "Проверьте что файлы server.py, client.py находятся в той же директории что и install.sh"
            print_status "Или укажите URL репозитория: REPO_URL=https://github.com/user/repo $0"
            exit 1
        fi
    fi
    
    # Установить Python зависимости
    if [ -f requirements.txt ]; then
        print_status "Установка Python зависимостей..."
        pip3 install -r requirements.txt
    fi
    
    # Создать конфигурационные файлы
    if [ ! -f config.py ] && [ -f config_example.py ]; then
        cp config_example.py config.py
    fi
    
    if [ ! -f .env ] && [ -f .env.example ]; then
        cp .env.example .env
    fi
    
    # Установить права
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 644 "$INSTALL_DIR"/*.py
    [ -f .env ] && chmod 600 "$INSTALL_DIR/.env"
    
    print_success "Сервер чата установлен в $INSTALL_DIR"
}

install_systemd_service() {
    print_status "Установка systemd сервиса..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Terminal Chat Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/server.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Ресурсы
LimitNOFILE=65536
MemoryMax=512M
CPUQuota=200%

# Переменные окружения
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd сервис установлен"
}

configure_firewall() {
    print_status "Настройка файрвола..."
    
    # Получить порт из конфигурации
    PORT=$(grep -E '^PORT\s*=' "$INSTALL_DIR/config.py" 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "12345")
    
    # UFW (Ubuntu/Debian)
    if command -v ufw >/dev/null; then
        ufw allow "$PORT/tcp" >/dev/null 2>&1 || true
        print_status "Добавлено правило UFW для порта $PORT"
    fi
    
    # firewalld (CentOS/RHEL/Fedora)
    if command -v firewall-cmd >/dev/null; then
        firewall-cmd --permanent --add-port="$PORT/tcp" >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
        print_status "Добавлено правило firewalld для порта $PORT"
    fi
    
    # iptables (fallback)
    if command -v iptables >/dev/null && ! command -v ufw >/dev/null && ! command -v firewall-cmd >/dev/null; then
        iptables -A INPUT -p tcp --dport "$PORT" -j ACCEPT >/dev/null 2>&1 || true
        # Попытаться сохранить правила
        if command -v iptables-save >/dev/null; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        print_status "Добавлено правило iptables для порта $PORT"
    fi
    
    print_success "Файрвол настроен для порта $PORT"
}

create_management_script() {
    print_status "Создание скрипта управления..."
    
    # Копируем скрипт управления если он есть
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    if [ -f "$SCRIPT_DIR/manage_service.sh" ]; then
        cp "$SCRIPT_DIR/manage_service.sh" "/usr/local/bin/terminal-chat"
        chmod +x "/usr/local/bin/terminal-chat"
        print_status "Скрипт управления установлен: /usr/local/bin/terminal-chat"
    fi
}

start_service() {
    print_status "Запуск сервиса..."
    
    systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Сервис запущен успешно!"
    else
        print_error "Не удалось запустить сервис"
        print_status "Проверьте логи: journalctl -u $SERVICE_NAME"
        exit 1
    fi
}

show_installation_info() {
    PORT=$(grep -E '^PORT\s*=' "$INSTALL_DIR/config.py" 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "12345")
    IP=$(curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')
    
    echo
    print_success "УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!"
    echo
    echo -e "${YELLOW}=== ИНФОРМАЦИЯ О СЕРВЕРЕ ===${NC}"
    echo -e "Директория установки: ${BLUE}$INSTALL_DIR${NC}"
    echo -e "Пользователь сервиса:  ${BLUE}$SERVICE_USER${NC}"
    echo -e "Служба systemd:        ${BLUE}$SERVICE_NAME${NC}"
    echo -e "Порт сервера:          ${BLUE}$PORT${NC}"
    echo -e "IP сервера:            ${BLUE}$IP${NC}"
    echo
    echo -e "${YELLOW}=== КОМАНДЫ УПРАВЛЕНИЯ ===${NC}"
    echo -e "Запуск:    ${GREEN}systemctl start $SERVICE_NAME${NC}"
    echo -e "Остановка: ${GREEN}systemctl stop $SERVICE_NAME${NC}"
    echo -e "Статус:    ${GREEN}systemctl status $SERVICE_NAME${NC}"
    echo -e "Логи:      ${GREEN}journalctl -u $SERVICE_NAME -f${NC}"
    echo
    echo -e "${YELLOW}=== ПОДКЛЮЧЕНИЕ К ЧАТУ ===${NC}"
    echo -e "Из локальной сети: ${GREEN}python3 client.py $IP $PORT${NC}"
    echo -e "С сервера:         ${GREEN}python3 client.py localhost $PORT${NC}"
    echo
    echo -e "${YELLOW}=== КОНФИГУРАЦИЯ ===${NC}"
    echo -e "Основная конфигурация: ${BLUE}$INSTALL_DIR/config.py${NC}"
    echo -e "Переменные окружения:  ${BLUE}$INSTALL_DIR/.env${NC}"
    echo
    echo -e "${YELLOW}=== БЕЗОПАСНОСТЬ ===${NC}"
    echo -e "• Откройте порт $PORT в файрволе облачного провайдера"
    echo -e "• Измените пароли в конфигурации"
    echo -e "• Рассмотрите использование SSL/TLS"
    echo
}

# Обработка аргументов
case "${1:-}" in
    --help|-h)
        echo "Скрипт установки терминального чата"
        echo
        echo "Использование: $0 [опции]"
        echo
        echo "Переменные окружения:"
        echo "  REPO_URL    - URL Git репозитория для клонирования"
        echo "  SKIP_DEPS   - Пропустить установку зависимостей"
        echo "  SKIP_FW     - Пропустить настройку файрвола"
        echo
        echo "Примеры:"
        echo "  $0                           # Установка с локальными файлами"
        echo "  REPO_URL=https://github.com/user/repo $0  # Установка из Git"
        echo "  SKIP_DEPS=1 $0              # Пропустить установку зависимостей"
        exit 0
        ;;
    --uninstall)
        print_status "Удаление терминального чата..."
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
        read -p "Удалить директорию $INSTALL_DIR? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        fi
        read -p "Удалить пользователя $SERVICE_USER? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            userdel "$SERVICE_USER" 2>/dev/null || true
        fi
        print_success "Удаление завершено"
        exit 0
        ;;
esac

# Основная установка
print_header
detect_os
check_root

if [ -z "$SKIP_DEPS" ]; then
    install_dependencies
fi

create_user
install_chat_server
install_systemd_service

if [ -z "$SKIP_FW" ]; then
    configure_firewall
fi

create_management_script
start_service
show_installation_info

print_success "Установка завершена! Сервер чата готов к использованию."