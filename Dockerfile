# Используем официальный Python образ
FROM python:3.11-slim

# Установить метаданные
LABEL maintainer="LORDx0001"
LABEL description="Terminal Chat Server"
LABEL version="1.0"

# Создать пользователя для приложения
RUN groupadd -r chatuser && useradd -r -g chatuser chatuser

# Установить рабочую директорию
WORKDIR /app

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копировать файлы требований и установить Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать исходный код приложения
COPY server.py .
COPY config_example.py ./config.py

# Создать директорию для данных
RUN mkdir -p /app/data && chown -R chatuser:chatuser /app

# Создать том для постоянного хранения данных
VOLUME ["/app/data"]

# Переключиться на непривилегированного пользователя
USER chatuser

# Открыть порт
EXPOSE 12345

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV CHAT_HOST=0.0.0.0
ENV CHAT_PORT=12345
ENV CHAT_DATA_FILE=/app/data/chat_data.json
ENV CHAT_LOG_FILE=/app/data/chat_server.log

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import socket; s = socket.socket(); s.connect(('localhost', 12345)); s.close()" || exit 1

# Команда запуска
CMD ["python3", "server.py"]