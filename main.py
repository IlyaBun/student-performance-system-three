"""
main.py - Точка входа в систему оценки успеваемости студентов ПолесГУ
Проверка зависимостей, инициализация БД, запуск GUI
"""

import sys
import subprocess


def check_dependencies():
    """Проверка и установка необходимых зависимостей"""
    required_packages = ["customtkinter", "matplotlib", "pandas", "bcrypt"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Обнаружены отсутствующие зависимости:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\nУстановка зависимостей...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Зависимости успешно установлены!")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка установки зависимостей: {e}")
            print("\nПожалуйста, установите зависимости вручную:")
            print("  pip install -r requirements.txt")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
    
    return True


def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("ИАС ПолесГУ - Система оценки успеваемости студентов")
    print("=" * 60)
    
    # Проверка зависимостей
    check_dependencies()
    
    print("\nЗапуск системы...")
    
    # Импорт и запуск приложения
    try:
        from client import run_app
        run_app()
    except Exception as e:
        print(f"\nКритическая ошибка при запуске: {e}")
        print("\nВозможные причины:")
        print("  1. Не установлены зависимости (выполните: pip install -r requirements.txt)")
        print("  2. Проблемы с графической средой (требуется дисплей)")
        print("  3. Повреждение файлов программы")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
