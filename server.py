import socket
import threading
import sqlite3
import sys

clients = []

def broadcast(message, conn, port):
    for client in clients:
        try:
            client.send(message)
        except:
            clients.remove(client)

    try:
        conn.execute("INSERT INTO messages (port, content) VALUES (?, ?)", (port, message.decode('utf-8')))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка записи в БД: {e}")

def handle_client(client, conn, port):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            broadcast(message, conn, port)
        except:
            break
    client.close()
    if client in clients:
        clients.remove(client)

def start_server(port):
    conn = sqlite3.connect("chat.db", check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port INTEGER,
            content TEXT
        )
    """)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen()

    print(f"[+] Сервер запущен на порту {port}")

    while True:
        client, addr = server.accept()
        clients.append(client)

        rows = conn.execute("SELECT content FROM messages WHERE port = ?", (port,)).fetchall()
        for row in rows:
            client.send(row[0].encode('utf-8'))

        threading.Thread(target=handle_client, args=(client, conn, port), daemon=True).start()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python3 server.py <порт>")
        sys.exit(1)

    port = int(sys.argv[1])
    start_server(port)
