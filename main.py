#!/usr/bin/env python3
"""
main.py - Точка входа ИС ПолесГУ
Проверка зависимостей, инициализация БД, запуск GUI
"""

import sys
import subprocess

def check_dependencies():
    """Проверка и установка зависимостей"""
    required = ['customtkinter', 'matplotlib', 'pandas', 'bcrypt']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠ Отсутствуют зависимости:", ", ".join(missing))
        print("📦 Установка...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Зависимости установлены")
        except Exception as e:
            print(f"❌ Ошибка установки: {e}")
            print("\nПопробуйте вручную: pip install -r requirements.txt")
            input("Нажмите Enter для выхода...")
            sys.exit(1)

def main():
    """Основная функция"""
    print("=" * 50)
    print("   ИНФОРМАЦИОННАЯ СИСТЕМА ПОЛЕСГУ")
    print("   Управление успеваемостью студентов")
    print("=" * 50)
    
    # Проверка зависимостей
    check_dependencies()
    
    # Импорт и инициализация
    try:
        from server import Database
        print("📁 Инициализация базы данных...")
        db = Database()
        print("✅ База данных готова")
        
        # Запуск GUI
        print("🚀 Запуск интерфейса...")
        from client import LoginWindow
        app = LoginWindow(db)
        app.mainloop()
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
