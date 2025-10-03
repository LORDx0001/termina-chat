import socket
import threading
import sys

HOST = '84.46.247.15'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                print(message)
        except:
            print("[!] Соединение потеряно.")
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
            msg = input()
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
