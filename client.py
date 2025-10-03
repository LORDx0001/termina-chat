import socket
import requests

def get_latest_port():
    rooms = requests.get("http://localhost:5000/rooms").json()
    if rooms:
        return rooms[0]["port"]
    return None

def connect_to_room(port):
    s = socket.socket()
    s.connect(('localhost', port))
    print(f"[client] Подключено к порту {port}")
    while True:
        msg = input("> ")
        s.send(msg.encode())
        print(s.recv(1024).decode())

if __name__ == "__main__":
    port = get_latest_port()
    if port:
        connect_to_room(port)
    else:
        print("[client] Нет активных комнат")
