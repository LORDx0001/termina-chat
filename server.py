#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import json
import datetime
import hashlib
import os
import uuid
from typing import Dict, List, Optional

class ChatRoom:
    def __init__(self, room_id: str, name: str, admin: str, password: str = None):
        self.room_id = room_id
        self.name = name
        self.admin = admin
        self.password = password
        self.users: Dict[str, dict] = {}  # username: {socket, address}
        self.messages: List[dict] = []
        self.created_at = datetime.datetime.now().isoformat()
        
    def add_user(self, username: str, user_socket, address):
        self.users[username] = {'socket': user_socket, 'address': address}
        
    def remove_user(self, username: str):
        if username in self.users:
            del self.users[username]
            
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
        
        # Отправить всем пользователям в комнате
        disconnected_users = []
        for username, user_info in self.users.items():
            try:
                user_info['socket'].send(formatted_message.encode('utf-8'))
            except:
                disconnected_users.append(username)
                
        # Удалить отключенных пользователей
        for username in disconnected_users:
            self.remove_user(username)
            
    def to_dict(self):
        return {
            'room_id': self.room_id,
            'name': self.name,
            'admin': self.admin,
            'password': self.password,
            'messages': self.messages,
            'created_at': self.created_at,
            'user_count': len(self.users)
        }

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.rooms: Dict[str, ChatRoom] = {}
        self.user_rooms: Dict[str, str] = {}  # username: room_id
        self.user_sockets: Dict[str, socket.socket] = {}  # username: socket
        self.socket_users: Dict[socket.socket, str] = {}  # socket: username
        self.data_file = 'chat_data.json'
        self.load_data()
        
    def load_data(self):
        """Загрузить сохраненные данные чатов"""
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
                print(f"[SERVER] Загружено {len(self.rooms)} комнат из сохраненных данных")
            except Exception as e:
                print(f"[SERVER] Ошибка загрузки данных: {e}")
                
    def save_data(self):
        """Сохранить данные чатов"""
        try:
            data = {
                'rooms': [room.to_dict() for room in self.rooms.values()],
                'last_updated': datetime.datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SERVER] Ошибка сохранения данных: {e}")
            
    def create_room(self, room_name: str, admin: str, password: str = None) -> str:
        """Создать новую комнату"""
        room_id = str(uuid.uuid4())[:8]
        room = ChatRoom(room_id, room_name, admin, password)
        self.rooms[room_id] = room
        self.save_data()
        return room_id
        
    def join_room(self, username: str, room_id: str, password: str = None) -> bool:
        """Присоединиться к комнате"""
        if room_id not in self.rooms:
            return False
            
        room = self.rooms[room_id]
        
        # Проверить пароль если установлен
        if room.password and room.password != password:
            return False
            
        # Удалить пользователя из предыдущей комнаты
        if username in self.user_rooms:
            old_room_id = self.user_rooms[username]
            if old_room_id in self.rooms:
                self.rooms[old_room_id].remove_user(username)
                self.rooms[old_room_id].broadcast_message(f"{username} покинул комнату", "SYSTEM")
                
        # Добавить в новую комнату
        user_socket = self.user_sockets[username]
        room.add_user(username, user_socket, None)
        self.user_rooms[username] = room_id
        
        # Отправить историю сообщений
        user_socket.send(f"\n=== Добро пожаловать в комнату '{room.name}' (ID: {room_id}) ===".encode('utf-8'))
        user_socket.send(f"Администратор: {room.admin}".encode('utf-8'))
        user_socket.send(f"Пользователей в комнате: {len(room.users)}".encode('utf-8'))
        
        if room.messages:
            user_socket.send("=== История сообщений ===".encode('utf-8'))
            for msg in room.messages[-10:]:  # Показать последние 10 сообщений
                if msg.get('sender'):
                    user_socket.send(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}".encode('utf-8'))
                else:
                    user_socket.send(f"[{msg['timestamp']}] {msg['message']}".encode('utf-8'))
        
        user_socket.send("=== Конец истории ===\n".encode('utf-8'))
        
        # Уведомить других пользователей
        room.broadcast_message(f"{username} присоединился к комнате", "SYSTEM")
        
        return True
        
    def leave_room(self, username: str):
        """Покинуть текущую комнату"""
        if username in self.user_rooms:
            room_id = self.user_rooms[username]
            if room_id in self.rooms:
                room = self.rooms[room_id]
                room.remove_user(username)
                room.broadcast_message(f"{username} покинул комнату", "SYSTEM")
                del self.user_rooms[username]
                
    def get_room_list(self) -> List[dict]:
        """Получить список всех комнат"""
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
        
    def handle_command(self, username: str, command: str) -> str:
        """Обработать команду пользователя"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd == '/help':
            return """
=== КОМАНДЫ ЧАТА ===
/help - показать справку
/list - список всех комнат
/create <название> [пароль] - создать комнату
/join <ID> [пароль] - присоединиться к комнате
/leave - покинуть текущую комнату
/users - список пользователей в комнате
/info - информация о текущей комнате
/kick <пользователь> - выгнать пользователя (только админ)
/password <новый_пароль> - изменить пароль комнаты (только админ)
/exit - выйти из чата
"""
        
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
            
            # Автоматически присоединиться к созданной комнате
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
                
        elif cmd == '/leave':
            if username in self.user_rooms:
                self.leave_room(username)
                return "Вы покинули комнату."
            else:
                return "Вы не находитесь в комнате."
                
        elif cmd == '/users':
            if username in self.user_rooms:
                room_id = self.user_rooms[username]
                room = self.rooms[room_id]
                users_list = list(room.users.keys())
                return f"Пользователи в комнате: {', '.join(users_list)}"
            else:
                return "Вы не находитесь в комнате."
                
        elif cmd == '/info':
            if username in self.user_rooms:
                room_id = self.user_rooms[username]
                room = self.rooms[room_id]
                lock_status = "Да" if room.password else "Нет"
                return f"""
=== ИНФОРМАЦИЯ О КОМНАТЕ ===
Название: {room.name}
ID: {room.room_id}
Администратор: {room.admin}
Защищена паролем: {lock_status}
Пользователей: {len(room.users)}
Создана: {room.created_at}
"""
            else:
                return "Вы не находитесь в комнате."
                
        elif cmd == '/kick':
            if len(parts) < 2:
                return "Использование: /kick <пользователь>"
            
            target_user = parts[1]
            if username in self.user_rooms:
                room_id = self.user_rooms[username]
                room = self.rooms[room_id]
                
                if room.admin != username:
                    return "Только администратор может выгонять пользователей."
                
                if target_user in room.users:
                    # Отправить уведомление выгоняемому пользователю
                    target_socket = room.users[target_user]['socket']
                    target_socket.send(f"Вы были выгнаны из комнаты администратором {username}".encode('utf-8'))
                    
                    # Удалить пользователя
                    room.remove_user(target_user)
                    if target_user in self.user_rooms:
                        del self.user_rooms[target_user]
                    
                    room.broadcast_message(f"{target_user} был выгнан администратором", "SYSTEM")
                    return f"Пользователь {target_user} выгнан из комнаты."
                else:
                    return f"Пользователь {target_user} не найден в комнате."
            else:
                return "Вы не находитесь в комнате."
                
        elif cmd == '/password':
            if len(parts) < 2:
                return "Использование: /password <новый_пароль>"
            
            new_password = parts[1]
            if username in self.user_rooms:
                room_id = self.user_rooms[username]
                room = self.rooms[room_id]
                
                if room.admin != username:
                    return "Только администратор может изменять пароль."
                
                room.password = new_password
                self.save_data()
                return f"Пароль комнаты изменен на: {new_password}"
            else:
                return "Вы не находитесь в комнате."
        
        else:
            return f"Неизвестная команда: {cmd}. Используйте /help для справки."
            
    def handle_client(self, client_socket, address):
        """Обработать подключение клиента"""
        username = None
        try:
            # Получить имя пользователя
            welcome_msg = client_socket.recv(1024).decode('utf-8')
            if "присоединился к чату" in welcome_msg:
                username = welcome_msg.split(" присоединился к чату")[0]
                self.user_sockets[username] = client_socket
                self.socket_users[client_socket] = username
                
                print(f"[SERVER] {username} подключился с {address}")
                
                # Отправить приветствие и справку
                client_socket.send("=== ДОБРО ПОЖАЛОВАТЬ В МНОГОПОЛЬЗОВАТЕЛЬСКИЙ ЧАТ ===".encode('utf-8'))
                client_socket.send("Используйте /help для получения списка команд".encode('utf-8'))
                client_socket.send("Используйте /list для просмотра доступных комнат".encode('utf-8'))
                client_socket.send("Используйте /create <название> для создания новой комнаты".encode('utf-8'))
                
                while True:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                        
                    if message.startswith('/'):
                        # Обработать команду
                        response = self.handle_command(username, message)
                        client_socket.send(response.encode('utf-8'))
                    else:
                        # Обычное сообщение - отправить в текущую комнату
                        if username in self.user_rooms:
                            room_id = self.user_rooms[username]
                            if room_id in self.rooms:
                                room = self.rooms[room_id]
                                # Извлечь имя и сообщение
                                if ": " in message:
                                    sender, text = message.split(": ", 1)
                                    room.broadcast_message(f"{sender}: {text}", sender)
                                else:
                                    room.broadcast_message(message, username)
                        else:
                            client_socket.send("Вы не находитесь ни в одной комнате. Используйте /join <ID> или /create <название>".encode('utf-8'))
                            
        except Exception as e:
            print(f"[SERVER] Ошибка с клиентом {address}: {e}")
        finally:
            if username:
                print(f"[SERVER] {username} отключился")
                # Удалить пользователя из комнаты
                self.leave_room(username)
                # Очистить ссылки
                if username in self.user_sockets:
                    del self.user_sockets[username]
                if client_socket in self.socket_users:
                    del self.socket_users[client_socket]
            client_socket.close()
            
    def start_server(self):
        """Запустить сервер"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind((self.host, self.port))
            server.listen(5)
            print(f"[SERVER] Сервер запущен на {self.host}:{self.port}")
            print(f"[SERVER] Загружено комнат: {len(self.rooms)}")
            
            while True:
                client_socket, address = server.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n[SERVER] Сервер остановлен")
        except Exception as e:
            print(f"[SERVER] Ошибка сервера: {e}")
        finally:
            self.save_data()
            server.close()

if __name__ == "__main__":
    import sys
    
    port = 12345
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Неверный номер порта")
            sys.exit(1)
    
    server = ChatServer(port=port)
    server.start_server()
