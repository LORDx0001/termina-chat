import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

clients = []

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            clients.remove(client)

    # Сохраняем сообщение в лог
    try:
        with open("chat.log", "a", encoding="utf-8") as log:
            log.write(message.decode('utf-8') + "\n")
    except Exception as e:
        print(f"[!] Ошибка записи в лог: {e}")

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break

            decoded = message.decode('utf-8').strip()

            if decoded == "/history":
                try:
                    with open("chat.log", "r", encoding="utf-8") as log:
                        history = log.read()
                    client.send(f"[История чата]\n{history}".encode('utf-8'))
                except:
                    client.send("[!] История недоступна.".encode('utf-8'))
                continue

            broadcast(message)
        except:
            break
    client.close()
    if client in clients:
        clients.remove(client)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[+] Сервер запущен на {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        clients.append(client)
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

if __name__ == "__main__":
    start_server()
