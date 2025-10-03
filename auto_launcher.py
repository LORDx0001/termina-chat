import subprocess
import socket
import time
import os
import logging

logging.basicConfig(filename="/root/terminal-chat/launcher.log", level=logging.INFO)

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def launch_server(port):
    logging.info(f"Запускаю сервер на порту {port}")
    subprocess.Popen(['python3', 'server.py', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def monitor_ports():
    known_ports = set()
    while True:
        try:
            with open("requested_ports.txt", "r") as f:
                ports = {int(line.strip()) for line in f if line.strip().isdigit()}
        except FileNotFoundError:
            ports = set()
        for port in ports:
            if port not in known_ports and not is_port_open(port):
                launch_server(port)
                known_ports.add(port)
        time.sleep(2)

if __name__ == "__main__":
    monitor_ports()
