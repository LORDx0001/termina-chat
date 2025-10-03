import socket
import sys

port = int(sys.argv[1])
s = socket.socket()
s.bind(('0.0.0.0', port))
s.listen(1)
print(f"[server] Listening on port {port}")

conn, addr = s.accept()
print(f"[server] Connected by {addr}")
while True:
    data = conn.recv(1024)
    if not data:
        break
    conn.send(data)
