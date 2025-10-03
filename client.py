import socket
import threading
import sys
import re

HOST = '84.46.247.15'
PORT = 12345

# ANSI цвета
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

def colorize(message):
    # Ищем формат "Имя: сообщение"
    match = re.match(r"^(.*?):\s(.*)", message)
    if match:
        name = match.group(1)
        text = match.group(2)
        return f"{RED}{name}{RESET}: {GREEN}{text}{RESET}"
    return message  # если не совпадает, выводим как есть

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                sys.stdout.write('\r' + ' ' * 80 + '\r')  # очистить строку
                print(colorize(message))
                sys.stdout.write('> ')
                sys.stdout.flush()
        except:
            print("\n[!] Соединение потеряно.")
            sock.close()
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except Exception as e:
        print(f"[!] Не удалось подключиться: {e}")
        return

    name = input("Введите ваше имя: ").strip() or "Аноним"
    client.send(f"{name} присоединился к чату.".encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    try:
        while True:
            msg = input('> ')
            if msg.lower() in ['exit', 'quit']:
                break
            client.send(f"{name}: {msg}".encode('utf-8'))
    except KeyboardInterrupt:
        print("\n[!] Вы вышли из чата через Ctrl+C.")
    finally:
        client.send(f"{name} покинул чат.".encode('utf-8'))
        client.close()
        sys.exit()

if __name__ == "__main__":
    start_client()
