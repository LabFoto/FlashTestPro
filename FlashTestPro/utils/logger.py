"""
Модуль логирования с автоматической очисткой старых логов
"""
import os
import logging
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# Глобальный логгер
_logger = None

def setup_global_logger(log_dir="logs", log_level=logging.INFO):
    """Настройка глобального логгера"""
    global _logger
    
    # Создание директории для логов
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(os.path.join(log_dir, "crashes"), exist_ok=True)
    
    # Очистка старых логов (>30 дней)
    _clean_old_logs(log_dir, days=30)
    
    # Настройка логгера
    _logger = logging.getLogger('FlashTestPro')
    _logger.setLevel(log_level)
    
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Файловый handler с ротацией
    log_file = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Добавление handlers
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    # Отдельный файл для ошибок
    error_file = os.path.join(log_dir, "error.log")
    error_handler = RotatingFileHandler(
        error_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    _logger.addHandler(error_handler)
    
    return _logger

def _clean_old_logs(log_dir: str, days: int = 30):
    """Очистка логов старше указанного количества дней"""
    try:
        now = time.time()
        cutoff = now - (days * 24 * 3600)
        
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            
            # Пропускаем директории
            if os.path.isdir(filepath):
                continue
            
            # Проверяем время модификации
            if os.path.getmtime(filepath) < cutoff:
                try:
                    os.remove(filepath)
                    print(f"Удален старый лог: {filename}")
                except Exception as e:
                    print(f"Не удалось удалить {filename}: {e}")
        
        # Очистка crash reports
        crash_dir = os.path.join(log_dir, "crashes")
        if os.path.exists(crash_dir):
            for filename in os.listdir(crash_dir):
                filepath = os.path.join(crash_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                        
    except Exception as e:
        print(f"Ошибка при очистке логов: {e}")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Получение логгера"""
    global _logger
    if _logger is None:
        _logger = setup_global_logger()
    
    if name:
        return _logger.getChild(name)
    return _logger

def log_crash(exc_type, exc_value, exc_traceback):
    """Логирование критических ошибок"""
    logger = get_logger('crash')
    logger.critical(
        "Необработанное исключение", 
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Сохранение в отдельный файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_file = os.path.join("logs", "crashes", f"crash_{timestamp}.log")
    
    try:
        with open(crash_file, 'w', encoding='utf-8') as f:
            import traceback
            f.write(f"Время: {datetime.now()}\n")
            f.write(f"Тип: {exc_type.__name__}\n")
            f.write(f"Сообщение: {exc_value}\n")
            f.write("Traceback:\n")
            traceback.print_tb(exc_traceback, file=f)
    except:
        pass

# Установка глобального обработчика исключений
sys.excepthook = log_crash