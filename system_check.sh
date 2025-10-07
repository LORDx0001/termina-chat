#!/bin/bash

# System Check - Проверка всей системы terminal-chat
# Автор: LORDx0001
# Версия: 1.0

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
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

# Заголовок
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║         Terminal Chat System Check        ║"
echo "║                 v1.0.0                   ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка файлов проекта
log "Проверка файлов проекта..."

files_to_check=(
    "server.py"
    "client.py" 
    "server_production.py"
    "install.sh"
    "quick_deploy.sh"
    "setup_cicd.sh"
    "docker_manager.sh"
    "Dockerfile"
    "docker-compose.yml"
    ".github/workflows/deploy.yml"
    "README.md"
    "DEPLOYMENT.md"
    "CICD.md"
)

missing_files=()
for file in "${files_to_check[@]}"; do
    if [[ -f "$file" ]]; then
        success "Файл $file найден"
    else
        error "Файл $file отсутствует"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -eq 0 ]]; then
    success "Все основные файлы на месте"
else
    error "Отсутствуют файлы: ${missing_files[*]}"
fi

# Проверка Python синтаксиса
log "Проверка Python синтаксиса..."

python_files=("server.py" "client.py" "server_production.py")
syntax_errors=()

for file in "${python_files[@]}"; do
    if [[ -f "$file" ]]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            success "Синтаксис $file корректен"
        else
            error "Синтаксические ошибки в $file"
            syntax_errors+=("$file")
        fi
    fi
done

if [[ ${#syntax_errors[@]} -eq 0 ]]; then
    success "Весь Python код синтаксически корректен"
else
    error "Синтаксические ошибки в файлах: ${syntax_errors[*]}"
fi

# Проверка исполнимых скриптов
log "Проверка прав доступа к скриптам..."

scripts=("install.sh" "quick_deploy.sh" "setup_cicd.sh" "docker_manager.sh")
non_executable=()

for script in "${scripts[@]}"; do
    if [[ -f "$script" ]]; then
        if [[ -x "$script" ]]; then
            success "Скрипт $script исполнимый"
        else
            warning "Скрипт $script не исполнимый (chmod +x $script)"
            non_executable+=("$script")
        fi
    fi
done

if [[ ${#non_executable[@]} -gt 0 ]]; then
    log "Исправление прав доступа..."
    chmod +x "${non_executable[@]}"
    success "Права доступа исправлены"
fi

# Проверка Docker
log "Проверка Docker..."

if command -v docker >/dev/null 2>&1; then
    success "Docker установлен"
    if docker info >/dev/null 2>&1; then
        success "Docker daemon работает"
    else
        warning "Docker daemon не запущен"
    fi
else
    warning "Docker не установлен"
fi

# Проверка Git
log "Проверка Git..."

if command -v git >/dev/null 2>&1; then
    success "Git установлен"
    
    if git rev-parse --git-dir >/dev/null 2>&1; then
        success "Находимся в Git репозитории"
        
        # Проверка remote origin
        if git remote get-url origin >/dev/null 2>&1; then
            origin_url=$(git remote get-url origin)
            success "Remote origin: $origin_url"
        else
            warning "Remote origin не настроен"
        fi
        
        # Проверка статуса
        if [[ -n $(git status --porcelain) ]]; then
            warning "Есть незакоммиченные изменения"
            git status --short
        else
            success "Working directory чистый"
        fi
    else
        warning "Не находимся в Git репозитории"
    fi
else
    error "Git не установлен"
fi

# Проверка GitHub CLI
log "Проверка GitHub CLI..."

if command -v gh >/dev/null 2>&1; then
    success "GitHub CLI установлен"
    
    if gh auth status >/dev/null 2>&1; then
        success "GitHub CLI авторизован"
    else
        warning "GitHub CLI не авторизован (gh auth login)"
    fi
else
    warning "GitHub CLI не установлен"
fi

# Проверка системных зависимостей
log "Проверка системных зависимостей..."

dependencies=("python3" "systemctl" "netstat" "curl" "wget")
missing_deps=()

for dep in "${dependencies[@]}"; do
    if command -v "$dep" >/dev/null 2>&1; then
        success "$dep доступен"
    else
        error "$dep не найден"
        missing_deps+=("$dep")
    fi
done

# Проверка Python модулей
log "Проверка Python модулей..."

python_modules=("socket" "threading" "json" "datetime" "time" "sys" "os")
missing_modules=()

for module in "${python_modules[@]}"; do
    if python3 -c "import $module" >/dev/null 2>&1; then
        success "Модуль $module доступен"
    else
        error "Модуль $module не найден"
        missing_modules+=("$module")
    fi
done

# Проверка сетевых портов
log "Проверка доступности портов..."

check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        warning "Порт $port уже используется"
        return 1
    else
        success "Порт $port свободен"
        return 0
    fi
}

check_port 12345

# Финальная сводка
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 ИТОГИ                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"

total_issues=0

if [[ ${#missing_files[@]} -gt 0 ]]; then
    error "Отсутствующие файлы: ${#missing_files[@]}"
    total_issues=$((total_issues + ${#missing_files[@]}))
fi

if [[ ${#syntax_errors[@]} -gt 0 ]]; then
    error "Файлы с синтаксическими ошибками: ${#syntax_errors[@]}"
    total_issues=$((total_issues + ${#syntax_errors[@]}))
fi

if [[ ${#missing_deps[@]} -gt 0 ]]; then
    error "Отсутствующие зависимости: ${#missing_deps[@]}"
    total_issues=$((total_issues + ${#missing_deps[@]}))
fi

if [[ ${#missing_modules[@]} -gt 0 ]]; then
    error "Отсутствующие Python модули: ${#missing_modules[@]}"
    total_issues=$((total_issues + ${#missing_modules[@]}))
fi

if [[ $total_issues -eq 0 ]]; then
    echo -e "${GREEN}"
    echo "🎉 ВСЁ ОТЛИЧНО! Система готова к деплою!"
    echo ""
    echo "Следующие шаги:"
    echo "1. ./setup_cicd.sh     - настроить CI/CD"
    echo "2. ./quick_deploy.sh   - быстрый деплой"
    echo "3. ./docker_manager.sh build - Docker сборка"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "❌ Найдено $total_issues проблем(ы)"
    echo ""
    echo "Рекомендации:"
    echo "1. Исправить отсутствующие файлы"
    echo "2. Установить недостающие зависимости"
    echo "3. Запустить проверку повторно"
    echo -e "${NC}"
    exit 1
fi