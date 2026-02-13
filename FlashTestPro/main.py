#!/usr/bin/env python3
"""
SD Card Tester Pro - Точка входа
"""
import sys
from error_logger import get_logger
from error_logger import global_exception_handler

# Устанавливаем глобальный обработчик исключений
sys.excepthook = global_exception_handler

def main():
    """Основная функция запуска"""
    try:
        from main_app import SDCardTesterApp
        app = SDCardTesterApp()
        app.run()
    except ImportError as e:
        logger = get_logger()
        logger.log_error(f"Ошибка импорта модулей: {e}")
        print(f"Ошибка: Не удалось загрузить модули приложения. {e}")
        print("Убедитесь, что все файлы находятся в правильных директориях.")
        sys.exit(1)
    except Exception as e:
        logger = get_logger()
        logger.log_exception(e, module="main")
        sys.exit(1)

if __name__ == "__main__":
    main()