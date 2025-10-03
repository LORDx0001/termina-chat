import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

clients = []

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                clients.remove(client)

def handle_client(client_socket, address):
    print(f"[+] Подключен: {address}")
    try:
        while True:
            message = client_socket.recv(1024)
            if not message:
                break
            broadcast(message, client_socket)
    except Exception as e:
        print(f"[!] Ошибка с {address}: {e}")
    finally:
        print(f"[-] Отключен: {address}")
        clients.remove(client_socket)
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[Сервер] Запущен на {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()

if __name__ == "__main__":
    start_server()
