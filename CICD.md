# CI/CD для терминального чата

Автоматическое развертывание терминального чата с помощью GitHub Actions.

## 🚀 Быстрая настройка CI/CD

### Вариант 1: Автоматическая настройка

```bash
# Настроить все автоматически
./setup_cicd.sh
```

Этот скрипт:
- Сгенерирует SSH ключи
- Настроит GitHub Secrets  
- Протестирует подключение
- Подготовит все для CI/CD

### Вариант 2: Ручная настройка

#### 1. Генерация SSH ключей

```bash
# Создать SSH ключ для деплоя
ssh-keygen -t ed25519 -f deploy_key -N ""

# Добавить публичный ключ на сервер
ssh your-server
mkdir -p ~/.ssh
cat deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

#### 2. Настройка GitHub Secrets

Перейдите в Settings → Secrets and variables → Actions и добавьте:

| Secret | Описание | Пример |
|--------|----------|--------|
| `SERVER_IP` | IP адрес сервера | `192.168.1.100` |
| `SERVER_USER` | SSH пользователь | `root` |
| `SERVER_PORT` | SSH порт | `22` |
| `SERVER_SSH_KEY` | Приватный SSH ключ | содержимое `deploy_key` |
| `DOCKER_USERNAME` | Docker Hub логин | `yourusername` |
| `DOCKER_PASSWORD` | Docker Hub пароль | `your_token` |
| `DOCKER_DEPLOY` | Включить Docker деплой | `true` |

## 🔄 Workflow CI/CD

### Триггеры

- **Push в main** - автоматический деплой
- **Pull Request** - только тестирование
- **Push в develop** - только тестирование

### Stages

1. **Test** - проверка синтаксиса и тестирование
2. **Build Docker** - сборка Docker образа (при наличии секретов)
3. **Deploy Systemd** - деплой через systemd сервис
4. **Deploy Docker** - деплой через Docker (опционально)
5. **Notify** - уведомления о результате

## 🎯 Методы деплоя

### 1. Systemd Service (по умолчанию)

```yaml
# Автоматически:
# - Клонирует код в /opt/terminal-chat
# - Создает systemd сервис
# - Настраивает пользователя chatuser
# - Запускает сервис
```

**Управление:**
```bash
# На сервере
sudo systemctl status terminal-chat
sudo systemctl restart terminal-chat
sudo journalctl -u terminal-chat -f
```

### 2. Docker Deployment

```yaml
# Требует DOCKER_DEPLOY=true
# Автоматически:
# - Собирает Docker образ
# - Публикует в Docker Hub
# - Деплоит контейнер на сервер
```

**Управление:**
```bash
# На сервере  
docker ps | grep terminal-chat
docker logs terminal-chat-server
docker restart terminal-chat-server
```

## 📋 Быстрые команды

### Ручной деплой

```bash
# Быстрый деплой без GitHub Actions
./quick_deploy.sh
```

### Мониторинг

```bash
# Логи GitHub Actions
gh run list
gh run view

# SSH на сервер
ssh user@server-ip

# Проверка сервиса
sudo systemctl status terminal-chat
sudo journalctl -u terminal-chat -f
```

### Откат изменений

```bash
# На сервере найти бэкап
ls -la /opt/terminal-chat.backup.*

# Восстановить из бэкапа
sudo systemctl stop terminal-chat
sudo rm -rf /opt/terminal-chat
sudo mv /opt/terminal-chat.backup.YYYYMMDD_HHMMSS /opt/terminal-chat
sudo systemctl start terminal-chat
```

## 🛠️ Кастомизация

### Изменение деплой директории

```yaml
# В .github/workflows/deploy.yml
env:
  DEPLOY_PATH: /your/custom/path
```

### Добавление pre/post deploy скриптов

```bash
# Создать на сервере
sudo nano /opt/terminal-chat/pre-deploy.sh
sudo nano /opt/terminal-chat/post-deploy.sh

# Изменить workflow для выполнения скриптов
```

### Мульти-сервер деплой

```yaml
# Добавить в workflow
strategy:
  matrix:
    server: [server1, server2, server3]
```

## 🔒 Безопасность

### SSH ключи
- Используйте отдельные ключи для каждого проекта
- Ограничьте доступ ключа только к необходимым командам
- Регулярно ротируйте ключи

### Secrets
- Никогда не коммитьте секреты в код
- Используйте environment-specific секреты
- Регулярно обновляйте токены

### Сервер
```bash
# Ограничить SSH доступ
echo 'AllowUsers deployuser' | sudo tee -a /etc/ssh/sshd_config

# Настроить файрвол
sudo ufw allow 22/tcp
sudo ufw allow 12345/tcp
sudo ufw enable
```

## 📊 Мониторинг и алерты

### GitHub Actions уведомления

```yaml
# Добавить в workflow
- name: Slack Notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Мониторинг сервера

```bash
# Установить мониторинг
sudo apt install prometheus-node-exporter

# Настроить алерты на падение сервиса
sudo systemctl enable prometheus-node-exporter
```

## 🚨 Troubleshooting

### GitHub Actions не запускается
```bash
# Проверить статус
gh api repos/:owner/:repo/actions/workflows

# Проверить секреты
gh secret list
```

### SSH подключение не работает
```bash
# Тестировать подключение
ssh -i deploy_key user@server -v

# Проверить authorized_keys
cat ~/.ssh/authorized_keys
```

### Сервис не запускается
```bash
# Проверить логи
sudo journalctl -u terminal-chat --no-pager
sudo systemctl status terminal-chat -l

# Проверить права
ls -la /opt/terminal-chat/
sudo -u chatuser python3 /opt/terminal-chat/server.py
```

## 🎯 Best Practices

### 1. Staging Environment
```bash
# Создать staging ветку
git checkout -b staging
git push origin staging

# Настроить отдельный workflow для staging
```

### 2. Rollback Strategy
- Всегда создавать бэкапы перед деплоем
- Тестировать деплой на staging
- Иметь план отката

### 3. Zero Downtime Deployment
```bash
# Blue-Green deployment
# Запустить новый сервис на другом порту
# Переключить nginx/load balancer
# Остановить старый сервис
```

### 4. Health Checks
```yaml
# Добавить в workflow проверки после деплоя
- name: Health Check
  run: |
    curl -f http://${{ secrets.SERVER_IP }}:12345/health || exit 1
```

## 📈 Масштабирование

### Мультисерверный деплой
```yaml
strategy:
  matrix:
    server:
      - { host: "server1.example.com", user: "deploy" }
      - { host: "server2.example.com", user: "deploy" }
```

### Load Balancer
```nginx
upstream terminal_chat {
    server 192.168.1.10:12345;
    server 192.168.1.11:12345;
    server 192.168.1.12:12345;
}
```

---

**🚀 Готово! Теперь у вас есть полноценный CI/CD пайплайн для автоматического деплоя терминального чата.**