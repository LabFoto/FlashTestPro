"""
Модуль для проверки реальной ёмкости накопителя (выявление поддельных карт памяти).
Использует прямой доступ к устройству и бинарный поиск.
"""
import os
import time
import threading
import queue
import platform
from typing import Optional, Dict

from utils.logger import get_logger

# Для Windows
if platform.system() == "Windows":
    import win32file
    import win32con

class CapacityTester:
    """Класс для определения реального объёма накопителя"""

    # Константа для размонтирования тома (если отсутствует в win32file)
    FSCTL_DISMOUNT_VOLUME = getattr(win32file, 'FSCTL_DISMOUNT_VOLUME', 0x00090020) if platform.system() == "Windows" else None

    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.system = platform.system()

        self.test_thread = None
        self.running = False
        self.stop_requested = False
        self.message_queue = queue.Queue(maxsize=100)

        self.drive_path = ""
        self.device_path = None
        self.device_handle = None
        self.unmounted = False

        # Параметры теста
        self.marker = b"FLASHTESTPRO_MARKER"  # уникальный маркер (20 байт)
        self.marker_size = len(self.marker)
        self.chunk_size = 64 * 1024 * 1024  # 64 MB для записи

    def _get_device_path(self, drive_path: str) -> Optional[str]:
        """Определение пути к физическому устройству"""
        if self.system == "Windows":
            return self._get_device_path_windows(drive_path)
        elif self.system == "Linux":
            return self._get_device_path_linux(drive_path)
        elif self.system == "Darwin":
            return self._get_device_path_macos(drive_path)
        else:
            self.logger.error(f"Неподдерживаемая ОС: {self.system}")
            return None

    def _get_device_path_windows(self, drive_path: str) -> Optional[str]:
        """Windows: преобразует букву диска в \\.\PhysicalDriveN"""
        try:
            import wmi
            c = wmi.WMI()
            drive_letter = drive_path[0].upper()
            for logical_disk in c.Win32_LogicalDisk(DeviceID=f"{drive_letter}:"):
                for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                    for disk_drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                        return r"\\.\PhysicalDrive" + str(disk_drive.Index)
        except Exception as e:
            self.logger.debug(f"Определение пути для {drive_path}")
            self.logger.error(f"Ошибка получения пути устройства (Windows): {e}")
        return None

    def _get_device_path_linux(self, mountpoint: str) -> Optional[str]:
        """Linux: получает базовое устройство (например, /dev/sda) из /proc/mounts"""
        try:
            with open('/proc/mounts') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) > 1 and parts[1] == mountpoint:
                        dev = parts[0]
                        # Убираем цифры в конце (номер раздела)
                        base = ''.join(c for c in dev if not c.isdigit())
                        return base
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства (Linux): {e}")
        return None

    def _get_device_path_macos(self, mountpoint: str) -> Optional[str]:
        """macOS: получает raw-устройство через diskutil"""
        try:
            import subprocess
            result = subprocess.run(
                ['diskutil', 'info', mountpoint],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'Device Node:' in line:
                    node = line.split(':', 1)[1].strip()
                    base = node.split('s')[0]  # убираем номер раздела
                    raw = base.replace('/dev/disk', '/dev/rdisk')
                    return raw
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства (macOS): {e}")
        return None

    def _unmount_drive(self, drive_path: str) -> bool:
        """
        Размонтирует том в Windows.
        Возвращает True, если том успешно размонтирован или уже недоступен.
        """
        if self.system != "Windows":
            return True

        try:
            import win32file
            import win32con
            import time

            drive_letter = drive_path[0].upper()
            volume_path = f"\\\\.\\{drive_letter}:"
            self.logger.info(f"Попытка размонтирования тома {volume_path}")

            # Пытаемся открыть том
            handle = win32file.CreateFile(
                volume_path,
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                0,
                None
            )

            if handle == win32file.INVALID_HANDLE_VALUE:
                # Если не удалось открыть — возможно, том уже размонтирован
                self.logger.warning(f"Не удалось открыть том {volume_path} (вероятно, уже размонтирован)")
                return True  # считаем, что он размонтирован

            FSCTL_DISMOUNT_VOLUME = 0x00090020
            success = False
            try:
                # Пытаемся размонтировать
                result = win32file.DeviceIoControl(handle, FSCTL_DISMOUNT_VOLUME, None, None)
                if result:
                    self.logger.info(f"Том {drive_letter}: успешно размонтирован")
                    success = True
                else:
                    self.logger.error(f"DeviceIoControl вернул False, том {drive_letter} не размонтирован")
            except Exception as e:
                self.logger.error(f"Исключение при размонтировании: {e}")
            finally:
                win32file.CloseHandle(handle)

            if not success:
                return False

            # Ждём, чтобы система освободила ресурсы
            time.sleep(1)

            # Проверяем, действительно ли том стал недоступен
            try:
                test_handle = win32file.CreateFile(
                    volume_path,
                    win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                if test_handle != win32file.INVALID_HANDLE_VALUE:
                    win32file.CloseHandle(test_handle)
                    self.logger.warning("Том всё ещё доступен после размонтирования")
                    return False
            except:
                pass  # Если не удалось открыть — отлично

            self.logger.info("Том успешно размонтирован и недоступен")
            self.unmounted = True
            return True

        except Exception as e:
            self.logger.error(f"Ошибка в _unmount_drive: {e}")
            return False

    def _get_drive_size(self) -> int:
        """Получает размер устройства в байтах"""
        try:
            if self.system == "Windows" and self.device_handle:
                # Для Windows можно использовать GetFileSizeEx через win32file,
                # но проще взять из информации о диске
                for drive in self.app.drive_manager.get_drives_list():
                    if drive['path'] == self.drive_path:
                        return drive['total_bytes']
            else:
                # Для Linux/macOS
                current = self.device_handle.tell()
                self.device_handle.seek(0, os.SEEK_END)
                size = self.device_handle.tell()
                self.device_handle.seek(current)
                return size
        except Exception as e:
            self.logger.error(f"Не удалось определить размер устройства: {e}")
        return 0

    def start_test(self, drive_path: str):
        if self.running:
            self.logger.warning("Тест уже выполняется")
            return

        self.drive_path = drive_path
        self.stop_requested = False
        self.unmounted = False

        self.device_path = self._get_device_path(drive_path)
        if not self.device_path:
            self._send_message('error', "Не удалось определить путь к физическому устройству")
            return

        if not self._unmount_drive(drive_path):
            self._send_message('error',
                               "Не удалось размонтировать диск. Закройте все программы, использующие диск, "
                               "и убедитесь, что диск не является системным.")
            return

        self.test_thread = threading.Thread(target=self._test_worker, daemon=True)
        self.test_thread.start()
        self.running = True
        self._send_message('log', f"Запуск проверки ёмкости для {drive_path}", 'info')

    def _test_worker(self):
        """Рабочий поток проверки ёмкости"""
        self.device_handle = None
        try:
            # --- Открытие устройства в зависимости от ОС ---
            if self.system == "Windows":
                import win32file
                import win32con
                import msvcrt

                self.logger.info(f"Открытие устройства через Win32 API: {self.device_path}")
                handle = win32file.CreateFile(
                    self.device_path,
                    win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                if handle == win32file.INVALID_HANDLE_VALUE:
                    error_code = win32file.GetLastError()
                    raise Exception(f"Не удалось открыть устройство, ошибка Win32: {error_code}")

                # Преобразуем Win32 handle в целое число (фактический дескриптор)
                try:
                    handle_int = int(handle)
                except Exception as e:
                    win32file.CloseHandle(handle)
                    raise Exception(f"Не удалось преобразовать handle в int: {e}")

                # Преобразуем в файловый дескриптор Python
                fd = msvcrt.open_osfhandle(handle_int, os.O_RDWR | os.O_BINARY)
                self.device_handle = os.fdopen(fd, 'rb+', buffering=0)
                self.logger.info(f"Дескриптор преобразован, объект device_handle создан")

            else:
                # Linux / macOS
                flags = os.O_RDWR | os.O_SYNC
                if hasattr(os, 'O_BINARY'):
                    flags |= os.O_BINARY
                self.logger.info(f"Открытие устройства через os.open: {self.device_path}")
                fd = os.open(self.device_path, flags)
                self.device_handle = os.fdopen(fd, 'rb+', buffering=0)
                self.logger.info(f"Файловый дескриптор получен: {fd}")

            # --- Проверка чтения ---
            try:
                self.device_handle.seek(0)
                test_read = self.device_handle.read(512)
                self.logger.info(f"Чтение первого сектора успешно: {len(test_read)} байт")
            except Exception as e:
                self.logger.error(f"Не удалось прочитать первый сектор: {e}")
                raise

            # --- Проверка возможности записи ---
            try:
                # Сохраняем текущую позицию
                current_pos = self.device_handle.tell()
                # Используем безопасное смещение (1 MB от начала)
                test_offset = 1024 * 1024
                if test_offset >= self._get_drive_size():
                    test_offset = self._get_drive_size() // 2
                self.device_handle.seek(test_offset)
                test_data = b'\xAA'
                self.device_handle.write(test_data)
                self.device_handle.flush()
                if hasattr(os, 'fdatasync'):
                    os.fdatasync(self.device_handle.fileno())
                else:
                    os.fsync(self.device_handle.fileno())
                # Проверяем чтением
                self.device_handle.seek(test_offset)
                read_back = self.device_handle.read(1)
                if read_back != test_data:
                    raise Exception("Записанные данные не совпадают при проверке")
                # Восстанавливаем позицию (можно не восстанавливать, т.к. дальше будем писать маркер)
                self.device_handle.seek(current_pos)
                self.logger.info("Проверка записи успешна: диск доступен для записи")
            except Exception as e:
                self.logger.error(f"Проверка записи не удалась: {e}")
                self._send_message('error',
                                   "Диск не доступен для записи. Возможные причины:\n"
                                   "• Физический переключатель защиты от записи (Lock)\n"
                                   "• Недостаточно прав (запустите программу от администратора)\n"
                                   "• Диск всё ещё используется системой\n"
                                   "• Диск является CD/DVD-ROM или устройством только для чтения")
                self.stop_requested = True
                self.device_handle.close()
                self.device_handle = None
                self.running = False
                return

            # --- Получение размера устройства ---
            total_bytes = self._get_drive_size()
            if total_bytes == 0:
                raise Exception("Не удалось определить размер устройства")
            claimed_gb = total_bytes / (1024**3)
            self._send_message('log', f"Заявленный объём: {claimed_gb:.2f} GB", 'info')

            # --- Запись маркера в начало ---
            if not self._write_marker(0):
                raise Exception("Не удалось записать маркер в начало")

            # --- Бинарный поиск реальной ёмкости ---
            low, high = 0, total_bytes
            iterations = 0
            max_iterations = 30

            while low < high and iterations < max_iterations and not self.stop_requested:
                mid = (low + high) // 2
                mid = (mid // 512) * 512  # выравнивание по сектору

                self._send_message('progress', (iterations / max_iterations) * 100)
                self._send_message('log', f"Итерация {iterations+1}: проверка на {mid / (1024**3):.2f} GB...", 'debug')

                if not self._write_test_block(mid):
                    high = mid
                    continue

                if not self._check_marker(0):
                    # Маркер повреждён – подделка
                    high = mid
                    self._write_marker(0)  # восстанавливаем маркер
                else:
                    low = mid + 1

                iterations += 1

            real_bytes = low
            real_gb = real_bytes / (1024**3)

            result = {
                'claimed': claimed_gb,
                'real': real_gb,
                'status': '✅ Подлинный' if real_gb >= claimed_gb * 0.95 else '❌ Поддельный'
            }
            self._send_message('result', result)

            if result['status'].startswith('✅'):
                self._send_message('complete', "Проверка завершена. Накопитель подлинный.")
            else:
                self._send_message('complete', f"Проверка завершена. Реальная ёмкость: {real_gb:.2f} GB (подделка).")

        except Exception as e:
            self.logger.error(f"Ошибка в потоке проверки ёмкости: {e}", exc_info=True)
            self._send_message('error', str(e))
        finally:
            if self.device_handle:
                try:
                    self.device_handle.close()
                except:
                    pass
            if self.unmounted:
                self._send_message('unmount_notice', self.drive_path)
            self.running = False
            self.device_handle = None

    def _write_marker(self, offset: int) -> bool:
        """Записывает маркер по заданному смещению с подробным логированием"""
        try:
            self.logger.debug(f"Попытка записи маркера по смещению {offset}")
            self.device_handle.seek(offset)
            self.logger.debug("Позиционирование выполнено")
            self.device_handle.write(self.marker)
            self.logger.debug("Запись выполнена")
            self.device_handle.flush()
            self.logger.debug("Сброс буфера выполнен")
            if hasattr(os, 'fdatasync'):
                os.fdatasync(self.device_handle.fileno())
            else:
                os.fsync(self.device_handle.fileno())
            self.logger.debug("Синхронизация выполнена")
            return True
        except OSError as e:
            self.logger.error(f"OSError при записи маркера: errno={e.errno}, strerror={e.strerror}")
            return False
        except Exception as e:
            self.logger.error(f"Неизвестная ошибка при записи маркера: {e}", exc_info=True)
            return False

    def _check_marker(self, offset: int) -> bool:
        """Проверяет наличие маркера по смещению"""
        try:
            self.device_handle.seek(offset)
            data = self.device_handle.read(self.marker_size)
            return data == self.marker
        except Exception as e:
            self.logger.warning(f"Не удалось проверить маркер по смещению {offset}: {e}")
            return False

    def _write_test_block(self, offset: int) -> bool:
        """Записывает тестовый блок (64 MB) по заданному смещению"""
        try:
            # Генерируем случайный блок данных
            block = os.urandom(self.chunk_size)
            self.device_handle.seek(offset)
            self.device_handle.write(block)
            self.device_handle.flush()
            if hasattr(os, 'fdatasync'):
                os.fdatasync(self.device_handle.fileno())
            else:
                os.fsync(self.device_handle.fileno())
            return True
        except OSError as e:
            # Ошибка записи – вероятно, выход за пределы реальной ёмкости
            self.logger.debug(f"Ошибка записи блока по смещению {offset}: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Неожиданная ошибка при записи блока: {e}")
            return False

    def _send_message(self, msg_type: str, *args):
        """Отправка сообщения в очередь"""
        try:
            self.message_queue.put_nowait((msg_type,) + args)
        except queue.Full:
            pass

    def get_message(self):
        """Получение сообщения из очереди"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        """Остановка теста"""
        if self.running:
            self.stop_requested = True

    def is_running(self) -> bool:
        return self.running