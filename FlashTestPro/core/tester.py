"""
Модуль тестирования дисков
Поддерживает два режима:
- free: тестирование только свободного места (через временный файл)
- full: полное тестирование всех секторов (прямой доступ к устройству) с защитой системных областей
"""
import os
import time
import random
import threading
import queue
import platform
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from utils.logger import get_logger

if platform.system() == "Windows":
    import wmi

class DiskTester:
    """Класс для тестирования дисков"""

    # Максимальное количество битых секторов, после которого тест останавливается
    MAX_BAD_SECTORS = 100

    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.system = platform.system()

        self.test_thread = None
        self.running = False
        self.paused = False
        self.stop_requested = False

        self.message_queue = queue.Queue(maxsize=100)

        self.stats = self._init_stats()
        self.test_params = {}
        self.drive_path = ""

        self.last_update_time = 0
        self.update_interval = 0.1

        self.test_handle = None
        self.device_path = None

        self.unmounted = False

        # Интервалы для системных областей и данных
        self.system_intervals: List[Tuple[int, int]] = []
        self.data_intervals: List[Tuple[int, int]] = []

    def _init_stats(self) -> Dict:
        return {
            'total_size': 0,
            'total_bytes': 0,
            'tested': 0,
            'tested_bytes': 0,
            'avg_speed': 0,
            'max_speed': 0,
            'min_speed': float('inf'),
            'speeds': [],
            'times': [],
            'start_time': None,
            'elapsed_time': "00:00:00",
            'elapsed_seconds': 0,
            'bad_sectors': [],
            'bad_sectors_count': 0,
            'system_bad_sectors': 0,
            'system_bad_sectors_list': [],
            'current_pass': 0,
            'total_passes': 1,
            'test_paused': False,
            'drive_path': '',
            'mode': 'free',
            'status': 'idle'
        }

    def _get_device_path_windows(self, drive_path):
        try:
            c = wmi.WMI()
            drive_letter = drive_path[0].upper()
            for logical_disk in c.Win32_LogicalDisk(DeviceID=f"{drive_letter}:"):
                for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                    for disk_drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                        return r"\\.\PhysicalDrive" + str(disk_drive.Index)
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства: {e}")
        return None

    def _get_device_path_linux(self, mountpoint):
        try:
            with open('/proc/mounts') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) > 1 and parts[1] == mountpoint:
                        dev = parts[0]
                        base = ''.join(c for c in dev if not c.isdigit())
                        return base
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства: {e}")
        return None

    def _get_device_path(self, drive_path):
        if self.system == "Windows":
            return self._get_device_path_windows(drive_path)
        elif self.system == "Linux":
            return self._get_device_path_linux(drive_path)
        elif self.system == "Darwin":
            self.logger.warning("macOS: полное тестирование не реализовано, используйте free режим")
            return None
        return None

    def _unmount_drive(self, drive_path):
        """Размонтирует том, чтобы освободить диск для прямого доступа (только Windows)."""
        if self.system != "Windows":
            return
        try:
            import win32file
            import win32con
            drive_letter = drive_path[0]
            handle = win32file.CreateFile(
                f"\\\\.\\{drive_letter}:",
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                0,
                None
            )
            if handle and handle != win32file.INVALID_HANDLE_VALUE:
                # Пытаемся размонтировать
                win32file.DeviceIoControl(handle, win32con.FSCTL_DISMOUNT_VOLUME, None, None)
                win32file.CloseHandle(handle)
                self.logger.info(f"Том {drive_letter}: успешно размонтирован")
                self._send_message('log', f"Том {drive_letter} размонтирован для прямого доступа к диску", 'info')
                self.unmounted = True
            else:
                self.logger.warning(f"Не удалось открыть том {drive_letter} для размонтирования")
        except Exception as e:
            self.logger.warning(f"Ошибка при размонтировании тома {drive_path}: {e}")
            self._send_message('log', f"Не удалось размонтировать том {drive_path} (возможно, уже размонтирован)", 'warning')

    def start_test(self, drive_path: str, params: Dict):
        """Запуск тестирования"""
        if self.running:
            return

        self.drive_path = drive_path
        self.test_params = params
        self.running = True
        self.stop_requested = False
        self.paused = False

        self.stats = self._init_stats()
        self.stats['total_passes'] = params.get('passes', 1)
        self.stats['drive_path'] = drive_path
        self.stats['mode'] = params.get('mode', 'free')

        drive_info = None
        for drive in self.app.drive_manager.get_drives_list():
            if drive['path'] == drive_path:
                drive_info = drive
                break

        if not drive_info:
            self._send_message('error', "Не удалось получить информацию о диске")
            self.running = False
            return

        # Определяем размер теста
        if self.stats['mode'] == 'full':
            self.stats['total_bytes'] = drive_info['total_bytes']
            self.logger.info(f"Полный режим: размер диска {self.stats['total_bytes'] / (1024**3):.2f} GB")
            # Получаем путь к устройству в главном потоке
            self.device_path = self._get_device_path(drive_path)
            if not self.device_path:
                self._send_message('error', "Не удалось определить путь к физическому устройству")
                self.running = False
                return
            # Размонтируем том перед открытием устройства
            self._unmount_drive(drive_path)
        else:
            free_bytes = drive_info['free_bytes']
            if free_bytes <= 0:
                self._send_message('error', "На диске нет свободного места для теста")
                self.running = False
                return
            # Тестируем 10% свободного места, но не более 10 GB и не менее 1 MB
            test_size = int(free_bytes * 0.1)
            max_test = 10 * 1024 * 1024 * 1024  # 10 GB
            min_test = 1 * 1024 * 1024          # 1 MB
            test_size = min(test_size, max_test)
            if test_size < min_test:
                self._send_message('error', f"Недостаточно свободного места для теста (нужно минимум {min_test // (1024**2)} MB)")
                self.running = False
                return
            self.stats['total_bytes'] = test_size
            self.logger.info(f"Свободный режим: размер теста {self.stats['total_bytes'] / (1024**2):.2f} MB")
            self.device_path = None

        self.stats['total_size'] = self.stats['total_bytes'] / (1024**3)

        self.test_thread = threading.Thread(target=self._test_worker, daemon=True)
        self.test_thread.start()

        self.logger.info(f"Тестирование запущено для диска {drive_path} в режиме {self.stats['mode']}")

    def _test_worker(self):
        """Рабочий поток тестирования"""
        self.stats['start_time'] = time.time()
        self.last_update_time = time.time()

        try:
            if self.stats['mode'] == 'full':
                device_path = self.device_path
                if not device_path:
                    raise Exception("Не удалось определить путь к физическому устройству")
                self.logger.info(f"Открытие устройства: {device_path}")
                # Формируем флаги в зависимости от ОС
                flags = os.O_RDWR
                if hasattr(os, 'O_BINARY'):      # Windows
                    flags |= os.O_BINARY
                if self.system != "Windows" and hasattr(os, 'O_SYNC'):   # Unix
                    flags |= os.O_SYNC
                fd = os.open(device_path, flags)
                self.test_handle = os.fdopen(fd, 'rb+', buffering=0)

                # Определяем системные и рабочие интервалы
                self._build_intervals(device_path)

                # Проверяем системные интервалы (только чтение)
                for start, end in self.system_intervals:
                    self._check_system_interval(start, end)
                    if self.stop_requested:
                        break

                # Основное тестирование на интервалах данных
                for start, end in self.data_intervals:
                    self._run_test_pass_on_interval(start, end)
                    if self.stop_requested:
                        break

            else:
                test_file_path = os.path.join(self.drive_path, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tmp")
                self.logger.info(f"Создание тестового файла: {test_file_path}")
                try:
                    self.test_handle = open(test_file_path, 'wb+', buffering=-1)
                except Exception as e:
                    self.logger.warning(f"Не удалось открыть с buffering=-1: {e}, пробуем buffering=0")
                    self.test_handle = open(test_file_path, 'wb+', buffering=0)

                # В свободном режиме тестируем весь файл как один интервал
                self.data_intervals = [(0, self.stats['total_bytes'])]
                self.system_intervals = []
                self._run_test_pass_on_interval(0, self.stats['total_bytes'])

            self._test_complete()

        except Exception as e:
            self.logger.error(f"Ошибка в потоке тестирования: {e}", exc_info=True)
            self._send_message('error', str(e))
        finally:
            if self.device_handle:
                try:
                    self.device_handle.close()
                except:
                    pass
            if self.unmounted:   # теперь переменная определена
                self._send_message('unmount_notice', self.drive_path)
            self.running = False
            self.device_handle = None

    def _build_intervals(self, device_path):
        """Построение интервалов системных областей и данных на основе разделов диска"""
        total = self.stats['total_bytes']
        partitions = self.app.drive_manager.get_partition_offsets(device_path)
        if partitions:
            partitions.sort(key=lambda x: x[0])
            self.system_intervals = []
            self.data_intervals = []

            # Область до первого раздела
            if partitions[0][0] > 0:
                self.system_intervals.append((0, partitions[0][0]))

            # Между разделами
            for i in range(len(partitions) - 1):
                end_prev = partitions[i][1]
                start_next = partitions[i+1][0]
                if end_prev < start_next:
                    self.system_intervals.append((end_prev, start_next))

            # Область после последнего раздела
            if partitions[-1][1] < total:
                self.system_intervals.append((partitions[-1][1], total))

            # Интервалы данных — сами разделы
            self.data_intervals = partitions
        else:
            # Разделов нет — всё считается данными
            self.data_intervals = [(0, total)]
            self.system_intervals = []

    def _check_system_interval(self, start: int, end: int):
        """Проверка системного интервала только чтением, без записи"""
        chunk_size = self.app.config.get('testing', {}).get('chunk_size_mb', 64) * 1024 * 1024
        offset = start
        while offset < end and not self.stop_requested:
            current_chunk = min(chunk_size, end - offset)
            try:
                self.test_handle.seek(offset)
                data = self.test_handle.read(current_chunk)
                # чтение успешно
            except OSError as e:
                sector = offset // 512
                self._add_bad_sector(sector, str(e), system=True)
                # Критическая ошибка дескриптора
                if e.errno == 9:  # Bad file descriptor
                    self._send_message('error',
                        "Критическая ошибка: диск не доступен для чтения.\n"
                        "Тест прерван.")
                    self.stop_requested = True
                    break
            except Exception as e:
                sector = offset // 512
                self._add_bad_sector(sector, str(e), system=True)

            offset += current_chunk
            # Обновляем прогресс
            self.stats['tested_bytes'] += current_chunk
            self.stats['tested'] = self.stats['tested_bytes'] / (1024**3)
            progress = (self.stats['tested_bytes'] / self.stats['total_bytes']) * 100
            self._send_message('progress', progress)
            self.last_update_time = time.time()

    def _run_test_pass_on_interval(self, start: int, end: int):
        """Выполнение одного прохода теста с записью/чтением в заданном интервале"""
        patterns = []

        if self.test_params.get('test_ones', False):
            patterns.append(('ones', b'\xFF'))
        if self.test_params.get('test_zeros', False):
            patterns.append(('zeros', b'\x00'))
        if self.test_params.get('test_random', False):
            patterns.append(('random', None))

        if not patterns:
            patterns = [('random', None)]

        chunk_size = self.app.config.get('testing', {}).get('chunk_size_mb', 64) * 1024 * 1024
        interval_bytes = end - start
        total_chunks = max(1, interval_bytes // chunk_size)

        for pattern_name, pattern_value in patterns:
            if self.stop_requested:
                break

            while self.paused and not self.stop_requested:
                time.sleep(0.1)

            self._send_message('log', f"Паттерн: {pattern_name}", 'info')

            if pattern_name == 'ones':
                data = pattern_value * chunk_size
            elif pattern_name == 'zeros':
                data = pattern_value * chunk_size
            else:
                data = os.urandom(chunk_size)

            for chunk_num in range(total_chunks):
                if self.stop_requested:
                    break

                while self.paused and not self.stop_requested:
                    time.sleep(0.1)

                offset = start + chunk_num * chunk_size
                current_chunk = min(chunk_size, end - offset)

                start_time = time.time()
                try:
                    self.test_handle.seek(offset)
                    self.test_handle.write(data[:current_chunk])
                    self.test_handle.flush()
                    if hasattr(os, 'fdatasync'):
                        os.fdatasync(self.test_handle.fileno())
                    else:
                        os.fsync(self.test_handle.fileno())

                    if self.test_params.get('test_verify', True):
                        self.test_handle.seek(offset)
                        read_data = self.test_handle.read(current_chunk)
                        if read_data != data[:current_chunk]:
                            raise Exception("Ошибка верификации данных")

                except OSError as e:
                    if e.errno == 9:  # Bad file descriptor
                        self._send_message('error',
                            "Критическая ошибка: диск не доступен для записи.\n"
                            "Возможные причины:\n"
                            "• Диск защищён от записи\n"
                            "• Недостаточно прав (запустите программу от администратора)\n"
                            "• Диск является CD/DVD-ROM или другим устройством только для чтения\n"
                            "Тест прерван.")
                        self.stop_requested = True
                        break
                    else:
                        sector = offset // 512
                        self._add_bad_sector(sector, str(e), system=False)
                        continue
                except Exception as e:
                    sector = offset // 512
                    self._add_bad_sector(sector, str(e), system=False)
                    continue

                elapsed = time.time() - start_time
                speed = (current_chunk / 1024 / 1024) / max(elapsed, 0.001)

                self.stats['tested_bytes'] += current_chunk
                self.stats['tested'] = self.stats['tested_bytes'] / (1024**3)

                self.stats['speeds'].append(speed)
                if self.stats['speeds']:
                    self.stats['avg_speed'] = sum(self.stats['speeds']) / len(self.stats['speeds'])

                if speed > self.stats['max_speed']:
                    self.stats['max_speed'] = speed
                if speed < self.stats['min_speed']:
                    self.stats['min_speed'] = speed

                self.stats['elapsed_seconds'] = time.time() - self.stats['start_time']
                hours = int(self.stats['elapsed_seconds'] // 3600)
                minutes = int((self.stats['elapsed_seconds'] % 3600) // 60)
                seconds = int(self.stats['elapsed_seconds'] % 60)
                self.stats['elapsed_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                self.stats['times'].append(self.stats['elapsed_seconds'])

                current_time = time.time()
                if current_time - self.last_update_time >= self.update_interval or chunk_num == total_chunks - 1:
                    progress = (self.stats['tested_bytes'] / self.stats['total_bytes']) * 100
                    self._send_message('progress', progress)
                    self._send_message('speed', speed, self.stats['elapsed_seconds'])
                    self.last_update_time = current_time

    def _add_bad_sector(self, sector: int, error_type: str, system: bool = False):
        bad_sector = {
            'sector': sector,
            'error_type': error_type,
            'time': datetime.now().strftime("%H:%M:%S"),
            'attempts': 1,
            'system': system
        }
        if system:
            self.stats['system_bad_sectors_list'].append(bad_sector)
            self.stats['system_bad_sectors'] = len(self.stats['system_bad_sectors_list'])
            self._send_message('log', f"Найден битый системный сектор: {sector} - {error_type}", 'error')
        else:
            self.stats['bad_sectors'].append(bad_sector)
            self.stats['bad_sectors_count'] = len(self.stats['bad_sectors'])
            self._send_message('bad_sector', sector, error_type, 1)
            self._send_message('log', f"Найден битый сектор: {sector} - {error_type}", 'error')

        # Если общее количество битых секторов превысило лимит, останавливаем тест
        total_bad = self.stats['bad_sectors_count'] + self.stats['system_bad_sectors']
        if total_bad >= self.MAX_BAD_SECTORS:
            self._send_message('log', f"Превышен лимит битых секторов ({self.MAX_BAD_SECTORS}). Тест остановлен.", 'error')
            self.stop_requested = True

    def _test_complete(self):
        elapsed = self.stats['elapsed_time']

        if self.stop_requested:
            self._send_message('log', "Тест остановлен пользователем или из-за ошибки", 'warning')
            self._send_message('complete', "Тестирование прервано")
        else:
            self._send_message('log', f"Тестирование завершено за {elapsed}", 'success')
            self._send_message('complete', "Тестирование успешно завершено")

        self.logger.info(f"Тестирование завершено. Битых секторов: {self.stats['bad_sectors_count']}, системных битых: {self.stats['system_bad_sectors']}")

        if self.unmounted:
            self._send_message('unmount_notice', self.drive_path)

    def _send_message(self, msg_type: str, *args):
        try:
            self.message_queue.put_nowait((msg_type,) + args)
        except queue.Full:
            pass

    def get_message(self):
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    def pause(self):
        if self.running and not self.stop_requested:
            self.paused = not self.paused
            self.stats['test_paused'] = self.paused
            status = "приостановлен" if self.paused else "продолжен"
            self._send_message('log', f"Тест {status}", 'info')
            return self.paused
        return None

    def stop(self):
        if self.running:
            self.stop_requested = True
            self._send_message('log', "Запрошена остановка теста...", 'warning')

    def is_running(self) -> bool:
        return self.running

    def get_statistics(self) -> Dict:
        return self.stats.copy()