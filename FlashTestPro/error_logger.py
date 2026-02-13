"""
Модуль логирования ошибок для SD Card Tester Pro
"""
import os
import sys
import traceback
import logging
from datetime import datetime
import platform
import json
from pathlib import Path

class ErrorLogger:
    """Класс для логирования ошибок программы"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.crash_dir = os.path.join(log_dir, "crashes")
        self.error_log_file = os.path.join(log_dir, "error.log")
        self.debug_log_file = os.path.join(log_dir, "debug.log")

        # Создаем директории для логов
        self._create_directories()
        
        # Настройка логгера
        self.logger = logging.getLogger('SDCardTester')
        self.logger.setLevel(logging.DEBUG)
        
        # Форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Хендлер для файла с ошибками
        error_handler = logging.FileHandler(self.error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Хендлер для файла с отладкой
        debug_handler = logging.FileHandler(self.debug_log_file, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        
        # Добавляем хендлеры
        self.logger.addHandler(error_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(console_handler)

        # Статистика ошибок - ИНИЦИАЛИЗИРУЕМ СТРУКТУРЫ
        self.error_stats = {
            'total_errors': 0,
            'total_warnings': 0,
            'errors_by_type': {},
            'errors_by_module': {}
        }

        # Загружаем статистику
        self._load_stats()
        
        # Логируем запуск
        self.log_info(f"=== SD Card Tester Pro запущен ===")
        self.log_info(f"ОС: {platform.system()} {platform.release()}")
        self.log_info(f"Python: {platform.python_version()}")
        self.log_info(f"Логи сохраняются в: {os.path.abspath(log_dir)}")
    
    def _create_directories(self):
        """Создание директорий для логов"""
        for dir_path in [self.log_dir, self.crash_dir]:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    print(f"Не удалось создать директорию {dir_path}: {e}")
    
    def _load_stats(self):
        """Загрузка статистики ошибок"""
        stats_file = os.path.join(self.log_dir, "error_stats.json")
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.error_stats = json.load(f)
            except:
                pass
    
    def _save_stats(self):
        """Сохранение статистики ошибок"""
        stats_file = os.path.join(self.log_dir, "error_stats.json")
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_stats, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _update_stats(self, error_type, module):
        """Обновление статистики ошибок"""
        try:
            self.error_stats['total_errors'] += 1

            # По типу ошибки - с проверкой наличия ключа
            if error_type not in self.error_stats['errors_by_type']:
                self.error_stats['errors_by_type'][error_type] = 0
            self.error_stats['errors_by_type'][error_type] += 1

            # По модулю - с проверкой наличия ключа
            if module not in self.error_stats['errors_by_module']:
                self.error_stats['errors_by_module'][module] = 0
            self.error_stats['errors_by_module'][module] += 1

            self._save_stats()
        except Exception as e:
            # Не логируем ошибку в статистике, чтобы избежать рекурсии
            print(f"Ошибка обновления статистики: {e}")

    def log_error(self, message, exc_info=True, module="main"):
        """Логирование ошибки"""
        self.logger.error(message, exc_info=exc_info)
        
        # Получаем тип ошибки
        error_type = "Unknown"
        if exc_info and isinstance(exc_info, tuple) and len(exc_info) == 3:
            exc_type, exc_value, _ = exc_info
            if exc_type:
                error_type = exc_type.__name__
        elif exc_info and not isinstance(exc_info, bool):
            exc_type = type(exc_info)
            error_type = exc_type.__name__

        self._update_stats(error_type, module)

        # При критических ошибках создаем crash report
        if "CRITICAL" in message or "FATAL" in message:
            self.create_crash_report(message)
    
    def log_warning(self, message, module="main"):
        """Логирование предупреждения"""
        self.error_stats['total_warnings'] += 1
        self.logger.warning(message)
        self._save_stats()
    
    def log_info(self, message, module="main"):
        """Логирование информации"""
        self.logger.info(message)
    
    def log_debug(self, message, module="main"):
        """Логирование отладочной информации"""
        self.logger.debug(message)
    
    def log_exception(self, e, module="main"):
        """Логирование исключения"""
        error_type = type(e).__name__
        error_msg = str(e)
        tb = traceback.format_exc()
        
        self.logger.error(f"Исключение {error_type}: {error_msg}\n{tb}")
        self._update_stats(error_type, module)
        
        return {
            'type': error_type,
            'message': error_msg,
            'traceback': tb,
            'timestamp': datetime.now().isoformat(),
            'module': module
        }
    
    def create_crash_report(self, error_message=""):
        """Создание отчета о краше программы"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = os.path.join(self.crash_dir, f"crash_{timestamp}.json")
        
        crash_info = {
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_compiler': platform.python_compiler(),
            'argv': sys.argv,
            'modules': self._get_module_list(),
            'traceback': traceback.format_exc(),
            'error_stats': self.error_stats
        }
        
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(crash_info, f, indent=2, ensure_ascii=False)
            self.log_error(f"Создан crash report: {crash_file}", exc_info=False)
            return crash_file
        except Exception as e:
            self.log_error(f"Не удалось создать crash report: {e}", exc_info=False)
            return None
    
    def _get_module_list(self):
        """Получение списка загруженных модулей"""
        modules = {}
        for name, module in sys.modules.items():
            if module and hasattr(module, '__version__'):
                try:
                    modules[name] = module.__version__
                except:
                    modules[name] = "unknown"
        return modules
    
    def get_recent_errors(self, count=10):
        """Получение последних ошибок"""
        errors = []
        try:
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    errors = lines[-count:]
        except:
            pass
        return errors

    def get_error_statistics(self):
        """Получение статистики ошибок"""
        # Безопасно получаем топ-10 ошибок по типу
        errors_by_type = {}
        if self.error_stats['errors_by_type']:
            # Сортируем и берем первые 10 элементов
            sorted_errors = sorted(
                self.error_stats['errors_by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            # Преобразуем обратно в словарь, берем только первые 10
            errors_by_type = dict(sorted_errors[:10])

        # Безопасно получаем топ-10 ошибок по модулю
        errors_by_module = {}
        if self.error_stats['errors_by_module']:
            sorted_modules = sorted(
                self.error_stats['errors_by_module'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            errors_by_module = dict(sorted_modules[:10])

        return {
            'total_errors': self.error_stats['total_errors'],
            'total_warnings': self.error_stats['total_warnings'],
            'errors_by_type': errors_by_type,
            'errors_by_module': errors_by_module
        }

    def clear_old_logs(self, days=7):
        """Очистка старых логов"""
        import time
        current_time = time.time()

        if not os.path.exists(self.log_dir):
            return

        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if (current_time - file_time) > (days * 24 * 3600):
                    try:
                        os.remove(filepath)
                        self.log_info(f"Удален старый лог: {filename}")
                    except:
                        pass

        # Очистка crash reports
        if os.path.exists(self.crash_dir):
            for filename in os.listdir(self.crash_dir):
                filepath = os.path.join(self.crash_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if (current_time - file_time) > (days * 24 * 3600):
                        try:
                            os.remove(filepath)
                        except:
                            pass


# Глобальный экземпляр логгера
_error_logger = None

def get_logger():
    """Получение глобального экземпляра логгера"""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик необработанных исключений"""
    try:
        error_logger = get_logger()
        
        # Логируем критическую ошибку
        error_logger.log_error(
            f"Необработанное исключение: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # Создаем crash report
        crash_file = error_logger.create_crash_report(f"{exc_type.__name__}: {exc_value}")

        # Показываем сообщение пользователю
        try:
            import tkinter.messagebox as tkmb
            error_msg = f"Произошла критическая ошибка:\n\n{exc_type.__name__}: {exc_value}\n\n"
            if crash_file:
                error_msg += f"Отчет сохранен в:\n{crash_file}"
            else:
                error_msg += "Не удалось сохранить отчет об ошибке."

            tkmb.showerror("Критическая ошибка", error_msg)
        except:
            print(f"Критическая ошибка: {exc_type.__name__}: {exc_value}")
            if crash_file:
                print(f"Отчет сохранен: {crash_file}")
    except:
        # Если даже обработчик исключений падает, используем стандартный
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

# Декоратор для логирования ошибок в функциях
def log_errors(func):
    """Декоратор для автоматического логирования ошибок"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.log_exception(e, module=func.__module__)
            raise
    return wrapper

# Контекстный менеджер для логирования
class ErrorContext:
    """Контекстный менеджер для логирования ошибок в блоке кода"""
    def __init__(self, description="", module="main"):
        self.description = description
        self.module = module
        self.logger = get_logger()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.log_exception(exc_val, module=self.module)
            if self.description:
                self.logger.log_error(f"Ошибка в контексте: {self.description}", exc_info=False)
        return False  # Пробрасываем исключение дальше