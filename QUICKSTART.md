# 🚀 Быстрый старт Terminal Chat

## ⚡ Мгновенный деплой (3 команды)

```bash
# 1. Проверить систему
./system_check.sh

# 2. Настроить CI/CD автоматизацию  
./setup_cicd.sh

# 3. Деплоить!
git add . && git commit -m "Deploy terminal-chat" && git push origin main
```

## 🎯 Альтернативные способы

### Ручной деплой на сервер
```bash
./quick_deploy.sh
```

### Docker локально
```bash
./docker_manager.sh build
./docker_manager.sh start
```

### Классическая установка
```bash
sudo ./install.sh
```

---

## 📋 Что нужно подготовить

### Для CI/CD автодеплоя:
- [x] GitHub аккаунт с репозиторием
- [x] Сервер с SSH доступом  
- [x] GitHub CLI (`gh auth login`)

### Для ручного деплоя:
- [x] Сервер с SSH доступом
- [x] Python 3.6+ на сервере

### Для Docker:
- [x] Docker установлен
- [x] Docker Compose (опционально)

---

## 🔧 После установки

### Подключение к серверу:
```bash
python3 client.py
# Введите IP сервера: YOUR_SERVER_IP
# Порт: 12345
```

### Управление сервисом:
```bash
sudo systemctl status terminal-chat   # статус
sudo systemctl restart terminal-chat  # перезапуск  
sudo journalctl -u terminal-chat -f   # логи
```

### Админские команды в чате:
- `/create room_name password` - создать комнату
- `/join room_name password` - войти в комнату
- `/kick username` - кик пользователя (админ)
- `/users` - список пользователей
- `/rooms` - список комнат

---

## 🆘 Проблемы?

1. **Запустить диагностику**: `./system_check.sh`
2. **Посмотреть логи**: `sudo journalctl -u terminal-chat`
3. **Проверить порты**: `sudo netstat -tulpn | grep 12345`
4. **Документация**: [DEPLOYMENT.md](DEPLOYMENT.md) | [CICD.md](CICD.md)

---

**Готово!** 🎉 Теперь у вас есть production-ready чат с автоматическим деплоем!