#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для тестирования многопользовательского чата
"""

import subprocess
import time
import sys
import os

def test_server():
    """Тест запуска сервера"""
    print("=== ТЕСТИРОВАНИЕ СЕРВЕРА ===")
    
    # Проверка файлов
    if not os.path.exists('server.py'):
        print("❌ Файл server.py не найден!")
        return False
        
    if not os.path.exists('client.py'):
        print("❌ Файл client.py не найден!")
        return False
    
    print("✅ Файлы сервера и клиента найдены")
    
    # Проверка синтаксиса Python
    try:
        result = subprocess.run([sys.executable, '-m', 'py_compile', 'server.py'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка синтаксиса в server.py: {result.stderr}")
            return False
        print("✅ Синтаксис server.py корректен")
        
        result = subprocess.run([sys.executable, '-m', 'py_compile', 'client.py'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка синтаксиса в client.py: {result.stderr}")
            return False
        print("✅ Синтаксис client.py корректен")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке синтаксиса: {e}")
        return False
    
    print("\n=== ИНСТРУКЦИИ ПО ЗАПУСКУ ===")
    print("1. Запустите сервер в одном терминале:")
    print("   python3 server.py")
    print("\n2. Запустите клиент в другом терминале:")
    print("   python3 client.py")
    print("\n3. Попробуйте команды:")
    print("   /help - справка")
    print("   /create МояКомната - создать комнату")
    print("   /list - список комнат")
    print("   /join <ID> - присоединиться к комнате")
    
    return True

def create_startup_scripts():
    """Создать скрипты для удобного запуска"""
    
    # Скрипт запуска сервера
    server_script = """#!/bin/bash
echo "=== ЗАПУСК СЕРВЕРА ЧАТА ==="
echo "Для остановки нажмите Ctrl+C"
echo "Сервер запускается на порту 12345..."
echo ""
python3 server.py
"""
    
    with open('start_server.sh', 'w', encoding='utf-8') as f:
        f.write(server_script)
    os.chmod('start_server.sh', 0o755)
    
    # Скрипт запуска клиента
    client_script = """#!/bin/bash
echo "=== ЗАПУСК КЛИЕНТА ЧАТА ==="
echo "Подключение к серверу localhost:12345..."
echo ""
python3 client.py
"""
    
    with open('start_client.sh', 'w', encoding='utf-8') as f:
        f.write(client_script)
    os.chmod('start_client.sh', 0o755)
    
    print("✅ Созданы скрипты запуска:")
    print("   ./start_server.sh - запуск сервера")
    print("   ./start_client.sh - запуск клиента")

if __name__ == "__main__":
    print("🚀 ТЕСТИРОВАНИЕ ТЕРМИНАЛЬНОГО ЧАТА")
    print("=" * 50)
    
    if test_server():
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        
        create_startup_scripts()
        
        print("\n🎉 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        print("\nДля быстрого старта:")
        print("1. ./start_server.sh")
        print("2. ./start_client.sh (в новом терминале)")
    else:
        print("\n" + "=" * 50)
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ!")
        print("Исправьте ошибки перед использованием.")
        sys.exit(1)