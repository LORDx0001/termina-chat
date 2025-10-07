# Конфигурация сервера терминального чата
# Скопируйте этот файл в config.py и настройте под ваши нужды

# Сетевые настройки
HOST = "0.0.0.0"        # Слушать все интерфейсы
PORT = 12345            # Порт сервера
MAX_CONNECTIONS = 100   # Максимум подключений

# Настройки чата
MAX_MESSAGE_LENGTH = 1024          # Максимальная длина сообщения в байтах
MAX_ROOM_NAME_LENGTH = 50          # Максимальная длина названия комнаты
MAX_USERNAME_LENGTH = 30           # Максимальная длина имени пользователя
HISTORY_MESSAGES_COUNT = 10        # Сколько сообщений показывать при входе

# Файлы данных
DATA_FILE = "chat_data.json"       # Файл хранения данных
LOG_FILE = "chat_server.log"       # Файл логов
BACKUP_INTERVAL = 3600             # Интервал бэкапа в секундах (1 час)

# Безопасность
ENABLE_PASSWORD_PROTECTION = True  # Разрешить пароли для комнат
MIN_PASSWORD_LENGTH = 3           # Минимальная длина пароля
ADMIN_PASSWORD = None             # Пароль администратора сервера (необязательно)

# Производительность
SOCKET_TIMEOUT = 30               # Таймаут сокета в секундах
CLEANUP_INTERVAL = 300            # Интервал очистки отключенных пользователей (5 мин)
AUTO_SAVE_INTERVAL = 60           # Интервал автосохранения в секундах

# Логирование
LOG_LEVEL = "INFO"                # DEBUG, INFO, WARNING, ERROR
LOG_TO_CONSOLE = True             # Выводить логи в консоль
LOG_TO_FILE = True                # Записывать логи в файл
MAX_LOG_SIZE = 10 * 1024 * 1024   # Максимальный размер лог-файла (10MB)

# Дополнительные функции
ENABLE_ROOM_PERSISTENCE = True    # Сохранять комнаты между перезапусками
ENABLE_MESSAGE_HISTORY = True     # Сохранять историю сообщений
ENABLE_USER_STATISTICS = False    # Собирать статистику пользователей
AUTO_DELETE_EMPTY_ROOMS = False   # Автоматически удалять пустые комнаты

# Лимиты
MAX_ROOMS_PER_USER = 5            # Максимум комнат, которые может создать пользователь
MAX_FAILED_LOGINS = 3             # Максимум неудачных попыток входа