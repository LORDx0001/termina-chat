# Файлы проекта терминального чата

Полный список всех файлов проекта с описанием их назначения.

## 📁 Структура проекта

### 🎯 Основные файлы
- **`server.py`** - Основной сервер чата (для разработки и тестирования)
- **`server_production.py`** - Production версия сервера с расширенным логированием
- **`client.py`** - Клиент с улучшенным интерфейсом и цветным выводом
- **`test_chat.py`** - Скрипт для тестирования системы

### ⚙️ Конфигурация
- **`config_example.py`** - Пример конфигурационного файла (скопировать в config.py)
- **`.env.example`** - Пример переменных окружения (скопировать в .env)
- **`requirements.txt`** - Python зависимости

### 🚀 Развертывание
- **`install.sh`** - Универсальный скрипт установки для Linux
- **`manage_service.sh`** - Управление systemd сервисом
- **`terminal-chat.service`** - Systemd сервис файл

### 🐳 Docker
- **`Dockerfile`** - Docker образ для контейнеризации
- **`docker-compose.yml`** - Docker Compose конфигурация
- **`docker_manager.sh`** - Скрипт управления Docker контейнерами

### 📚 Документация
- **`README.md`** - Основная документация проекта
- **`DEPLOYMENT.md`** - Полное руководство по развертыванию
- **`FILES.md`** - Этот файл со списком всех файлов

## 🎮 Как использовать

### Локальное тестирование
```bash
# 1. Запустить сервер
python3 server.py

# 2. В другом терминале запустить клиент
python3 client.py
```

### Быстрая установка на сервер
```bash
# Автоматическая установка
sudo bash install.sh

# Управление сервисом
sudo ./manage_service.sh start
sudo ./manage_service.sh status
sudo ./manage_service.sh logs
```

### Docker развертывание
```bash
# Сделать скрипт исполняемым
chmod +x docker_manager.sh

# Собрать и запустить
./docker_manager.sh build
./docker_manager.sh start
./docker_manager.sh status
```

## 📋 Последовательность установки

### Для production сервера:

1. **Подготовить сервер**
   ```bash
   # Обновить систему
   sudo apt update && sudo apt upgrade -y
   
   # Установить Git
   sudo apt install -y git
   ```

2. **Скачать проект**
   ```bash
   git clone https://github.com/LORDx0001/terminal-chat.git
   cd terminal-chat
   ```

3. **Выбрать метод установки**
   
   **Вариант A: Автоматическая установка**
   ```bash
   sudo bash install.sh
   ```
   
   **Вариант B: Docker**
   ```bash
   chmod +x docker_manager.sh
   ./docker_manager.sh build
   ./docker_manager.sh start
   ```

4. **Настроить конфигурацию**
   ```bash
   # Для systemd установки
   sudo nano /opt/terminal-chat/config.py
   sudo nano /opt/terminal-chat/.env
   
   # Для Docker
   cp config_example.py config.py
   nano config.py
   ```

5. **Настроить файрвол**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 12345/tcp
   
   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=12345/tcp
   sudo firewall-cmd --reload
   ```

6. **Проверить работу**
   ```bash
   # Systemd
   sudo systemctl status terminal-chat
   
   # Docker
   ./docker_manager.sh status
   
   # Подключиться клиентом
   python3 client.py YOUR_SERVER_IP 12345
   ```

## 🔧 Кастомизация

### Изменение порта
1. **В config.py:** `PORT = 9999`
2. **В .env:** `CHAT_PORT=9999`
3. **В Docker:** изменить docker-compose.yml
4. **Перезапустить сервис**

### Настройка логирования
1. **Уровень логов:** `LOG_LEVEL = "DEBUG"`
2. **Файл логов:** `LOG_FILE = "/var/log/chat.log"`
3. **Размер файла:** `MAX_LOG_SIZE = 50 * 1024 * 1024`

### Лимиты безопасности
1. **Макс. подключений:** `MAX_CONNECTIONS = 200`
2. **Длина сообщения:** `MAX_MESSAGE_LENGTH = 2048`
3. **Пароли комнат:** `MIN_PASSWORD_LENGTH = 6`

## 🛠️ Диагностика

### Проверка работы сервера
```bash
# Проверить порт
sudo netstat -tulpn | grep :12345

# Проверить процесс
ps aux | grep server.py

# Проверить логи
sudo journalctl -u terminal-chat -f
```

### Тестирование подключения
```bash
# Telnet тест
telnet YOUR_SERVER_IP 12345

# Проверка с клиентом
python3 client.py YOUR_SERVER_IP 12345
```

## 📊 Мониторинг

### Просмотр логов
```bash
# Systemd логи
sudo journalctl -u terminal-chat -f

# Файловые логи
sudo tail -f /opt/terminal-chat/chat_server.log
sudo tail -f /opt/terminal-chat/chat_server_actions.log

# Docker логи
./docker_manager.sh logs follow
```

### Статистика сервера
```bash
# В клиенте используйте команду:
/stats

# Показывает:
# - Время работы
# - Количество подключений
# - Количество сообщений
# - Количество комнат
```

## 🔄 Обновление

### Обновление кода
```bash
# Systemd установка
cd /opt/terminal-chat
sudo git pull
sudo systemctl restart terminal-chat

# Docker установка
cd terminal-chat
git pull
./docker_manager.sh update
```

### Резервное копирование
```bash
# Systemd
sudo tar -czf chat_backup.tar.gz -C /opt/terminal-chat .

# Docker
./docker_manager.sh backup
```

## 🆘 Устранение проблем

### Сервер не запускается
1. Проверить логи: `sudo journalctl -u terminal-chat`
2. Проверить порт: `sudo netstat -tulpn | grep :12345`
3. Проверить права: `ls -la /opt/terminal-chat/`
4. Проверить конфигурацию: `python3 server.py --test`

### Клиенты не подключаются
1. Проверить файрвол: `sudo ufw status`
2. Проверить сеть: `ping YOUR_SERVER_IP`
3. Тестировать порт: `telnet YOUR_SERVER_IP 12345`
4. Проверить DNS: `nslookup your-domain.com`

### Высокое использование ресурсов
1. Проверить подключения: `sudo netstat -an | grep :12345 | wc -l`
2. Ограничить память в systemd
3. Очистить старые логи: `sudo journalctl --vacuum-time=7d`

## 🎯 Заключение

Этот проект предоставляет полный набор инструментов для развертывания и управления терминальным чатом в production среде. Выберите подходящий метод установки и следуйте инструкциям.

**Поддержка:**
- GitHub: https://github.com/LORDx0001/terminal-chat
- Issues: https://github.com/LORDx0001/terminal-chat/issues
- Email: support@terminal-chat.com

**Удачного развертывания! 🚀**