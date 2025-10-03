import subprocess
import socket
import time
import os

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('84.46.247.15', port)) == 0

def launch_server(port):
    print(f"[+] Запускаю сервер на порту {port}...")
    subprocess.Popen(['python3', 'server.py', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

def launch_client(port):
    subprocess.call(['python3', 'client.py'], env={**os.environ, 'CHAT_PORT': str(port)})

def main():
    port = int(input("Введите порт комнаты: ").strip())

    if not is_port_open(port):
        launch_server(port)
    else:
        print(f"[✓] Сервер на порту {port} уже запущен.")

    launch_client(port)

if __name__ == "__main__":
    main()
