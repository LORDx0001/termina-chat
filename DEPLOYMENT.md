# Руководство по развертыванию терминального чата на сервере

Полное руководство по установке и настройке многопользовательского терминального чата на различных серверных платформах.

## 🚀 Быстрый старт

### Автоматическая установка (рекомендуется)

```bash
# Скачайте проект
git clone https://github.com/LORDx0001/terminal-chat.git
cd terminal-chat

# Запустите автоматическую установку
sudo bash install.sh

# Или установка из интернета одной командой
curl -sSL https://raw.githubusercontent.com/LORDx0001/terminal-chat/main/install.sh | sudo bash
```

### Ручная установка

```bash
# 1. Создайте директорию для проекта
sudo mkdir -p /opt/terminal-chat
cd /opt/terminal-chat

# 2. Скопируйте файлы
sudo cp server.py config_example.py .env.example /opt/terminal-chat/
sudo cp config_example.py config.py
sudo cp .env.example .env

# 3. Создайте пользователя для сервиса
sudo useradd --system --home-dir /opt/terminal-chat --shell /bin/false chatuser

# 4. Установите права
sudo chown -R chatuser:chatuser /opt/terminal-chat
sudo chmod 755 /opt/terminal-chat
sudo chmod 644 /opt/terminal-chat/*.py
sudo chmod 600 /opt/terminal-chat/.env

# 5. Установите systemd сервис
sudo cp terminal-chat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable terminal-chat
sudo systemctl start terminal-chat
```

## 🏗️ Варианты развертывания

### 1. VPS/Dedicated сервер (Ubuntu/Debian)

#### Системные требования
- **ОС:** Ubuntu 18.04+ / Debian 9+
- **RAM:** Минимум 256MB, рекомендуется 512MB+
- **CPU:** 1 ядро
- **Диск:** 100MB свободного места
- **Сеть:** 1 открытый порт (по умолчанию 12345)

#### Установка

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить зависимости
sudo apt install -y python3 python3-pip git curl wget

# Клонировать проект
git clone https://github.com/LORDx0001/terminal-chat.git
cd terminal-chat

# Запустить установку
sudo bash install.sh

# Проверить статус
sudo systemctl status terminal-chat
```

#### Настройка файрвола (UFW)

```bash
# Включить UFW
sudo ufw enable

# Открыть порт для чата
sudo ufw allow 12345/tcp

# Проверить статус
sudo ufw status
```

### 2. CentOS/RHEL/Fedora

```bash
# Установить зависимости
sudo yum install -y python3 python3-pip git curl wget  # CentOS 7
# или
sudo dnf install -y python3 python3-pip git curl wget  # CentOS 8/Fedora

# Клонировать и установить
git clone https://github.com/LORDx0001/terminal-chat.git
cd terminal-chat
sudo bash install.sh

# Настроить firewalld
sudo firewall-cmd --permanent --add-port=12345/tcp
sudo firewall-cmd --reload
```

### 3. Docker развертывание

#### Быстрый запуск с Docker

```bash
# Клонировать проект
git clone https://github.com/LORDx0001/terminal-chat.git
cd terminal-chat

# Сделать скрипт исполняемым
chmod +x docker_manager.sh

# Собрать и запустить
./docker_manager.sh build
./docker_manager.sh start

# Проверить статус
./docker_manager.sh status
```

#### Ручное Docker развертывание

```bash
# Собрать образ
docker build -t terminal-chat .

# Запустить контейнер
docker run -d \
  --name terminal-chat-server \
  --restart unless-stopped \
  -p 12345:12345 \
  -v chat_data:/app/data \
  terminal-chat

# Проверить логи
docker logs terminal-chat-server
```

#### Docker Compose

```bash
# Запустить с docker-compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f terminal-chat-server

# Остановить
docker-compose down
```

### 4. Облачные платформы

#### 4.1 DigitalOcean Droplet

1. **Создайте Droplet**
   - ОС: Ubuntu 20.04 LTS
   - План: Basic $5/месяц (1GB RAM)
   - Datacenter: Ближайший к пользователям

2. **Подключитесь по SSH**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Установите чат**
   ```bash
   curl -sSL https://raw.githubusercontent.com/LORDx0001/terminal-chat/main/install.sh | bash
   ```

4. **Настройте файрвол в панели DigitalOcean**
   - Создайте правило: TCP 12345 (Custom)

#### 4.2 AWS EC2

1. **Запустите инстанс**
   - AMI: Ubuntu Server 20.04 LTS
   - Тип: t3.micro (бесплатный уровень)
   - Security Group: Откройте порт 12345

2. **Подключитесь**
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_EC2_IP
   ```

3. **Установите**
   ```bash
   sudo apt update
   git clone https://github.com/LORDx0001/terminal-chat.git
   cd terminal-chat
   sudo bash install.sh
   ```

#### 4.3 Google Cloud Platform

1. **Создайте VM инстанс**
   ```bash
   gcloud compute instances create terminal-chat-server \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-micro \
     --tags=terminal-chat
   ```

2. **Создайте правило файрвола**
   ```bash
   gcloud compute firewall-rules create allow-terminal-chat \
     --allow tcp:12345 \
     --source-ranges 0.0.0.0/0 \
     --target-tags terminal-chat
   ```

3. **Подключитесь и установите**
   ```bash
   gcloud compute ssh terminal-chat-server
   # Далее стандартная установка
   ```

#### 4.4 Hetzner Cloud

1. **Создайте сервер через веб-панель**
   - Образ: Ubuntu 20.04
   - Тип: CX11 (самый дешевый)
   - Datacenter: Ближайший

2. **Установите через SSH**
   ```bash
   ssh root@YOUR_HETZNER_IP
   curl -sSL https://github.com/LORDx0001/terminal-chat/raw/main/install.sh | bash
   ```

### 5. Бесплатные платформы

#### 5.1 Oracle Cloud (Always Free)

Oracle предоставляет бесплатные VM инстансы навсегда:

1. **Создайте аккаунт на oracle.com/cloud**

2. **Создайте Compute инстанс**
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Image: Ubuntu 20.04

3. **Настройте Network Security List**
   - Добавьте правило: TCP 12345

4. **Установите как обычно**

#### 5.2 Google Cloud Free Tier

Google дает $300 кредитов на 90 дней + всегда бесплатные ресурсы:

1. **Используйте e2-micro инстанс** (всегда бесплатный)
2. **Следуйте инструкциям для GCP выше**

## ⚙️ Конфигурация

### Основная конфигурация (`config.py`)

```python
# Сетевые настройки
HOST = "0.0.0.0"        # Слушать все интерфейсы
PORT = 12345            # Порт сервера
MAX_CONNECTIONS = 100   # Максимум подключений

# Настройки чата
MAX_MESSAGE_LENGTH = 1024
MAX_ROOM_NAME_LENGTH = 50
MAX_USERNAME_LENGTH = 30

# Безопасность
ENABLE_PASSWORD_PROTECTION = True
MIN_PASSWORD_LENGTH = 3
```

### Переменные окружения (`.env`)

```bash
CHAT_HOST=0.0.0.0
CHAT_PORT=12345
CHAT_ADMIN_PASSWORD=your_secure_password
CHAT_LOG_LEVEL=INFO
```

### Изменение порта

```bash
# Способ 1: В конфигурации
sudo nano /opt/terminal-chat/config.py
# Измените PORT = 12345 на нужный

# Способ 2: Через переменные окружения
sudo nano /opt/terminal-chat/.env
# Добавьте: CHAT_PORT=новый_порт

# Перезапустите сервис
sudo systemctl restart terminal-chat
```

## 🔒 Безопасность

### Базовая защита

```bash
# 1. Обновите систему
sudo apt update && sudo apt upgrade -y

# 2. Настройте файрвол
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 12345/tcp

# 3. Отключите root login по SSH
sudo nano /etc/ssh/sshd_config
# Добавьте: PermitRootLogin no
sudo systemctl restart ssh

# 4. Создайте нового пользователя
sudo adduser yourusername
sudo usermod -aG sudo yourusername
```

### SSL/TLS (с nginx)

```bash
# Установить nginx и certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Настроить nginx для проксирования
sudo nano /etc/nginx/sites-available/terminal-chat
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:12345;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/terminal-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Получить SSL сертификат
sudo certbot --nginx -d your-domain.com
```

## 📊 Мониторинг и обслуживание

### Просмотр логов

```bash
# Логи systemd
sudo journalctl -u terminal-chat -f

# Логи приложения
sudo tail -f /opt/terminal-chat/chat_server.log

# Логи действий пользователей
sudo tail -f /opt/terminal-chat/chat_server_actions.log
```

### Управление сервисом

```bash
# Статус
sudo systemctl status terminal-chat

# Запуск/остановка
sudo systemctl start terminal-chat
sudo systemctl stop terminal-chat
sudo systemctl restart terminal-chat

# Автозагрузка
sudo systemctl enable terminal-chat
sudo systemctl disable terminal-chat
```

### Резервное копирование

```bash
# Ручное создание backup
sudo tar -czf chat_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  -C /opt/terminal-chat chat_data.json config.py .env

# Автоматическое backup (cron)
sudo crontab -e
# Добавьте: 0 2 * * * /opt/terminal-chat/backup.sh
```

### Мониторинг ресурсов

```bash
# CPU и память
htop

# Сетевые подключения
sudo netstat -tulpn | grep :12345

# Дисковое пространство
df -h

# Статистика сервера чата
# Используйте команду /stats в клиенте
```

## 🚨 Устранение проблем

### Сервер не запускается

```bash
# 1. Проверить логи
sudo journalctl -u terminal-chat --no-pager

# 2. Проверить порт
sudo netstat -tulpn | grep :12345

# 3. Проверить права доступа
ls -la /opt/terminal-chat/

# 4. Проверить конфигурацию
sudo -u chatuser python3 /opt/terminal-chat/server.py --check-config
```

### Клиенты не могут подключиться

```bash
# 1. Проверить файрвол
sudo ufw status

# 2. Проверить сетевые интерфейсы
ip addr show

# 3. Тестировать подключение
telnet YOUR_SERVER_IP 12345

# 4. Проверить DNS
nslookup your-domain.com
```

### Высокое использование ресурсов

```bash
# 1. Проверить количество подключений
sudo netstat -an | grep :12345 | wc -l

# 2. Ограничить память в systemd
sudo systemctl edit terminal-chat
# Добавьте: [Service]
#          MemoryMax=256M

# 3. Очистить старые логи
sudo journalctl --vacuum-time=7d
```

## 🔧 Дополнительные настройки

### Кастомный домен

1. **Купите домен** (Namecheap, GoDaddy, etc.)

2. **Настройте DNS A-запись**
   ```
   Type: A
   Name: chat (или @)
   Value: YOUR_SERVER_IP
   TTL: 300
   ```

3. **Настройте SSL** (см. раздел безопасности)

### Множественные инстансы

```bash
# Запустить второй сервер на другом порту
sudo cp /etc/systemd/system/terminal-chat.service \
       /etc/systemd/system/terminal-chat-2.service

# Отредактировать новый сервис
sudo nano /etc/systemd/system/terminal-chat-2.service
# Изменить ExecStart и добавить Environment=CHAT_PORT=12346

sudo systemctl daemon-reload
sudo systemctl enable terminal-chat-2
sudo systemctl start terminal-chat-2
```

### Интеграция с веб-интерфейсом

В будущем можно добавить веб-интерфейс через WebSocket мост:

```bash
# Установить дополнительные зависимости
pip3 install websockets flask

# Запустить WebSocket мост
python3 websocket_bridge.py
```

## 📈 Масштабирование

### Для большого количества пользователей

1. **Увеличьте лимиты системы**
   ```bash
   # /etc/security/limits.conf
   chatuser soft nofile 65536
   chatuser hard nofile 65536
   ```

2. **Настройте Load Balancer**
   ```bash
   # nginx upstream
   upstream chat_backend {
       server 127.0.0.1:12345;
       server 127.0.0.1:12346;
   }
   ```

3. **Используйте Redis для синхронизации**
   ```bash
   sudo apt install redis-server
   pip3 install redis
   ```

### Мониторинг производительности

```bash
# Установить Prometheus и Grafana
# Создать метрики в приложении
# Настроить алерты
```

## 📝 Автоматизация развертывания

### Ansible Playbook

```yaml
# deploy.yml
---
- hosts: servers
  become: yes
  tasks:
    - name: Install terminal chat
      script: install.sh
    - name: Configure firewall
      ufw:
        rule: allow
        port: '12345'
        proto: tcp
```

### Terraform для облака

```hcl
# main.tf
resource "aws_instance" "chat_server" {
  ami           = "ami-0c02fb55956c7d316"  # Ubuntu 20.04
  instance_type = "t3.micro"
  
  user_data = file("install.sh")
  
  vpc_security_group_ids = [aws_security_group.chat.id]
}
```

---

## 🎯 Заключение

Теперь у вас есть полное руководство по развертыванию терминального чата на любой платформе. Выберите подходящий вариант и следуйте инструкциям.

**Рекомендации по выбору:**
- **Для обучения:** Локальная установка или Oracle Cloud Free
- **Для небольших проектов:** DigitalOcean Droplet $5/месяц
- **Для продакшена:** AWS/GCP с Load Balancer и мониторингом
- **Для разработки:** Docker на локальной машине

**Поддержка:**
- GitHub Issues: https://github.com/LORDx0001/terminal-chat/issues
- Email: support@terminal-chat.com
- Telegram: @terminalchat_support

**Удачного развертывания! 🚀**