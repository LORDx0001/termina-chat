import socket
import threading
import sys
import re

HOST = '84.46.247.15' 


RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

buffer = ''

def colorize(message):
    match = re.match(r"^(.*?):\s(.*)", message)
    if match:
        name = match.group(1)
        text = match.group(2)
        return f"{RED}{name}{RESET}: {GREEN}{text}{RESET}"
    return message

def receive_messages(sock):
    global buffer
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                sys.stdout.write('\r' + ' ' * 80 + '\r')
                print(colorize(message))
                sys.stdout.write(f'> {buffer}')
                sys.stdout.flush()
        except:
            print("\n[!] Соединение потеряно.")
            sock.close()
            break

def start_client():
    global buffer
    port = int(input("Введите порт комнаты: ").strip())

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, port))
    except Exception as e:
        print(f"[!] Не удалось подключиться: {e}")
        return

    name = input("Введите ваше имя: ").strip() or "Аноним"
    client.send(f"{name} присоединился к чату.".encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    try:
        while True:
            sys.stdout.write('> ')
            sys.stdout.flush()
            buffer = input()
            if buffer.lower() in ['exit', 'quit']:
                break
            client.send(f"{name}: {buffer}".encode('utf-8'))
            buffer = ''
    except KeyboardInterrupt:
        print("\n[!] Вы вышли из чата через Ctrl+C.")
    finally:
        client.send(f"{name} покинул чат.".encode('utf-8'))
        client.close()
        sys.exit()

if __name__ == "__main__":
    start_client()
