#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import sys
import re
import os
import getpass

HOST = '84.46.247.15'  # Для локального тестирования
PORT = 12345

# ANSI цвета и форматирование
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'

class ChatClient:
    def __init__(self):
        self.socket = None
        self.username = ""
        self.connected = False
        self.current_room = None
        
    def colorize_message(self, message):
        """Раскрасить сообщения для лучшей читаемости"""
        # Системные сообщения
        if "[SYSTEM]" in message or "=== " in message:
            return f"{CYAN}{message}{RESET}"
        
        # Временные метки
        timestamp_pattern = r'\[(\d{2}:\d{2}:\d{2})\]'
        message = re.sub(timestamp_pattern, f"{YELLOW}[\\1]{RESET}", message)
        
        # Сообщения пользователей "Имя: сообщение"
        user_message_match = re.match(r"^(.*?)\[(\d{2}:\d{2}:\d{2})\]\s(.+?):\s(.+)", message)
        if user_message_match:
            prefix = user_message_match.group(1)
            timestamp = user_message_match.group(2)
            username = user_message_match.group(3)
            text = user_message_match.group(4)
            return f"{prefix}{YELLOW}[{timestamp}]{RESET} {RED}{username}{RESET}: {GREEN}{text}{RESET}"
        
        # Простые сообщения "Имя: сообщение"
        simple_match = re.match(r"^(.+?):\s(.+)", message)
        if simple_match:
            username = simple_match.group(1)
            text = simple_match.group(2)
            return f"{RED}{username}{RESET}: {GREEN}{text}{RESET}"
        
        return message
        
    def clear_input_line(self):
        """Очистить текущую строку ввода"""
        # Сохранить позицию курсора, очистить строку, вернуть курсор
        sys.stdout.write('\r\033[K')  # Очистить строку от курсора до конца
        sys.stdout.flush()
        
    def print_prompt(self):
        """Показать приглашение для ввода"""
        if self.current_room:
            prompt = f"{BLUE}[{self.current_room}]{RESET} {self.username}> "
        else:
            prompt = f"{self.username}> "
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
    def receive_messages(self):
        """Получать сообщения от сервера"""
        while self.connected:
            try:
                message = self.socket.recv(4096).decode('utf-8')
                if message:
                    # Очистить текущую строку ввода
                    self.clear_input_line()
                    
                    # Обработать специальные сообщения
                    if "Добро пожаловать в комнату" in message:
                        # Извлечь ID комнаты
                        room_match = re.search(r"ID: ([a-zA-Z0-9-]+)", message)
                        if room_match:
                            self.current_room = room_match.group(1)
                    elif "Вы покинули комнату" in message:
                        self.current_room = None
                    
                    # Показать сообщение
                    print(self.colorize_message(message))
                    
                    # Восстановить приглашение для ввода
                    self.print_prompt()
                else:
                    break
            except Exception as e:
                if self.connected:
                    print(f"\n{RED}[!] Ошибка получения сообщения: {e}{RESET}")
                break
                
        print(f"\n{RED}[!] Соединение потеряно.{RESET}")
        self.connected = False
        
    def send_message(self, message):
        """Отправить сообщение на сервер"""
        try:
            self.socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"{RED}[!] Ошибка отправки: {e}{RESET}")
            return False
            
    def print_help(self):
        """Показать локальную справку"""
        help_text = f"""
{BOLD}=== СПРАВКА ПО КОМАНДАМ ==={RESET}
{CYAN}Команды чата:{RESET}
  /help          - показать справку сервера
  /list          - список всех комнат
  /create <name> [password] - создать комнату
  /join <ID> [password]     - присоединиться к комнате
  /leave         - покинуть текущую комнату
  /users         - пользователи в комнате
  /info          - информация о комнате
  
{CYAN}Персональные команды:{RESET}
  /profile       - ваш профиль
  /myrooms       - ваши комнаты
  /history       - история сообщений
  
{CYAN}Админские команды:{RESET}
  /kick <user>   - выгнать пользователя
  /password <new> - изменить пароль комнаты
  
{CYAN}Локальные команды:{RESET}
  !help          - эта справка
  !clear         - очистить экран
  !status        - статус подключения
  !quit, !exit   - выйти из чата
  
{CYAN}Примеры:{RESET}
  /create MyRoom secret123
  /join abc12345 secret123
  /kick BadUser
"""
        print(help_text)
        
    def handle_local_command(self, command):
        """Обработать локальные команды (начинающиеся с !)"""
        cmd = command.lower()
        
        if cmd in ['!quit', '!exit']:
            return False
        elif cmd == '!help':
            self.print_help()
        elif cmd == '!clear':
            os.system('clear' if os.name == 'posix' else 'cls')
        elif cmd == '!status':
            status = f"{GREEN}Подключен{RESET}" if self.connected else f"{RED}Отключен{RESET}"
            room_info = f" | Комната: {BLUE}{self.current_room}{RESET}" if self.current_room else " | Не в комнате"
            print(f"Статус: {status}{room_info}")
        else:
            print(f"{RED}Неизвестная локальная команда: {command}{RESET}")
            print("Используйте !help для справки")
            
        return True
        
    def start_client(self):
        """Запустить клиент с аутентификацией"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            print(f"{CYAN}Подключение к {HOST}:{PORT}...{RESET}")
            self.socket.connect((HOST, PORT))
            self.connected = True
            print(f"{GREEN}Подключение установлено!{RESET}")
        except Exception as e:
            print(f"{RED}[!] Не удалось подключиться: {e}{RESET}")
            return
        
        # Аутентификация
        if not self.authenticate():
            return
        
        # Запустить поток для получения сообщений
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()
        
        # Основной цикл ввода
        try:
            while self.connected:
                self.print_prompt()
                try:
                    user_input = input().strip()
                except EOFError:
                    break
                    
                if not user_input:
                    continue
                    
                # Локальные команды
                if user_input.startswith('!'):
                    if not self.handle_local_command(user_input):
                        break
                    continue
                
                # Команды выхода
                if user_input.lower() in ['exit', 'quit', '/exit']:
                    break
                    
                # Отправить сообщение или команду на сервер
                if user_input.startswith('/'):
                    # Команда
                    if not self.send_message(user_input):
                        break
                else:
                    # Обычное сообщение
                    full_message = f"{self.username}: {user_input}"
                    if not self.send_message(full_message):
                        break
                        
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Выход по Ctrl+C{RESET}")
        finally:
            self.disconnect()
    
    def authenticate(self):
        """Процесс аутентификации"""
        try:
            # Ждем запрос аутентификации
            auth_prompt = self.socket.recv(1024).decode('utf-8')
            if auth_prompt != "AUTH_REQUIRED":
                print(f"{RED}Неожиданный ответ сервера: {auth_prompt}{RESET}")
                return False
            
            print(f"\n{BOLD}=== АУТЕНТИФИКАЦИЯ ==={RESET}")
            
            # Получить имя пользователя
            while True:
                username = input(f"{BOLD}Введите имя пользователя: {RESET}").strip()
                if username and len(username) >= 3 and len(username) <= 20:
                    # Проверить допустимые символы
                    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
                    if all(c in allowed_chars for c in username):
                        break
                    else:
                        print(f"{RED}Имя может содержать только буквы, цифры, '_' и '-'{RESET}")
                else:
                    print(f"{RED}Имя должно содержать от 3 до 20 символов{RESET}")
            
            self.username = username.lower()
            
            # Отправить логин
            login_msg = f"LOGIN:{self.username}"
            self.socket.send(login_msg.encode('utf-8'))
            
            # Получить ответ сервера
            response = self.socket.recv(1024).decode('utf-8')
            
            if response.startswith("NEW_USER:"):
                # Новый пользователь
                message = response[9:]
                print(f"{YELLOW}{message}{RESET}")
                
                confirm = input(f"{BOLD}Создать новый аккаунт? (y/n): {RESET}").strip().lower()
                self.socket.send(confirm.encode('utf-8'))
                
                if confirm in ['y', 'yes']:
                    # Ждем запрос пароля
                    pwd_prompt = self.socket.recv(1024).decode('utf-8')
                    if pwd_prompt.startswith("PASSWORD_NEW:"):
                        message = pwd_prompt[13:]
                        print(f"{CYAN}{message}{RESET}")
                        
                        import getpass
                        password = getpass.getpass(f"{BOLD}Пароль: {RESET}")
                        
                        if len(password) < 6:
                            print(f"{RED}Пароль должен быть не менее 6 символов{RESET}")
                            return False
                        
                        self.socket.send(password.encode('utf-8'))
                        
                        # Получить результат
                        result = self.socket.recv(1024).decode('utf-8')
                        if result.startswith("SUCCESS:"):
                            print(f"{GREEN}{result[8:]}{RESET}")
                            return True
                        else:
                            print(f"{RED}{result[6:] if result.startswith('ERROR:') else result}{RESET}")
                            return False
                else:
                    return False
                    
            elif response.startswith("PASSWORD:"):
                # Существующий пользователь
                message = response[9:]
                print(f"{CYAN}{message}{RESET}")
                
                import getpass
                password = getpass.getpass(f"{BOLD}Пароль: {RESET}")
                
                self.socket.send(password.encode('utf-8'))
                
                # Получить результат
                result = self.socket.recv(1024).decode('utf-8')
                if result.startswith("SUCCESS:"):
                    print(f"{GREEN}{result[8:]}{RESET}")
                    return True
                else:
                    print(f"{RED}{result[6:] if result.startswith('ERROR:') else result}{RESET}")
                    return False
                    
            elif response.startswith("ERROR:"):
                print(f"{RED}{response[6:]}{RESET}")
                return False
            else:
                print(f"{RED}Неожиданный ответ сервера: {response}{RESET}")
                return False
                
        except Exception as e:
            print(f"{RED}Ошибка аутентификации: {e}{RESET}")
            return False
            
    def disconnect(self):
        """Отключиться от сервера"""
        if self.connected:
            try:
                goodbye_msg = f"{self.username} покинул чат."
                self.socket.send(goodbye_msg.encode('utf-8'))
            except:
                pass
            self.connected = False
            
        if self.socket:
            self.socket.close()
        
        print(f"{CYAN}Отключено от сервера. До свидания!{RESET}")

def main():
    """Главная функция"""
    print(f"{BOLD}{MAGENTA}=== ТЕРМИНАЛЬНЫЙ ЧАТ КЛИЕНТ ==={RESET}")
    
    # Обработка аргументов командной строки
    global HOST, PORT
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            PORT = int(sys.argv[2])
        except ValueError:
            print(f"{RED}Неверный номер порта: {sys.argv[2]}{RESET}")
            sys.exit(1)
    
    print(f"Подключение к {HOST}:{PORT}")
    
    client = ChatClient()
    client.start_client()

if __name__ == "__main__":
    main()
