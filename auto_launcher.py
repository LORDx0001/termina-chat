import subprocess
import socket
import time
import os
import logging

logging.basicConfig(
    filename="/root/terminal-chat/launcher.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

SERVER_PATH = "/root/terminal-chat/server.py"
PORT_FILE = "/root/terminal-chat/requested_ports.txt"

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def launch_server(port):
    logging.info(f"Запускаю сервер на порту {port}")
    print(f"[auto_launcher] Запускаю сервер на порту {port}")
    try:
        subprocess.Popen(['python3', SERVER_PATH, str(port)],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Ошибка запуска порта {port}: {e}")
        print(f"[auto_launcher] Ошибка запуска порта {port}: {e}")

def initialize_ports():
    if not os.path.exists(PORT_FILE) or os.stat(PORT_FILE).st_size == 0:
        with open(PORT_FILE, "w") as f:
            for port in range(12345, 12350):
                f.write(f"{port}\n")
        logging.info("Инициализированы порты: 12345–12349")
        print("[auto_launcher] Инициализированы порты: 12345–12349")

def monitor_ports():
    known_ports = set()
    while True:
        print("[auto_launcher] Цикл запущен...")
        try:
            with open(PORT_FILE, "r") as f:
                ports = {int(line.strip()) for line in f if line.strip().isdigit()}
        except Exception as e:
            logging.error(f"Ошибка чтения портов: {e}")
            ports = set()
        for port in sorted(ports):
            if port not in known_ports and not is_port_open(port):
                launch_server(port)
                known_ports.add(port)
        time.sleep(2)

if __name__ == "__main__":
    initialize_ports()
    monitor_ports()
