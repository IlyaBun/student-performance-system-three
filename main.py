"""
main.py - Точка входа в систему ИАС ПолесГУ
Проверка зависимостей, инициализация БД, запуск GUI
"""

import sys
import subprocess


def check_dependencies():
    """Проверка и установка зависимостей"""
    required_packages = ["customtkinter", "matplotlib", "pandas", "bcrypt"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Обнаружены отсутствующие зависимости:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Установка зависимостей...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Зависимости успешно установлены")
        except Exception as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            print("\nПожалуйста, выполните вручную:")
            print("   pip install -r requirements.txt")
            input("\nНажмите Enter для выхода...")
            sys.exit(1)


def main():
    """Точка входа в приложение"""
    print("=" * 60)
    print("🎓 ИАС ПолесГУ - Система оценки успеваемости")
    print("   Инженерный факультет Полесского государственного университета")
    print("=" * 60)
    print()
    
    # Проверка зависимостей
    check_dependencies()
    
    # Импорт сервера (инициализация БД)
    print("📁 Инициализация базы данных...")
    try:
        import server
        print("✅ База данных готова к работе")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    print()
    print("🚀 Запуск графического интерфейса...")
    print()
    print("📋 Учетные данные для входа:")
    print("   👤 Администратор: admin / RwQNt")
    print("   👨‍🏫 Преподаватель: teacher1 / password")
    print("   🎓 Студент: student1 / password")
    print()
    print("=" * 60)
    
    # Запуск клиента
    try:
        import client
        client.start_app()
    except Exception as e:
        print(f"❌ Ошибка запуска GUI: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
