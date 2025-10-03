import sqlite3
import socket

DB_PATH = "/root/terminal-chat/ports.db"

def get_latest_port():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT port FROM rooms ORDER BY launched_at DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def connect_to_room(port):
    s = socket.socket()
    try:
        s.connect(('127.0.0.1', port))
        print(f"[client] Подключено к порту {port}")
        while True:
            msg = input("> ")
            s.send(msg.encode())
            print(s.recv(1024).decode())
    except Exception as e:
        print(f"[client] Ошибка подключения: {e}")

if __name__ == "__main__":
    port = get_latest_port()
    if port:
        connect_to_room(port)
    else:
        print("[client] Нет активных комнат")
