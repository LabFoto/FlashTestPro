#!/usr/bin/env python3
"""
FlashTest Pro - Точка входа в приложение
"""
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import FlashTestProApp
from utils.logger import setup_global_logger, get_logger

def main():
    """Главная функция запуска"""
    # Настройка глобального логирования
    logger = setup_global_logger()
    
    try:
        # Создание и запуск приложения
        app = FlashTestProApp()
        app.run()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()