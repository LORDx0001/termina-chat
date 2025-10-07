#!/bin/bash
# Скрипт для настройки CI/CD secrets в GitHub

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

print_header() {
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}    НАСТРОЙКА CI/CD SECRETS ДЛЯ GITHUB${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo
}

check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI не установлен"
        print_status "Установите GitHub CLI: https://cli.github.com/"
        print_status "Ubuntu/Debian: sudo apt install gh"
        print_status "macOS: brew install gh"
        exit 1
    fi
}

check_auth() {
    if ! gh auth status &> /dev/null; then
        print_error "Не авторизованы в GitHub CLI"
        print_status "Выполните: gh auth login"
        exit 1
    fi
}

generate_ssh_key() {
    print_status "Генерация SSH ключа для деплоя..."
    
    SSH_KEY_PATH="./deploy_key"
    
    if [ -f "$SSH_KEY_PATH" ]; then
        print_warning "SSH ключ уже существует. Использовать существующий? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            rm -f "$SSH_KEY_PATH" "$SSH_KEY_PATH.pub"
        fi
    fi
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "github-actions-deploy"
        print_success "SSH ключ создан: $SSH_KEY_PATH"
    fi
    
    echo
    print_warning "ВАЖНО: Добавьте этот публичный ключ на ваш сервер:"
    echo -e "${YELLOW}====== ПУБЛИЧНЫЙ КЛЮЧ ======${NC}"
    cat "$SSH_KEY_PATH.pub"
    echo -e "${YELLOW}=============================${NC}"
    echo
    print_status "Команды для добавления ключа на сервер:"
    echo "ssh your-server"
    echo "mkdir -p ~/.ssh"
    echo "echo '$(cat "$SSH_KEY_PATH.pub")' >> ~/.ssh/authorized_keys"
    echo "chmod 600 ~/.ssh/authorized_keys"
    echo "chmod 700 ~/.ssh"
    echo
    
    read -p "Нажмите Enter когда добавите ключ на сервер..."
}

set_secrets() {
    print_status "Настройка GitHub Secrets..."
    
    # Получить информацию о сервере
    echo
    read -p "IP адрес сервера: " SERVER_IP
    read -p "Пользователь SSH (по умолчанию: root): " SERVER_USER
    SERVER_USER=${SERVER_USER:-root}
    read -p "Порт SSH (по умолчанию: 22): " SERVER_PORT
    SERVER_PORT=${SERVER_PORT:-22}
    
    # Docker Hub (опционально)
    echo
    print_status "Docker Hub настройки (опционально, для Docker деплоя):"
    read -p "Docker Hub username (оставьте пустым чтобы пропустить): " DOCKER_USERNAME
    
    if [ -n "$DOCKER_USERNAME" ]; then
        read -s -p "Docker Hub password/token: " DOCKER_PASSWORD
        echo
        read -p "Включить Docker deploy? (y/N): " DOCKER_DEPLOY
        if [[ "$DOCKER_DEPLOY" =~ ^[Yy]$ ]]; then
            DOCKER_DEPLOY="true"
        else
            DOCKER_DEPLOY="false"
        fi
    fi
    
    # Установить secrets
    print_status "Установка secrets в GitHub..."
    
    gh secret set SERVER_IP --body "$SERVER_IP"
    gh secret set SERVER_USER --body "$SERVER_USER"  
    gh secret set SERVER_PORT --body "$SERVER_PORT"
    gh secret set SERVER_SSH_KEY --body "$(cat deploy_key)"
    
    if [ -n "$DOCKER_USERNAME" ]; then
        gh secret set DOCKER_USERNAME --body "$DOCKER_USERNAME"
        gh secret set DOCKER_PASSWORD --body "$DOCKER_PASSWORD"
        gh secret set DOCKER_DEPLOY --body "$DOCKER_DEPLOY"
    fi
    
    print_success "Secrets настроены успешно!"
}

test_connection() {
    print_status "Тестирование SSH подключения..."
    
    if ssh -i deploy_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
       "$SERVER_USER@$SERVER_IP" -p "$SERVER_PORT" "echo 'SSH connection successful'"; then
        print_success "SSH подключение работает!"
    else
        print_error "Ошибка SSH подключения"
        print_status "Проверьте:"
        print_status "1. IP адрес и порт"
        print_status "2. SSH ключ добавлен на сервер"  
        print_status "3. SSH сервис запущен на сервере"
        exit 1
    fi
}

cleanup() {
    print_status "Очистка временных файлов..."
    
    read -p "Удалить локальные SSH ключи? (y/N): " cleanup_keys
    if [[ "$cleanup_keys" =~ ^[Yy]$ ]]; then
        rm -f deploy_key deploy_key.pub
        print_success "SSH ключи удалены"
    else
        print_warning "SSH ключи сохранены локально"
        print_status "Не забудьте добавить их в .gitignore!"
    fi
}

show_next_steps() {
    echo
    print_success "Настройка CI/CD завершена!"
    echo
    print_status "Что дальше:"
    echo "1. Закоммитьте изменения: git add . && git commit -m 'Setup CI/CD'"
    echo "2. Запушьте в main ветку: git push origin main"
    echo "3. GitHub Actions автоматически задеплоит на сервер"
    echo
    print_status "Мониторинг:"
    echo "- GitHub Actions: https://github.com/$(gh repo view --json owner,name -q '.owner.login + \"/\" + .name')/actions"
    echo "- SSH на сервер: ssh $SERVER_USER@$SERVER_IP -p $SERVER_PORT"
    echo "- Логи сервиса: sudo journalctl -u terminal-chat -f"
    echo
    print_status "Подключение к чату:"
    echo "python3 client.py $SERVER_IP 12345"
}

main() {
    print_header
    check_gh_cli
    check_auth
    generate_ssh_key
    set_secrets
    test_connection
    cleanup
    show_next_steps
}

# Обработка аргументов
case "${1:-}" in
    --help|-h)
        echo "Скрипт настройки CI/CD для терминального чата"
        echo
        echo "Использование: $0"
        echo
        echo "Этот скрипт:"
        echo "1. Генерирует SSH ключи для деплоя"
        echo "2. Настраивает GitHub Secrets"
        echo "3. Тестирует подключение к серверу"
        exit 0
        ;;
esac

main "$@"