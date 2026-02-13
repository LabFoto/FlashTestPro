"""
Модуль бизнес-логики для SD Card Tester Pro
Содержит всю функциональность, не связанную с UI
"""
import os
import platform
import ctypes
import sys
import time
import psutil
from datetime import datetime, timedelta
import json
import queue
import threading
import subprocess
import traceback
import struct
import win32file
import win32con
import win32api
from error_logger import get_logger

class TesterLogic:
    """Класс бизнес-логики тестирования SD карт"""
    
    def __init__(self):
        self.logger = get_logger()
        self.message_queue = queue.Queue()
        
        # Состояние тестирования
        self.test_running = False
        self.test_paused = False
        self.cancel_requested = False
        
        # Данные тестирования
        self.speed_data = []
        self.bad_sectors = []
        self.test_start_time = None
        self.current_pass = 0
        self.total_passes = 1
        self.current_position = 0
        self.total_size = 0
        self.current_drive = None
        self.sector_size = 512
        
        # Конфигурация
        self.config = self._load_default_config()
        
        # Коллбеки для обновления UI
        self.ui_callbacks = {}
        
    # ========== УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ ==========
    
    def _load_default_config(self):
        """Загрузка конфигурации по умолчанию"""
        return {
            "app": {
                "name": "SD Card Tester Pro",
                "version": "1.0.0",
                "auto_save_log": False,
                "auto_update_stats": True,
            },
            "testing": {
                "default_passes": 1,
                "chunk_size_mb": 1024,
                "test_patterns": [],
                "verify_read": False,
                "auto_format": False,
                "default_filesystem": "FAT32",
            },
            "ui": {
                "theme": "dark",
                "language": "ru",
                "chart_points": 100,
                "font_size": 9,
                "show_warnings": True,
            },
        }
    
    def load_config(self, config_path="config.json"):
        """Загрузка конфигурации из файла"""
        default_config = self._load_default_config()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self._merge_configs(default_config, user_config)
                self.logger.log_info(f"Конфигурация загружена из {config_path}")
            except Exception as e:
                self.logger.log_error(f"Ошибка загрузки конфигурации: {e}")
        
        self.config = default_config
        return self.config
    
    def save_config(self, config_path="config.json"):
        """Сохранение конфигурации в файл"""
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.log_info(f"Конфигурация сохранена в {config_path}")
            return True
        except Exception as e:
            self.logger.log_error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def _merge_configs(self, default, user):
        """Рекурсивное объединение конфигураций"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def update_config(self, section, key, value):
        """Обновление конкретного параметра конфигурации"""
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            return True
        return False
    
    # ========== РАБОТА С ДИСКАМИ ==========
    
    def get_drives_list(self):
        """Получение списка всех дисков с информацией"""
        drives = []
        
        if platform.system() == "Windows":
            drives = self._get_windows_drives()
        else:
            drives = self._get_unix_drives()
            
        return drives
    
    def _get_windows_drives(self):
        """Получение списка дисков в Windows"""
        drives = []
        
        try:
            import win32api
            import win32file
            import string
            
            for drive in string.ascii_uppercase:
                drive_path = f"{drive}:\\"
                try:
                    # Проверяем существование диска
                    if not os.path.exists(drive_path):
                        continue
                        
                    drive_type = win32file.GetDriveType(drive_path)
                    
                    # Только съемные и фиксированные диски (исключаем CD-ROM)
                    if drive_type in [win32file.DRIVE_REMOVABLE, win32file.DRIVE_FIXED]:
                        try:
                            free_bytes, total_bytes, _ = win32api.GetDiskFreeSpaceEx(drive_path)
                            size_gb = total_bytes / (1024**3)
                            
                            # Получаем информацию о секторах
                            try:
                                sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = \
                                    win32file.GetDiskFreeSpace(drive_path)
                                total_sectors = total_clusters * sectors_per_cluster
                                self.logger.log_debug(f"Диск {drive_path}: секторов={total_sectors}, сектор={bytes_per_sector} байт")
                            except:
                                total_sectors = 0
                                bytes_per_sector = 512
                            
                            # Определение типа
                            if drive_type == win32file.DRIVE_REMOVABLE:
                                drive_type_str = "Съемный"
                                tag_color = "#4caf50"
                            elif drive_type == win32file.DRIVE_FIXED:
                                drive_type_str = "Внутренний"
                                tag_color = "#ff5252"
                            else:
                                drive_type_str = "Неизвестно"
                                tag_color = "#888888"
                            
                            # Получение файловой системы
                            fs = ""
                            try:
                                volume_info = win32api.GetVolumeInformation(drive_path)
                                fs = volume_info[4]
                            except:
                                fs = "Неизвестно"
                            
                            # Определение системного диска
                            is_system = False
                            try:
                                if os.path.exists(os.path.join(drive_path, "Windows")):
                                    is_system = True
                                    drive_type_str = "СИСТЕМНЫЙ"
                                    tag_color = "#f44336"
                            except:
                                pass
                            
                            drives.append({
                                "path": drive_path,
                                "type": drive_type_str,
                                "size": f"{size_gb:.1f} GB",
                                "size_bytes": total_bytes,
                                "total_sectors": total_sectors,
                                "bytes_per_sector": bytes_per_sector,
                                "fs": fs,
                                "color": tag_color,
                                "is_system": is_system,
                            })
                        except Exception as e:
                            self.logger.log_debug(f"Ошибка получения информации о диске {drive_path}: {e}")
                            continue
                except:
                    continue
        except ImportError:
            self.logger.log_error("Не удалось импортировать win32api. Установите pywin32")
        
        return drives
    
    def _get_unix_drives(self):
        """Получение списка дисков в Linux/macOS"""
        drives = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                size_gb = usage.total / (1024**3)
                
                # Определение системного диска
                is_system = partition.mountpoint in ["/", "/boot", "/etc", "/System"]
                
                drive_type = "Внутренний"
                if "removable" in partition.opts or "usb" in partition.opts:
                    drive_type = "Съемный"
                
                drives.append({
                    "path": partition.mountpoint,
                    "type": "СИСТЕМНЫЙ" if is_system else drive_type,
                    "size": f"{size_gb:.1f} GB",
                    "size_bytes": usage.total,
                    "fs": partition.fstype,
                    "color": "#f44336" if is_system else "#ff5252",
                    "is_system": is_system,
                })
            except:
                continue
        
        return drives
    
    def get_drive_info(self, drive_path):
        """Получение подробной информации о диске"""
        info = {
            "path": drive_path,
            "label": self.get_volume_label(drive_path),
            "is_system": False,
            "size_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "percent_used": 0,
            "filesystem": "Неизвестно"
        }
        
        try:
            usage = psutil.disk_usage(drive_path)
            info["size_bytes"] = usage.total
            info["used_bytes"] = usage.used
            info["free_bytes"] = usage.free
            info["percent_used"] = usage.percent
        except:
            pass
        
        # Проверка системного диска
        if platform.system() == "Windows":
            info["is_system"] = drive_path == "C:\\" or os.path.exists(os.path.join(drive_path, "Windows"))
        else:
            info["is_system"] = drive_path in ["/", "/boot", "/etc"]
        
        return info
    
    def get_volume_label(self, drive_path):
        """Получить метку тома"""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                volume_name_buffer = ctypes.create_unicode_buffer(256)
                
                root_path = drive_path
                if not root_path.endswith('\\'):
                    root_path += '\\'
                
                success = kernel32.GetVolumeInformationW(
                    root_path, volume_name_buffer, len(volume_name_buffer),
                    None, None, None, None, 0
                )
                
                if success and volume_name_buffer.value:
                    return volume_name_buffer.value
                return "Нет метки"
                
            elif platform.system() == "Linux":
                import subprocess
                result = subprocess.run(['blkid', '-o', 'value', '-s', 'LABEL', drive_path],
                                       capture_output=True, text=True)
                label = result.stdout.strip()
                return label if label else "Нет метки"
                
            elif platform.system() == "Darwin":
                import subprocess
                disk_id = os.path.basename(drive_path)
                result = subprocess.run(['diskutil', 'info', disk_id],
                                       capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Volume Name' in line:
                        label = line.split(':')[1].strip()
                        return label if label else "Нет метки"
                return "Нет метки"
        except Exception as e:
            self.logger.log_debug(f"Ошибка получения метки тома: {e}")
            return "Не определено"
    
    def rename_drive(self, drive_path, new_name):
        """Переименование диска"""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                root_path = drive_path if drive_path.endswith('\\') else drive_path + '\\'
                result = kernel32.SetVolumeLabelW(root_path, new_name + '\0')
                
                if result:
                    self.logger.log_info(f"Диск {drive_path} переименован в '{new_name}'")
                    return True, f"Диск переименован в '{new_name}'"
                else:
                    error_code = ctypes.GetLastError()
                    return False, f"Не удалось переименовать диск (код ошибки: {error_code})"
                    
            elif platform.system() == "Linux":
                import subprocess
                result = subprocess.run(['sudo', 'e2label', drive_path, new_name],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Диск переименован в '{new_name}'"
                else:
                    return False, f"Ошибка переименования: {result.stderr}"
                    
            elif platform.system() == "Darwin":
                import subprocess
                disk_id = os.path.basename(drive_path)
                result = subprocess.run(['diskutil', 'rename', disk_id, new_name],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Диск переименован в '{new_name}'"
                else:
                    return False, f"Ошибка переименования: {result.stderr}"
                    
        except Exception as e:
            self.logger.log_error(f"Ошибка переименования диска: {e}")
            return False, str(e)
    
    # ========== ПРОВЕРКА ПРАВ ==========
    
    def is_admin(self):
        """Проверка прав администратора"""
        if platform.system() == "Windows":
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0
    
    def check_write_permissions(self, drive_path):
        """Проверка прав на запись"""
        try:
            test_file = os.path.join(drive_path, ".write_test")
            with open(test_file, 'wb') as f:
                f.write(b'test')
            os.remove(test_file)
            return True
        except Exception as e:
            self.logger.log_debug(f"Нет прав на запись: {e}")
            return False
    
    # ========== ТЕСТИРОВАНИЕ ==========
    
    def _unmount_drive_windows(self, drive_letter):
        """Размонтирование диска в Windows для прямого доступа"""
        try:
            # Используем mountvol для размонтирования
            result = subprocess.run(
                f'mountvol {drive_letter}: /p',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.log_info(f"Диск {drive_letter}: размонтирован")
                return True
            else:
                self.logger.log_debug(f"Не удалось размонтировать диск {drive_letter}: {result.stderr}")
                return False
        except Exception as e:
            self.logger.log_debug(f"Ошибка размонтирования: {e}")
            return False
    
    def _mount_drive_windows(self, drive_letter):
        """Монтирование диска в Windows"""
        try:
            result = subprocess.run(
                f'mountvol {drive_letter}: \\\\?\\Volume{{{drive_letter}}}',
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def _open_disk_direct_windows(self, drive_path):
        """Открытие диска для прямого доступа в Windows с диагностикой"""
        try:
            drive_letter = drive_path[0]
            physical_path = f"\\\\.\\{drive_letter}:"

            self._emit('log', f"Попытка открыть диск: {physical_path}", "debug")

            # Сначала пробуем открыть для чтения (чтобы проверить доступ)
            try:
                handle_read = win32file.CreateFile(
                    physical_path,
                    win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                if handle_read and handle_read != win32file.INVALID_HANDLE_VALUE:
                    win32file.CloseHandle(handle_read)
                    self._emit('log', "✅ Доступ на чтение есть", "debug")
                else:
                    self._emit('log', "❌ Нет доступа на чтение", "debug")
            except Exception as e:
                self._emit('log', f"❌ Ошибка чтения: {e}", "debug")

            # Пробуем открыть для записи
            self._emit('log', "Попытка открыть для записи...", "debug")

            handle = win32file.CreateFile(
                physical_path,
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                0,  # Без флагов для совместимости
                None
            )

            if handle and handle != win32file.INVALID_HANDLE_VALUE:
                self._emit('log', "✅ Диск открыт для записи", "success")
                return handle, "direct"
            else:
                self._emit('log', "❌ Не удалось открыть диск для записи", "warning")

        except Exception as e:
            self._emit('log', f"❌ Ошибка открытия диска: {e}", "error")
            self.logger.log_debug(f"Детали ошибки: {traceback.format_exc()}")

        return None, None
    
    def _open_disk_fallback_windows(self, drive_path):
        """Запасной метод: запись через файловую систему"""
        try:
            # Создаем тестовый файл и пишем в него
            test_file = os.path.join(drive_path, ".sd_test_temp.dat")
            self.logger.log_info(f"Используется запасной метод: запись в файл {test_file}")
            return test_file, "file"
        except Exception as e:
            self.logger.log_error(f"Не удалось создать тестовый файл: {e}")
            return None, None
    
    def _write_sector_direct_windows(self, handle, sector_num, data, access_type):
        """Запись сектора через прямой доступ"""
        try:
            if access_type == "direct" or access_type == "unmounted":
                # Прямая запись в сектор
                offset = sector_num * self.sector_size
                win32file.SetFilePointer(handle, offset, win32file.FILE_BEGIN)
                win32file.WriteFile(handle, data)
                return True
            else:
                # Запись в файл (не настоящая запись секторов)
                return False
        except Exception as e:
            self.logger.log_debug(f"Ошибка прямой записи сектора {sector_num}: {e}")
            return False
    
    def _write_sector_file_windows(self, file_path, sector_num, data):
        """Запись через файл (имитация для тестирования)"""
        try:
            # Для тестирования пишем в файл с отступом
            with open(file_path, 'r+b') as f:
                f.seek(sector_num * self.sector_size)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception as e:
            self.logger.log_debug(f"Ошибка записи в файл: {e}")
            return False
    
    def start_test(self, drive_path, test_params):
        """Запуск тестирования"""
        self.current_drive = drive_path
        self.total_passes = test_params.get('passes', 1)
        self.test_patterns = {
            'ones': test_params.get('test_ones', False),
            'zeros': test_params.get('test_zeros', False),
            'random': test_params.get('test_random', False),
            'verify': test_params.get('test_verify', False)
        }
        self.auto_format = test_params.get('auto_format', False)
        self.filesystem = test_params.get('filesystem', 'FAT32')
        
        # Сброс данных
        self.speed_data = []
        self.bad_sectors = []
        self.current_pass = 0
        self.current_position = 0
        self.test_running = True
        self.test_paused = False
        self.cancel_requested = False
        self.test_start_time = datetime.now()
        
        # Получаем размер диска
        try:
            if platform.system() == "Windows":
                try:
                    sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = \
                        win32file.GetDiskFreeSpace(drive_path)
                    self.sector_size = bytes_per_sector
                    self.total_sectors = total_clusters * sectors_per_cluster
                    self.total_size = (self.total_sectors * self.sector_size) / (1024**3)
                except:
                    self.total_size = psutil.disk_usage(drive_path).total / (1024**3)
                    self.total_sectors = int(psutil.disk_usage(drive_path).total / 512)
            else:
                self.total_size = psutil.disk_usage(drive_path).total / (1024**3)
                self.total_sectors = int(psutil.disk_usage(drive_path).total / 512)
        except Exception as e:
            self.logger.log_error(f"Ошибка получения размера диска: {e}")
            self.total_size = 100  # Fallback
            self.total_sectors = int(100 * 1024**3 / 512)
        
        self._emit('log', f"Размер диска: {self.total_size:.1f} GB", "info")
        self._emit('log', f"Всего секторов: {self.total_sectors}", "info")
        self._emit('log', f"Размер сектора: {self.sector_size} байт", "info")
        
        # Проверяем, можем ли мы писать напрямую
        self.write_mode = "file"  # По умолчанию через файл
        
        if platform.system() == "Windows":
            self._emit('log', "Проверка возможности прямого доступа к диску...", "info")
            handle, access_type = self._open_disk_direct_windows(drive_path)
            
            if handle:
                win32file.CloseHandle(handle)
                self.write_mode = "direct"
                self._emit('log', "✅ Прямой доступ к диску доступен", "success")
            else:
                self._emit('log', "⚠️ Прямой доступ недоступен. Используется запись через файл.", "warning")
                self._emit('log', "Для полного тестирования запустите программу от имени Администратора", "warning")
        
        # Запускаем тест в отдельном потоке
        test_thread = threading.Thread(
            target=self._run_test_thread,
            args=(drive_path,),
            daemon=True,
            name="TestThread"
        )
        test_thread.start()
        
        return True
    
    def _run_test_thread(self, drive_path):
        """Основной поток тестирования"""
        handle = None
        access_type = None
        test_file = None
        
        try:
            self._emit('log', f"Начало тестирования диска: {drive_path}", "info")
            self._emit('log', f"Количество проходов: {self.total_passes}", "info")
            
            # Открываем диск для доступа
            if platform.system() == "Windows":
                if self.write_mode == "direct":
                    handle, access_type = self._open_disk_direct_windows(drive_path)
                    if not handle:
                        self._emit('error', "Не удалось открыть диск для прямого доступа")
                        return
                else:
                    # Запасной метод - создаем тестовый файл
                    test_file = os.path.join(drive_path, ".sd_test_temp.dat")
                    self._emit('log', f"Создан тестовый файл: {test_file}", "info")
                    
                    # Создаем пустой файл нужного размера
                    with open(test_file, 'wb') as f:
                        f.seek(int(self.total_size * 1024**3) - 1)
                        f.write(b'\0')
            else:
                # Linux/macOS
                try:
                    handle = open(drive_path, 'r+b')
                    access_type = "direct"
                except:
                    test_file = os.path.join(drive_path, ".sd_test_temp.dat")
                    self._emit('log', f"Используется запись в файл: {test_file}", "info")
            
            # Основной цикл тестирования
            for pass_num in range(1, self.total_passes + 1):
                if self.cancel_requested:
                    break
                
                while self.test_paused:
                    time.sleep(0.1)
                    if self.cancel_requested:
                        break
                
                self.current_pass = pass_num
                self._emit('log', f"Проход {pass_num}/{self.total_passes} начат", "info")
                
                # Запускаем тесты для выбранных паттернов
                if self.test_patterns.get('ones', False):
                    self._emit('log', "Тест: запись единиц (0xFF)", "info")
                    self._write_pattern(drive_path, handle, test_file, "ones", pass_num, access_type)
                
                if self.test_patterns.get('zeros', False):
                    self._emit('log', "Тест: запись нулей (0x00)", "info")
                    self._write_pattern(drive_path, handle, test_file, "zeros", pass_num, access_type)
                
                if self.test_patterns.get('random', False):
                    self._emit('log', "Тест: случайные данные", "info")
                    self._write_pattern(drive_path, handle, test_file, "random", pass_num, access_type)
                
                self._emit('log', f"Проход {pass_num}/{self.total_passes} завершен", "success")
                
                # Обновляем прогресс
                progress = (pass_num / self.total_passes) * 100
                self._emit('progress', progress)
            
            # Удаляем тестовый файл, если использовали
            if test_file and os.path.exists(test_file):
                try:
                    os.remove(test_file)
                    self._emit('log', "Тестовый файл удален", "info")
                except Exception as e:
                    self._emit('log', f"Не удалось удалить тестовый файл: {e}", "warning")
            
            # Форматирование
            if self.auto_format and self.filesystem != "Don't format" and not self.cancel_requested:
                self._emit('log', f"Форматирование в {self.filesystem}...", "info")
                if self._format_drive(drive_path, self.filesystem):
                    self._emit('log', "Форматирование завершено", "success")
                else:
                    self._emit('log', "Ошибка форматирования", "error")
            
            if not self.cancel_requested:
                self._emit('complete', "Тестирование успешно завершено!")
            else:
                self._emit('log', "Тест прерван пользователем", "warning")
                
        except PermissionError:
            self._emit('error', f"Нет прав на запись на диск {drive_path}! Запустите от администратора/root.")
        except Exception as e:
            self._emit('error', f"Ошибка тестирования: {str(e)}")
            self.logger.log_exception(e)
        finally:
            if handle:
                try:
                    if platform.system() == "Windows":
                        win32file.CloseHandle(handle)
                    else:
                        handle.close()
                except:
                    pass
            self.test_running = False
    
    def _write_pattern(self, drive_path, handle, test_file, pattern_type, pass_num, access_type):
        """Запись паттерна на диск"""
        try:
            # Подготовка тестовых данных
            if pattern_type == "ones":
                pattern_data = b'\xFF' * self.sector_size
            elif pattern_type == "zeros":
                pattern_data = b'\x00' * self.sector_size
            else:  # random
                pattern_data = os.urandom(self.sector_size)
            
            # Определяем диапазон секторов для этого прохода
            sectors_per_pass = self.total_sectors // self.total_passes
            start_sector = (pass_num - 1) * sectors_per_pass
            end_sector = start_sector + sectors_per_pass if pass_num < self.total_passes else self.total_sectors
            
            total_sectors_to_write = end_sector - start_sector
            sectors_written = 0
            bad_sectors_found = 0
            
            start_time = time.time()
            last_update_time = start_time
            
            for sector in range(start_sector, end_sector):
                if self.cancel_requested:
                    break
                
                while self.test_paused:
                    time.sleep(0.1)
                    if self.cancel_requested:
                        break
                
                success = False
                
                # Пытаемся записать в зависимости от режима
                if handle and access_type in ["direct", "unmounted"]:
                    # Прямая запись в сектор
                    try:
                        offset = sector * self.sector_size
                        win32file.SetFilePointer(handle, offset, win32file.FILE_BEGIN)
                        win32file.WriteFile(handle, pattern_data)
                        success = True
                    except Exception as e:
                        self.logger.log_debug(f"Ошибка записи сектора {sector}: {e}")
                        success = False
                elif test_file:
                    # Запись в файл (имитация)
                    try:
                        with open(test_file, 'r+b') as f:
                            f.seek(sector * self.sector_size)
                            f.write(pattern_data)
                            if sector % 100 == 0:  # Сбрасываем каждые 100 секторов
                                f.flush()
                                os.fsync(f.fileno())
                        success = True
                    except Exception as e:
                        self.logger.log_debug(f"Ошибка записи в файл сектора {sector}: {e}")
                        success = False
                
                if success:
                    sectors_written += 1
                    self.current_position = sectors_written * self.sector_size / (1024**3)
                else:
                    # Битый сектор
                    bad_sectors_found += 1
                    self.bad_sectors.append(sector)
                    self._emit('bad_sector', sector, f"Ошибка записи ({pattern_type})", pass_num)
                    self._emit('log', f"⚠️ Битый сектор: {sector}", "error")
                
                # Обновление скорости и прогресса
                current_time = time.time()
                if current_time - last_update_time >= 0.5:  # Обновляем каждые 0.5 секунды
                    elapsed = current_time - start_time
                    if elapsed > 0 and sectors_written > 0:
                        bytes_written = sectors_written * self.sector_size
                        speed_mb = (bytes_written / (1024 * 1024)) / elapsed
                        
                        # Сохраняем данные для графика
                        self.speed_data.append((elapsed, speed_mb))
                        self._emit('speed', speed_mb, elapsed)
                        
                        # Прогресс для текущего паттерна
                        progress = (sectors_written / total_sectors_to_write) * 100
                        self._emit('progress_detail', progress)
                        
                        self._emit('log', 
                                 f"Сектор {sector}/{end_sector-1} | "
                                 f"Скорость: {speed_mb:.1f} MB/s | "
                                 f"Битых: {bad_sectors_found}", "debug")
                    
                    last_update_time = current_time
            
            # Итоговая статистика для паттерна
            elapsed = time.time() - start_time
            if sectors_written > 0 and elapsed > 0:
                avg_speed = (sectors_written * self.sector_size / (1024 * 1024)) / elapsed
                self._emit('log', 
                         f"Паттерн {pattern_type} завершен: "
                         f"записано {sectors_written} секторов, "
                         f"средняя скорость {avg_speed:.1f} MB/s, "
                         f"битых секторов: {bad_sectors_found}", 
                         "success" if bad_sectors_found == 0 else "warning")
            
        except Exception as e:
            self._emit('error', f"Ошибка в паттерне {pattern_type}: {str(e)}")
    
    def _format_drive(self, drive_path, filesystem):
        """Форматирование диска"""
        try:
            if platform.system() == "Windows":
                import subprocess
                drive_letter = drive_path[0]
                cmd = f'cmd /c echo y | format.com {drive_letter}: /FS:{filesystem} /Q'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return result.returncode == 0
                
            elif platform.system() == "Linux":
                import subprocess
                if filesystem == "FAT32":
                    cmd = ['mkfs.vfat', '-F32', drive_path]
                elif filesystem == "EXT4":
                    cmd = ['mkfs.ext4', '-F', drive_path]
                elif filesystem == "exFAT":
                    cmd = ['mkfs.exfat', drive_path]
                else:
                    return False
                
                if os.geteuid() != 0:
                    cmd = ['sudo'] + cmd
                
                subprocess.run(cmd, check=True)
                return True
                
            elif platform.system() == "Darwin":
                import subprocess
                disk_id = os.path.basename(drive_path)
                if filesystem == "FAT32":
                    cmd = ['diskutil', 'eraseDisk', 'FAT32', 'SD_CARD', disk_id]
                elif filesystem == "exFAT":
                    cmd = ['diskutil', 'eraseDisk', 'exFAT', 'SD_CARD', disk_id]
                else:
                    return False
                
                subprocess.run(cmd, check=True)
                return True
                
        except Exception as e:
            self._emit('log', f"Ошибка форматирования: {e}", "error")
            return False
    
    # ========== УПРАВЛЕНИЕ ТЕСТОМ ==========
    
    def pause_test(self):
        """Пауза/продолжение теста"""
        if self.test_running:
            self.test_paused = not self.test_paused
            status = "приостановлен" if self.test_paused else "продолжен"
            self._emit('log', f"Тест {status}", "warning" if self.test_paused else "success")
            return self.test_paused
        return None
    
    def stop_test(self):
        """Остановка теста"""
        if self.test_running:
            self.cancel_requested = True
            self._emit('log', "Запрошена остановка теста...", "warning")
            return True
        return False
    
    # ========== СТАТИСТИКА ==========
    
    def get_statistics(self):
        """Получение текущей статистики"""
        stats = {
            'total_size': self.total_size,
            'current_position': self.current_position,
            'current_pass': self.current_pass,
            'total_passes': self.total_passes,
            'bad_sectors_count': len(self.bad_sectors),
            'test_running': self.test_running,
            'test_paused': self.test_paused,
        }
        
        if self.speed_data:
            speeds = [s[1] for s in self.speed_data[-100:]]  # Последние 100 точек
            stats['avg_speed'] = sum(speeds) / len(speeds) if speeds else 0
            stats['max_speed'] = max(speeds) if speeds else 0
            stats['min_speed'] = min(speeds) if speeds else 0
        else:
            stats['avg_speed'] = 0
            stats['max_speed'] = 0
            stats['min_speed'] = 0
        
        if self.test_start_time:
            elapsed = datetime.now() - self.test_start_time
            stats['elapsed_time'] = str(elapsed).split('.')[0]
            stats['elapsed_seconds'] = elapsed.total_seconds()
        else:
            stats['elapsed_time'] = "--:--:--"
            stats['elapsed_seconds'] = 0
        
        return stats
    
    # ========== СИСТЕМНАЯ ИНФОРМАЦИЯ ==========
    
    def get_system_info(self):
        """Получение информации о системе"""
        import psutil
        import platform
        
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]
        
        return {
            'os': f"{platform.system()} {platform.release()}",
            'python': platform.python_version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor() or "Unknown",
            'memory_total': psutil.virtual_memory().total,
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_count': len(psutil.disk_partitions()),
            'uptime': uptime_str,
            'hostname': platform.node(),
            'is_admin': self.is_admin()
        }
    
    # ========== ЭКСПОРТ ОТЧЕТОВ ==========
    
    def export_report(self, filepath, format_type='txt'):
        """Экспорт отчета о тестировании"""
        try:
            if format_type == 'txt':
                return self._export_text_report(filepath)
            elif format_type == 'html':
                return self._export_html_report(filepath)
            elif format_type == 'json':
                return self._export_json_report(filepath)
            else:
                return False
        except Exception as e:
            self.logger.log_error(f"Ошибка экспорта отчета: {e}")
            return False
    
    def _export_text_report(self, filepath):
        """Экспорт в текстовый файл"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SD CARD TESTER PRO - ОТЧЕТ О ТЕСТИРОВАНИИ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Версия: {self.config['app']['version']}\n")
            f.write(f"Диск: {self.current_drive}\n")
            f.write(f"Режим доступа: {'Прямой' if self.write_mode == 'direct' else 'Через файл'}\n")
            f.write(f"Проходов: {self.current_pass}/{self.total_passes}\n")
            f.write(f"Размер диска: {self.total_size:.1f} GB\n")
            f.write(f"Всего секторов: {self.total_sectors}\n")
            f.write(f"Средняя скорость: {self.get_statistics()['avg_speed']:.1f} MB/s\n")
            f.write(f"Макс скорость: {self.get_statistics()['max_speed']:.1f} MB/s\n")
            f.write(f"Мин скорость: {self.get_statistics()['min_speed']:.1f} MB/s\n")
            f.write(f"Битых секторов: {len(self.bad_sectors)}\n")
            f.write(f"Время теста: {self.get_statistics()['elapsed_time']}\n")
            
            if self.bad_sectors:
                f.write(f"\nСписок битых секторов (первые 100):\n")
                for sector in self.bad_sectors[:100]:
                    f.write(f"  {sector}\n")
        return True
    
    def _export_html_report(self, filepath):
        """Экспорт в HTML"""
        stats = self.get_statistics()
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SD Card Tester Pro - Отчет</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #1e1e1e; color: white; }}
        h1 {{ color: #00bcd4; }}
        h2 {{ color: #00bcd4; }}
        .stats {{ background: #2d2d2d; padding: 20px; border-radius: 5px; }}
        .bad {{ color: #f44336; }}
        .good {{ color: #4caf50; }}
        .warning {{ color: #ff9800; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #444; }}
        th {{ background-color: #00bcd4; color: white; }}
    </style>
</head>
<body>
    <h1>SD Card Tester Pro - Отчет о тестировании</h1>
    <p>Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <div class="stats">
        <h2>Статистика</h2>
        <p><b>Диск:</b> {self.current_drive}</p>
        <p><b>Режим доступа:</b> {'Прямой' if self.write_mode == 'direct' else 'Через файл'}</p>
        <p><b>Проходов:</b> {self.current_pass}/{self.total_passes}</p>
        <p><b>Размер:</b> {self.total_size:.1f} GB</p>
        <p><b>Всего секторов:</b> {self.total_sectors}</p>
        <p><b>Средняя скорость:</b> {stats['avg_speed']:.1f} MB/s</p>
        <p><b>Макс скорость:</b> {stats['max_speed']:.1f} MB/s</p>
        <p><b>Мин скорость:</b> {stats['min_speed']:.1f} MB/s</p>
        <p><b>Битых секторов:</b> <span class="{'bad' if len(self.bad_sectors) > 0 else 'good'}">{len(self.bad_sectors)}</span></p>
        <p><b>Время теста:</b> {stats['elapsed_time']}</p>
        <p><b>Статус:</b> <span class="{'bad' if len(self.bad_sectors) > 0 else 'good'}">{'⚠️ Обнаружены битые сектора' if len(self.bad_sectors) > 0 else '✅ Диск исправен'}</span></p>
    </div>"""
        
        if self.bad_sectors:
            html += """
    <h2>Битые сектора</h2>
    <table>
        <tr>
            <th>Номер сектора</th>
            <th>Смещение (байт)</th>
        </tr>"""
            for sector in self.bad_sectors[:100]:
                offset = sector * 512
                html += f"""
        <tr>
            <td>{sector}</td>
            <td>{offset}</td>
        </tr>"""
            html += """
    </table>"""
        
        html += """
</body>
</html>"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    
    def _export_json_report(self, filepath):
        """Экспорт в JSON"""
        stats = self.get_statistics()
        report = {
            'timestamp': datetime.now().isoformat(),
            'version': self.config['app']['version'],
            'drive': self.current_drive,
            'access_mode': 'direct' if self.write_mode == 'direct' else 'file',
            'total_size_gb': self.total_size,
            'total_sectors': self.total_sectors,
            'passes_completed': self.current_pass,
            'passes_total': self.total_passes,
            'avg_speed_mbs': stats['avg_speed'],
            'max_speed_mbs': stats['max_speed'],
            'min_speed_mbs': stats['min_speed'],
            'bad_sectors': len(self.bad_sectors),
            'bad_sectors_list': self.bad_sectors[:100],
            'elapsed_time': stats['elapsed_time']
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return True
    
    # ========== СИСТЕМА СОБЫТИЙ ==========
    
    def register_callback(self, event_type, callback):
        """Регистрация коллбека для определенного типа событий"""
        if event_type not in self.ui_callbacks:
            self.ui_callbacks[event_type] = []
        self.ui_callbacks[event_type].append(callback)
    
    def _emit(self, event_type, *args, **kwargs):
        """Отправка события в UI"""
        # Добавляем в очередь
        if event_type == 'log':
            self.message_queue.put(('log', args[0], args[1] if len(args) > 1 else 'info'))
        elif event_type == 'speed':
            self.message_queue.put(('speed', args[0], args[1]))
        elif event_type == 'progress':
            self.message_queue.put(('progress', args[0]))
        elif event_type == 'progress_detail':
            self.message_queue.put(('progress_detail', args[0]))
        elif event_type == 'bad_sector':
            self.message_queue.put(('bad_sector', args[0], args[1], args[2]))
        elif event_type == 'complete':
            self.message_queue.put(('complete', args[0]))
        elif event_type == 'error':
            self.message_queue.put(('error', args[0]))
        
        # Вызываем коллбеки
        if event_type in self.ui_callbacks:
            for callback in self.ui_callbacks[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self.logger.log_error(f"Ошибка в коллбеке {event_type}: {e}")
    
    def get_message(self):
        """Получение сообщения из очереди (для UI)"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None