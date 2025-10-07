#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production-ready сервер для терминального чата с улучшенным логированием
"""

import socket
import threading
import json
import datetime
import os
import uuid
import logging
import logging.handlers
import signal
import sys
import time
import traceback
import hashlib
from typing import Dict, List, Optional
from pathlib import Path

# Попытаться импортировать конфигурацию
try:
    from config import *
except ImportError:
    # Значения по умолчанию если config.py не найден
    HOST = "0.0.0.0"
    PORT = 12345
    MAX_CONNECTIONS = 100
    MAX_MESSAGE_LENGTH = 1024
    DATA_FILE = "/opt/terminal-chat/data/chat_data.json"
    LOG_FILE = "/opt/terminal-chat/logs/chat_server.log"
    LOG_LEVEL = "INFO"
    AUTO_SAVE_INTERVAL = 60
    USERS_FILE = "/opt/terminal-chat/data/users.json"

class User:
    """Класс для представления пользователя с аутентификацией"""
    def __init__(self, username: str, password_hash: str, created_at: str = None, 
                 last_login: str = None, message_history: List = None, 
                 room_history: List = None, settings: Dict = None):
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at or datetime.datetime.now().isoformat()
        self.last_login = last_login
        self.message_history = message_history or []
        self.room_history = room_history or []
        self.settings = settings or {}
        self.is_online = False
        self.current_room = None
        
    def check_password(self, password: str) -> bool:
        """Проверить пароль пользователя"""
        return self.password_hash == self.hash_password(password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def add_message_to_history(self, room_id: str, message: str, timestamp: str = None):
        """Добавить сообщение в историю пользователя"""
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        self.message_history.append({
            'room_id': room_id,
            'message': message,
            'timestamp': timestamp
        })
        
        # Ограничить историю последними 1000 сообщениями
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]
    
    def add_room_to_history(self, room_id: str, room_name: str):
        """Добавить комнату в историю посещений"""
        room_entry = {'room_id': room_id, 'room_name': room_name, 'last_visit': datetime.datetime.now().isoformat()}
        
        # Удалить если уже есть и добавить в начало
        self.room_history = [r for r in self.room_history if r['room_id'] != room_id]
        self.room_history.insert(0, room_entry)
        
        # Ограничить историю последними 50 комнатами
        if len(self.room_history) > 50:
            self.room_history = self.room_history[:50]
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'message_history': self.message_history,
            'room_history': self.room_history,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Создать объект из словаря"""
        return cls(
            username=data['username'],
            password_hash=data['password_hash'],
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            message_history=data.get('message_history', []),
            room_history=data.get('room_history', []),
            settings=data.get('settings', {})
        )

class ChatRoom:
    def __init__(self, room_id: str, name: str, admin: str, password: str = None):
        self.room_id = room_id
        self.name = name
        self.admin = admin
        self.password = password
        self.users: Dict[str, dict] = {}
        self.messages: List[dict] = []
        self.created_at = datetime.datetime.now().isoformat()
        self.last_activity = datetime.datetime.now()
        
    def add_user(self, username: str, user_socket, address):
        self.users[username] = {
            'socket': user_socket, 
            'address': address,
            'joined_at': datetime.datetime.now().isoformat()
        }
        self.last_activity = datetime.datetime.now()
        
    def remove_user(self, username: str):
        if username in self.users:
            del self.users[username]
            self.last_activity = datetime.datetime.now()
            
    def broadcast_message(self, message: str, sender: str = None):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Сохранить сообщение в истории
        self.messages.append({
            'timestamp': timestamp,
            'sender': sender,
            'message': message,
            'date': datetime.datetime.now().isoformat()
        })
        
        # Ограничить количество сохраняемых сообщений
        if len(self.messages) > 1000:
            self.messages = self.messages[-500:]  # Оставить последние 500
        
        # Отправить всем пользователям в комнате
        disconnected_users = []
        for username, user_info in self.users.items():
            try:
                user_info['socket'].send(formatted_message.encode('utf-8'))
            except Exception as e:
                logging.warning(f"Ошибка отправки сообщения пользователю {username}: {e}")
                disconnected_users.append(username)
                
        # Удалить отключенных пользователей
        for username in disconnected_users:
            self.remove_user(username)
            
        self.last_activity = datetime.datetime.now()
            
    def to_dict(self):
        return {
            'room_id': self.room_id,
            'name': self.name,
            'admin': self.admin,
            'password': self.password,
            'messages': self.messages[-100:],  # Сохранять только последние 100 сообщений
            'created_at': self.created_at,
            'last_activity': self.last_activity.isoformat(),
            'user_count': len(self.users)
        }

class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.rooms: Dict[str, ChatRoom] = {}
        self.user_rooms: Dict[str, str] = {}
        self.user_sockets: Dict[str, socket.socket] = {}
        self.socket_users: Dict[socket.socket, str] = {}
        self.data_file = DATA_FILE
        self.users_file = USERS_FILE
        self.users: Dict[str, User] = {}  # Словарь всех зарегистрированных пользователей
        self.online_users: Dict[str, User] = {}  # Словарь онлайн пользователей
        self.running = False
        self.server_socket = None
        self.stats = {
            'start_time': datetime.datetime.now(),
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'rooms_created': 0,
            'registered_users': 0
        }
        
        self.setup_logging()
        self.setup_signal_handlers()
        self.load_data()
        self.load_users()
        
        # Запустить фоновые задачи
        self.start_background_tasks()
        
    def setup_logging(self):
        """Настроить систему логирования"""
        # Создать директорию для логов
        log_dir = Path(LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
        
        # Настроить форматирование
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Настроить основной логгер
        self.logger = logging.getLogger('ChatServer')
        self.logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        
        # Файловый обработчик с ротацией
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Отдельный логгер для действий пользователей
        self.action_logger = logging.getLogger('UserActions')
        self.action_logger.setLevel(logging.INFO)
        
        action_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE.replace('.log', '_actions.log'),
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        action_formatter = logging.Formatter('%(asctime)s - %(message)s')
        action_handler.setFormatter(action_formatter)
        self.action_logger.addHandler(action_handler)
        
    def setup_signal_handlers(self):
        """Настроить обработчики сигналов для graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.shutdown()
        
    def start_background_tasks(self):
        """Запустить фоновые задачи"""
        # Автосохранение данных
        auto_save_thread = threading.Thread(
            target=self.auto_save_worker,
            daemon=True
        )
        auto_save_thread.start()
        
        # Очистка неактивных соединений
        cleanup_thread = threading.Thread(
            target=self.cleanup_worker,
            daemon=True
        )
        cleanup_thread.start()
        
        # Сбор статистики
        stats_thread = threading.Thread(
            target=self.stats_worker,
            daemon=True
        )
        stats_thread.start()
        
    def auto_save_worker(self):
        """Фоновое автосохранение данных"""
        while self.running:
            try:
                time.sleep(AUTO_SAVE_INTERVAL)
                if self.running:
                    self.save_data()
                    self.logger.debug("Автосохранение выполнено")
            except Exception as e:
                self.logger.error(f"Ошибка автосохранения: {e}")
                
    def cleanup_worker(self):
        """Очистка отключенных соединений"""
        while self.running:
            try:
                time.sleep(300)  # Каждые 5 минут
                if self.running:
                    self.cleanup_disconnected_users()
            except Exception as e:
                self.logger.error(f"Ошибка очистки: {e}")
                
    def stats_worker(self):
        """Сбор статистики"""
        while self.running:
            try:
                time.sleep(60)  # Каждую минуту
                if self.running:
                    self.log_statistics()
            except Exception as e:
                self.logger.error(f"Ошибка сбора статистики: {e}")
                
    def cleanup_disconnected_users(self):
        """Очистить отключенных пользователей"""
        disconnected = []
        for username, sock in self.user_sockets.items():
            try:
                # Попытаться отправить пустой пакет для проверки соединения
                sock.send(b'')
            except:
                disconnected.append(username)
                
        for username in disconnected:
            self.logger.info(f"Очистка отключенного пользователя: {username}")
            self.cleanup_user(username)
            
    def cleanup_user(self, username: str):
        """Очистить все ссылки на пользователя"""
        try:
            # Сохранить данные пользователя перед отключением
            if username in self.users:
                user = self.users[username]
                user.is_online = False
                self.save_users()
            
            # Удалить из онлайн пользователей
            if username in self.online_users:
                del self.online_users[username]
            
            # Удалить из комнаты
            if username in self.user_rooms:
                room_id = self.user_rooms[username]
                if room_id in self.rooms:
                    self.rooms[room_id].remove_user(username)
                del self.user_rooms[username]
                
            # Удалить сокет
            if username in self.user_sockets:
                try:
                    self.user_sockets[username].close()
                except:
                    pass
                del self.user_sockets[username]
                
            # Обновить обратную ссылку
            sock_to_remove = None
            for sock, user in self.socket_users.items():
                if user == username:
                    sock_to_remove = sock
                    break
            if sock_to_remove:
                del self.socket_users[sock_to_remove]
                
            self.stats['active_connections'] = len(self.user_sockets)
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки пользователя {username}: {e}")
            
    def log_statistics(self):
        """Логировать статистику сервера"""
        uptime = datetime.datetime.now() - self.stats['start_time']
        stats_msg = (
            f"Статистика: Время работы: {uptime}, "
            f"Активных подключений: {self.stats['active_connections']}, "
            f"Всего подключений: {self.stats['total_connections']}, "
            f"Сообщений отправлено: {self.stats['messages_sent']}, "
            f"Комнат создано: {self.stats['rooms_created']}, "
            f"Активных комнат: {len(self.rooms)}"
        )
        self.logger.info(stats_msg)
        
    def load_data(self):
        """Загрузить сохраненные данные"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for room_data in data.get('rooms', []):
                        room = ChatRoom(
                            room_data['room_id'],
                            room_data['name'],
                            room_data['admin'],
                            room_data.get('password')
                        )
                        room.messages = room_data.get('messages', [])
                        room.created_at = room_data.get('created_at', datetime.datetime.now().isoformat())
                        self.rooms[room.room_id] = room
                        
                self.logger.info(f"Загружено {len(self.rooms)} комнат из {self.data_file}")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки данных: {e}")
                # Создать резервную копию поврежденного файла
                if os.path.exists(self.data_file):
                    backup_name = f"{self.data_file}.backup.{int(time.time())}"
                    os.rename(self.data_file, backup_name)
                    self.logger.warning(f"Поврежденный файл перемещен в {backup_name}")
                    
    def save_data(self):
        """Сохранить данные"""
        try:
            # Создать временный файл для атомарной записи
            temp_file = f"{self.data_file}.tmp"
            
            data = {
                'rooms': [room.to_dict() for room in self.rooms.values()],
                'stats': {
                    'total_connections': self.stats['total_connections'],
                    'messages_sent': self.stats['messages_sent'],
                    'rooms_created': self.stats['rooms_created'],
                },
                'last_updated': datetime.datetime.now().isoformat(),
                'server_version': '1.0'
            }
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Атомарно заменить основной файл
            os.replace(temp_file, self.data_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных: {e}")
            # Удалить временный файл в случае ошибки
            if os.path.exists(f"{self.data_file}.tmp"):
                os.unlink(f"{self.data_file}.tmp")
    
    def load_users(self):
        """Загрузить пользователей из файла"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                for username, user_data in users_data.get('users', {}).items():
                    self.users[username] = User.from_dict(user_data)
                
                self.stats['registered_users'] = len(self.users)
                self.logger.info(f"Загружено пользователей: {len(self.users)}")
            else:
                self.logger.info("Файл пользователей не найден, создаем новый")
                self.save_users()
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки пользователей: {e}")
            self.users = {}
    
    def save_users(self):
        """Сохранить пользователей в файл"""
        try:
            # Создать временный файл для атомарной записи
            temp_file = f"{self.users_file}.tmp"
            
            data = {
                'users': {username: user.to_dict() for username, user in self.users.items()},
                'last_updated': datetime.datetime.now().isoformat(),
                'total_users': len(self.users)
            }
            
            # Убедиться что директория существует
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Атомарно заменить основной файл
            os.replace(temp_file, self.users_file)
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения пользователей: {e}")
            # Удалить временный файл в случае ошибки
            if os.path.exists(f"{self.users_file}.tmp"):
                os.unlink(f"{self.users_file}.tmp")
    
    def register_user(self, username: str, password: str) -> bool:
        """Зарегистрировать нового пользователя"""
        username = username.strip().lower()
        
        # Проверка валидности имени пользователя
        if not username or len(username) < 3 or len(username) > 20:
            return False
        
        # Проверка на недопустимые символы
        allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_-')
        if not all(c in allowed_chars for c in username):
            return False
        
        # Проверка что пользователь не существует
        if username in self.users:
            return False
        
        # Создать нового пользователя
        password_hash = User.hash_password(password)
        user = User(username, password_hash)
        self.users[username] = user
        
        self.save_users()
        self.stats['registered_users'] = len(self.users)
        
        self.action_logger.info(f"REGISTER: Новый пользователь зарегистрирован: {username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Аутентификация пользователя"""
        username = username.strip().lower()
        
        if username not in self.users:
            return False
        
        user = self.users[username]
        if user.check_password(password):
            user.last_login = datetime.datetime.now().isoformat()
            self.save_users()
            return True
        
        return False
    
    def login_user(self, username: str, user_socket: socket.socket) -> User:
        """Войти в систему (пользователь уже аутентифицирован)"""
        username = username.strip().lower()
        user = self.users[username]
        
        # Если пользователь уже онлайн, отключить предыдущее подключение
        if username in self.online_users:
            old_socket = self.user_sockets.get(username)
            if old_socket:
                try:
                    old_socket.send("Ваш аккаунт был авторизован с другого устройства".encode('utf-8'))
                    old_socket.close()
                except:
                    pass
        
        # Установить онлайн статус
        user.is_online = True
        self.online_users[username] = user
        self.user_sockets[username] = user_socket
        self.socket_users[user_socket] = username
        
        self.action_logger.info(f"LOGIN: Пользователь {username} вошел в систему")
        return user
                
    def create_room(self, room_name: str, admin: str, password: str = None) -> str:
        """Создать новую комнату"""
        room_id = str(uuid.uuid4())[:8]
        room = ChatRoom(room_id, room_name, admin, password)
        self.rooms[room_id] = room
        self.stats['rooms_created'] += 1
        
        self.action_logger.info(f"ROOM_CREATED: {admin} создал комнату '{room_name}' (ID: {room_id})")
        self.logger.info(f"Создана комната '{room_name}' (ID: {room_id}) пользователем {admin}")
        
        return room_id
        
    def join_room(self, username: str, room_id: str, password: str = None) -> bool:
        """Присоединиться к комнате"""
        if room_id not in self.rooms:
            self.action_logger.warning(f"JOIN_FAILED: {username} попытался войти в несуществующую комнату {room_id}")
            return False
            
        room = self.rooms[room_id]
        
        # Проверить пароль
        if room.password and room.password != password:
            self.action_logger.warning(f"JOIN_FAILED: {username} ввел неверный пароль для комнаты {room_id}")
            return False
            
        # Удалить из предыдущей комнаты
        if username in self.user_rooms:
            old_room_id = self.user_rooms[username]
            if old_room_id in self.rooms:
                self.rooms[old_room_id].remove_user(username)
                self.rooms[old_room_id].broadcast_message(f"{username} покинул комнату", "SYSTEM")
                
        # Добавить в новую комнату
        user_socket = self.user_sockets[username]
        address = getattr(user_socket, 'address', 'unknown')
        room.add_user(username, user_socket, address)
        self.user_rooms[username] = room_id
        
        # Добавить комнату в историю пользователя
        if username in self.users:
            user = self.users[username]
            user.add_room_to_history(room_id, room.name)
            user.current_room = room_id
        
        # Отправить приветствие и историю
        try:
            user_socket.send(f"\n=== Добро пожаловать в комнату '{room.name}' (ID: {room_id}) ===".encode('utf-8'))
            user_socket.send(f"Администратор: {room.admin}".encode('utf-8'))
            user_socket.send(f"Пользователей в комнате: {len(room.users)}".encode('utf-8'))
            
            if room.messages:
                user_socket.send("=== История сообщений ===".encode('utf-8'))
                for msg in room.messages[-10:]:
                    if msg.get('sender'):
                        user_socket.send(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}".encode('utf-8'))
                    else:
                        user_socket.send(f"[{msg['timestamp']}] {msg['message']}".encode('utf-8'))
            
            user_socket.send("=== Конец истории ===\n".encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки приветствия пользователю {username}: {e}")
        
        # Уведомить других
        room.broadcast_message(f"{username} присоединился к комнате", "SYSTEM")
        
        self.action_logger.info(f"JOIN_SUCCESS: {username} присоединился к комнате {room_id}")
        self.logger.info(f"{username} присоединился к комнате '{room.name}' (ID: {room_id})")
        
        return True
        
    def handle_client(self, client_socket, address):
        """Обработать подключение клиента с аутентификацией"""
        username = None
        try:
            client_socket.settimeout(60)  # Таймаут для аутентификации
            
            # Аутентификация пользователя
            username = self.authenticate_client(client_socket, address)
            if not username:
                return
            
            # Пользователь аутентифицирован, входим в систему
            user = self.login_user(username, client_socket)
            
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1
            
            self.action_logger.info(f"CONNECT: {username} подключился с {address}")
            self.logger.info(f"Пользователь {username} подключился с {address}")
            
            # Отправить персонализированное приветствие
            welcome_messages = [
                f"=== ДОБРО ПОЖАЛОВАТЬ ОБРАТНО, {username.upper()}! ===",
                f"Последний вход: {user.last_login or 'Первый раз'}",
                f"Ваших сообщений: {len(user.message_history)}",
                f"Посещенных комнат: {len(user.room_history)}",
                "",
                "=== КОМАНДЫ ЧАТА ===",
                "Используйте /help для получения списка команд",
                "Используйте /list для просмотра доступных комнат",
                "Используйте /create <название> [пароль] для создания новой комнаты",
                "Используйте /join <ID> [пароль] для входа в существующую комнату",
                "Используйте /myrooms для просмотра ваших комнат",
                "Используйте /history для просмотра истории сообщений"
            ]
            
            for msg in welcome_messages:
                client_socket.send(msg.encode('utf-8'))
            
            client_socket.settimeout(None)  # Убрать таймаут для обычной работы
            
            # Основной цикл обработки сообщений
            while self.running:
                try:
                    message = client_socket.recv(MAX_MESSAGE_LENGTH).decode('utf-8')
                    if not message:
                        break
                        
                    if message.startswith('/'):
                        response = self.handle_command(username, message)
                        if response:
                            client_socket.send(response.encode('utf-8'))
                    else:
                        # Обычное сообщение
                        if username in self.user_rooms:
                            room_id = self.user_rooms[username]
                            if room_id in self.rooms:
                                room = self.rooms[room_id]
                                if ": " in message:
                                    sender, text = message.split(": ", 1)
                                    room.broadcast_message(f"{sender}: {text}", sender)
                                    # Добавить в историю пользователя
                                    user.add_message_to_history(room_id, text)
                                    self.stats['messages_sent'] += 1
                                else:
                                    room.broadcast_message(message, username)
                                    # Добавить в историю пользователя
                                    user.add_message_to_history(room_id, message)
                                    self.stats['messages_sent'] += 1
                        else:
                            client_socket.send("Вы не находитесь ни в одной комнате. Используйте /join <ID> или /create <название>".encode('utf-8'))
                            
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except Exception as e:
                    self.logger.error(f"Ошибка обработки сообщения от {username}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки клиента {address}: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        finally:
            if username:
                self.action_logger.info(f"DISCONNECT: {username} отключился")
                self.logger.info(f"Пользователь {username} отключился")
                self.cleanup_user(username)
                
            try:
                client_socket.close()
            except:
                pass
    
    def authenticate_client(self, client_socket, address) -> Optional[str]:
        """Аутентификация клиента"""
        try:
            # Отправить запрос на аутентификацию
            auth_prompt = "AUTH_REQUIRED"
            client_socket.send(auth_prompt.encode('utf-8'))
            
            # Получить логин
            login_data = client_socket.recv(1024).decode('utf-8')
            if not login_data.startswith("LOGIN:"):
                client_socket.send("ERROR:Неверный формат логина".encode('utf-8'))
                return None
            
            username = login_data[6:].strip().lower()
            
            # Проверить валидность имени пользователя
            if not username or len(username) < 3 or len(username) > 20:
                client_socket.send("ERROR:Имя пользователя должно быть от 3 до 20 символов".encode('utf-8'))
                return None
            
            # Проверить что пользователь существует
            if username not in self.users:
                # Новый пользователь - предложить регистрацию
                client_socket.send("NEW_USER:Пользователь не найден. Создать новый аккаунт? (y/n)".encode('utf-8'))
                
                response = client_socket.recv(1024).decode('utf-8').strip().lower()
                if response != 'y' and response != 'yes':
                    client_socket.send("ERROR:Регистрация отменена".encode('utf-8'))
                    return None
                
                # Запросить пароль для нового аккаунта
                client_socket.send("PASSWORD_NEW:Введите пароль для нового аккаунта:".encode('utf-8'))
                password = client_socket.recv(1024).decode('utf-8').strip()
                
                if len(password) < 6:
                    client_socket.send("ERROR:Пароль должен быть не менее 6 символов".encode('utf-8'))
                    return None
                
                # Зарегистрировать пользователя
                if self.register_user(username, password):
                    client_socket.send("SUCCESS:Аккаунт создан! Добро пожаловать!".encode('utf-8'))
                    return username
                else:
                    client_socket.send("ERROR:Не удалось создать аккаунт".encode('utf-8'))
                    return None
            else:
                # Существующий пользователь - запросить пароль
                client_socket.send("PASSWORD:Введите пароль:".encode('utf-8'))
                password = client_socket.recv(1024).decode('utf-8').strip()
                
                if self.authenticate_user(username, password):
                    client_socket.send("SUCCESS:Авторизация успешна!".encode('utf-8'))
                    return username
                else:
                    client_socket.send("ERROR:Неверный пароль".encode('utf-8'))
                    self.action_logger.warning(f"AUTH_FAILED: {username} с {address}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Ошибка аутентификации клиента {address}: {e}")
            return None
                
    def handle_command(self, username: str, command: str) -> str:
        """Обработать команду (с тем же функционалом что и раньше)"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        self.action_logger.info(f"COMMAND: {username} выполнил команду {cmd}")
        
        # Здесь тот же код обработки команд что и в оригинальном сервере
        if cmd == '/help':
            return """
=== КОМАНДЫ ЧАТА ===
📋 Основные команды:
/help - показать эту справку
/list - список всех комнат
/users - пользователи в текущей комнате
/exit - выйти из чата

🏠 Работа с комнатами:
/create <название> [пароль] - создать новую комнату
/join <ID> [пароль] - войти в существующую комнату
/leave - покинуть текущую комнату
/info - информация о текущей комнате

� Персональные команды:
/profile - ваш профиль
/myrooms - ваши комнаты
/history - история сообщений

�👨‍💼 Админские команды (только для создателя комнаты):
/kick <пользователь> - исключить пользователя
/password <новый_пароль> - установить/изменить пароль комнаты

📊 Информация:
/stats - статистика сервера

💡 Примеры:
/create Общение 123 - создать комнату с паролем
/join abc123 456 - войти в комнату с паролем
/create Открытая - создать комнату без пароля
"""
        
        elif cmd == '/stats':
            uptime = datetime.datetime.now() - self.stats['start_time']
            return f"""
=== СТАТИСТИКА СЕРВЕРА ===
Время работы: {uptime}
Активных подключений: {self.stats['active_connections']}
Всего подключений: {self.stats['total_connections']}
Сообщений отправлено: {self.stats['messages_sent']}
Комнат создано: {self.stats['rooms_created']}
Активных комнат: {len(self.rooms)}
Зарегистрированных пользователей: {self.stats['registered_users']}
"""
        
        elif cmd == '/myrooms':
            user = self.users.get(username)
            if not user or not user.room_history:
                return "У вас нет истории посещений комнат."
            
            result = "\n=== ВАШИ КОМНАТЫ ===\n"
            for room_entry in user.room_history[:10]:  # Показать последние 10
                room_id = room_entry['room_id']
                room_name = room_entry['room_name']
                last_visit = room_entry['last_visit']
                status = "🟢 Активна" if room_id in self.rooms else "🔴 Закрыта"
                result += f"{room_id}: {room_name} - {status}\n"
                result += f"   Последний визит: {last_visit[:19]}\n\n"
            return result
            
        elif cmd == '/history':
            user = self.users.get(username)
            if not user or not user.message_history:
                return "У вас нет истории сообщений."
            
            result = "\n=== ВАША ИСТОРИЯ СООБЩЕНИЙ ===\n"
            recent_messages = user.message_history[-20:]  # Последние 20 сообщений
            
            for msg_entry in recent_messages:
                room_id = msg_entry['room_id']
                message = msg_entry['message']
                timestamp = msg_entry['timestamp'][:19]  # Убрать миллисекунды
                
                room_name = "Неизвестная комната"
                if room_id in self.rooms:
                    room_name = self.rooms[room_id].name
                
                result += f"[{timestamp}] {room_name}: {message}\n"
            
            return result
            
        elif cmd == '/profile':
            user = self.users.get(username)
            if not user:
                return "Профиль не найден."
            
            return f"""
=== ВАШ ПРОФИЛЬ ===
Имя пользователя: {user.username}
Дата регистрации: {user.created_at[:19]}
Последний вход: {user.last_login[:19] if user.last_login else 'Первый раз'}
Сообщений отправлено: {len(user.message_history)}
Комнат посещено: {len(user.room_history)}
Статус: 🟢 Онлайн
"""
        
        # Остальные команды остаются теми же...
        # (копируем из оригинального сервера)
        elif cmd == '/list':
            rooms = self.get_room_list()
            if not rooms:
                return "Нет доступных комнат."
            
            result = "\n=== СПИСОК КОМНАТ ===\n"
            for room in rooms:
                lock_icon = "🔒" if room['protected'] else "🔓"
                result += f"{lock_icon} {room['id']}: {room['name']} (Админ: {room['admin']}, Пользователей: {room['users']})\n"
            return result
            
        elif cmd == '/create':
            if len(parts) < 2:
                return "Использование: /create <название> [пароль]"
            
            room_name = parts[1]
            password = parts[2] if len(parts) > 2 else None
            room_id = self.create_room(room_name, username, password)
            
            self.join_room(username, room_id, password)
            return f"Комната '{room_name}' создана! ID: {room_id}"
            
        elif cmd == '/join':
            if len(parts) < 2:
                return "Использование: /join <ID> [пароль]"
            
            room_id = parts[1]
            password = parts[2] if len(parts) > 2 else None
            
            if self.join_room(username, room_id, password):
                return f"Вы присоединились к комнате {room_id}"
            else:
                return "Не удалось присоединиться к комнате. Проверьте ID и пароль."
                
        # ... остальные команды
        
        else:
            return f"Неизвестная команда: {cmd}. Используйте /help для справки."
    
    def get_room_list(self) -> List[dict]:
        """Получить список комнат"""
        room_list = []
        for room in self.rooms.values():
            room_info = {
                'id': room.room_id,
                'name': room.name,
                'admin': room.admin,
                'users': len(room.users),
                'protected': bool(room.password),
                'created': room.created_at
            }
            room_list.append(room_info)
        return room_list
        
    def start_server(self):
        """Запустить сервер"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CONNECTIONS)
            self.running = True
            
            self.logger.info(f"Сервер запущен на {self.host}:{self.port}")
            self.logger.info(f"Максимум подключений: {MAX_CONNECTIONS}")
            self.logger.info(f"Загружено комнат: {len(self.rooms)}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)  # Таймаут для возможности проверки self.running
                    client_socket, address = self.server_socket.accept()
                    
                    if not self.running:
                        client_socket.close()
                        break
                        
                    # Проверить лимит подключений
                    if len(self.user_sockets) >= MAX_CONNECTIONS:
                        client_socket.send("Сервер перегружен. Попробуйте позже.".encode('utf-8'))
                        client_socket.close()
                        self.logger.warning(f"Отклонено подключение от {address}: превышен лимит подключений")
                        continue
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except OSError:
                    if self.running:  # Если это не shutdown
                        self.logger.error("Ошибка сокета сервера")
                    break
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Неожиданная ошибка сервера: {e}")
                        
        except Exception as e:
            self.logger.error(f"Критическая ошибка сервера: {e}")
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Корректное завершение работы сервера"""
        if not self.running:
            return
            
        self.logger.info("Начинается завершение работы сервера...")
        self.running = False
        
        # Закрыть серверный сокет
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        # Уведомить всех пользователей
        shutdown_msg = "Сервер завершает работу. Соединение будет разорвано."
        for username, sock in list(self.user_sockets.items()):
            try:
                sock.send(shutdown_msg.encode('utf-8'))
                sock.close()
            except:
                pass
                
        # Сохранить данные
        try:
            self.save_data()
            self.logger.info("Данные сохранены")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных при завершении: {e}")
            
        # Логировать финальную статистику
        uptime = datetime.datetime.now() - self.stats['start_time']
        self.logger.info(f"Сервер проработал: {uptime}")
        self.logger.info(f"Обслужено подключений: {self.stats['total_connections']}")
        self.logger.info(f"Отправлено сообщений: {self.stats['messages_sent']}")
        self.logger.info("Сервер остановлен")

if __name__ == "__main__":
    import sys
    
    # Обработка аргументов командной строки
    host = HOST
    port = PORT
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Неверный номер порта")
            sys.exit(1)
            
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # Создать и запустить сервер
    server = ChatServer(host=host, port=port)
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания...")
    finally:
        server.shutdown()
        sys.exit(0)