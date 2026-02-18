"""
Модуль безопасного затирания данных.
Поддерживает методы: simple, DoD 5220.22-M, Gutmann.
Реальная запись на устройство с возможностью верификации.
"""
import os
import time
import random
import threading
import queue
import platform
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger

# Для работы с WMI на Windows
if platform.system() == "Windows":
    import wmi

class DataWiper:
    """Класс для безопасного затирания данных на диске"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.system = platform.system()

        self.wipe_thread = None
        self.running = False
        self.stop_requested = False

        self.message_queue = queue.Queue(maxsize=100)

        # Параметры затирания
        self.drive_path = ""
        self.method = ""
        self.passes = 0
        self.verify = False
        self.device_handle = None

        # Статистика
        self.stats = {
            'total_bytes': 0,
            'total_size_gb': 0,
            'current_pass': 0,
            'bad_sectors': 0,
            'errors': []
        }

    def _get_device_path_windows(self, drive_path: str) -> Optional[str]:
        """Определение пути к физическому диску для Windows"""
        try:
            import wmi
            c = wmi.WMI()
            drive_letter = drive_path[0].upper()
            for logical_disk in c.Win32_LogicalDisk(DeviceID=f"{drive_letter}:"):
                for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                    for disk_drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                        return r"\\.\PhysicalDrive" + str(disk_drive.Index)
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства (Windows): {e}")
        return None

    def _get_device_path_linux(self, mountpoint: str) -> Optional[str]:
        """Определение пути к физическому диску для Linux"""
        try:
            # Получаем базовое устройство из /proc/mounts
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
        """Определение пути к физическому диску для macOS"""
        try:
            import subprocess
            # diskutil info /Volumes/NAME | grep "Device Node"
            result = subprocess.run(
                ['diskutil', 'info', mountpoint],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'Device Node:' in line:
                    node = line.split(':', 1)[1].strip()
                    # Преобразуем /dev/disk2s1 -> /dev/rdisk2 для сырого доступа
                    base = node.split('s')[0]  # отрезаем номер раздела
                    raw = base.replace('/dev/disk', '/dev/rdisk')
                    return raw
        except Exception as e:
            self.logger.error(f"Ошибка получения пути устройства (macOS): {e}")
        return None

    def _get_device_path(self, drive_path: str) -> Optional[str]:
        """Обёртка для получения пути к устройству в зависимости от ОС"""
        if self.system == "Windows":
            return self._get_device_path_windows(drive_path)
        elif self.system == "Linux":
            return self._get_device_path_linux(drive_path)
        elif self.system == "Darwin":  # macOS
            return self._get_device_path_macos(drive_path)
        else:
            self.logger.error(f"Неподдерживаемая ОС: {self.system}")
            return None

    def _get_device_size(self, device_path: str) -> int:
        """Получение размера устройства в байтах"""
        try:
            if self.system == "Windows":
                # Для Windows используем GetDiskFreeSpaceEx на томе, но для физического диска сложнее
                # Временно используем размер, полученный из DriveManager
                for drive in self.app.drive_manager.get_drives_list():
                    if drive['path'] == self.drive_path:
                        return drive['total_bytes']
                return 0
            else:
                # Для Linux/macOS используем os.lseek
                fd = os.open(device_path, os.O_RDONLY)
                size = os.lseek(fd, 0, os.SEEK_END)
                os.close(fd)
                return size
        except Exception as e:
            self.logger.error(f"Не удалось определить размер устройства: {e}")
            return 0

    def wipe_disk(self, drive_path: str, method: str = "dod", passes: int = 3, verify: bool = True) -> bool:
        """Запуск затирания диска"""
        if self.running:
            self.logger.warning("Затирание уже выполняется")
            return False

        self.drive_path = drive_path
        self.method = method
        self.passes = passes
        self.verify = verify
        self.stop_requested = False
        self.stats = {
            'total_bytes': 0,
            'total_size_gb': 0,
            'current_pass': 0,
            'bad_sectors': 0,
            'errors': []
        }

        self.wipe_thread = threading.Thread(target=self._wipe_worker, daemon=True)
        self.wipe_thread.start()
        self.logger.info(f"Затирание запущено для диска {drive_path} методом {method}")
        return True

    def _wipe_worker(self):
        """Рабочий поток затирания"""
        self.running = True

        try:
            # 1. Получаем путь к устройству
            device_path = self._get_device_path(self.drive_path)
            if not device_path:
                raise Exception("Не удалось определить путь к физическому устройству")

            # 2. Получаем размер устройства
            total_bytes = self._get_device_size(device_path)
            if total_bytes == 0:
                raise Exception("Не удалось определить размер устройства")
            self.stats['total_bytes'] = total_bytes
            self.stats['total_size_gb'] = total_bytes / (1024**3)

            self._send_message('log', f"Устройство: {device_path}, размер: {self.stats['total_size_gb']:.2f} GB", 'info')

            # 3. Открываем устройство для записи
            #   На Windows открываем с флагами GENERIC_READ | GENERIC_WRITE, но через os.open сложно
            #   Используем стандартное открытие файла с os.O_RDWR | os.O_BINARY | os.O_SYNC
            flags = os.O_RDWR | os.O_BINARY if hasattr(os, 'O_BINARY') else os.O_RDWR
            if self.system != "Windows":
                flags |= os.O_SYNC

            fd = os.open(device_path, flags)
            self.device_handle = os.fdopen(fd, 'rb+', buffering=0)

            # 4. Определяем количество проходов и паттерны
            passes_to_do, patterns = self._get_patterns_for_method(self.method, self.passes)

            # 5. Выполняем проходы
            for pass_num in range(1, passes_to_do + 1):
                if self.stop_requested:
                    break

                self.stats['current_pass'] = pass_num
                pattern = patterns[pass_num - 1]
                self._send_message('log', f"Проход {pass_num}/{passes_to_do} - паттерн: {pattern:02X}", 'info')

                # Запись паттерна по всему диску
                self._write_pattern(pattern)

                # Если запрошена остановка, выходим
                if self.stop_requested:
                    break

            # 6. Верификация (если включена и не было остановки)
            if self.verify and not self.stop_requested and patterns:
                self._send_message('log', "Начало верификации...", 'info')
                last_pattern = patterns[-1]
                self._verify_pattern(last_pattern)

            # 7. Завершение
            if self.stop_requested:
                self._send_message('log', "Затирание прервано пользователем", 'warning')
                self._send_message('complete', "Затирание прервано")
            else:
                self._send_message('log', "Затирание успешно завершено", 'success')
                self._send_message('complete', "Затирание завершено")

        except Exception as e:
            self.logger.error(f"Ошибка при затирании: {e}", exc_info=True)
            self._send_message('error', str(e))
        finally:
            if self.device_handle:
                try:
                    self.device_handle.close()
                except:
                    pass
            self.running = False
            self.device_handle = None

    def _get_patterns_for_method(self, method: str, passes: int) -> Tuple[int, List[int]]:
        """Возвращает количество проходов и список байтовых паттернов для метода"""
        if method == "simple":
            return 1, [0x00]
        elif method == "dod":
            # DoD 5220.22-M: 1-й проход - любой символ, 2-й - его дополнение, 3-й - случайный
            # Упрощённо: 0x00, 0xFF, случайный
            random_byte = random.randint(0, 255)
            return 3, [0x00, 0xFF, random_byte]
        elif method == "gutmann":
            patterns = self._get_gutmann_patterns()
            return len(patterns), patterns
        else:
            # Пользовательский метод: просто повторяем случайные паттерны
            patterns = [random.randint(0, 255) for _ in range(passes)]
            return passes, patterns

    def _get_gutmann_patterns(self) -> List[int]:
        """Получение 35 паттернов Гутманна"""
        patterns = []

        # Первые 4 прохода: случайные данные
        for _ in range(4):
            patterns.append(random.randint(0, 255))

        # Специальные паттерны (27 проходов)
        specials = [0x55, 0xAA, 0x92, 0x49, 0x24, 0x12, 0x09, 0x04,
                    0x02, 0x01, 0x80, 0x40, 0x20, 0x10, 0x08]
        # Повторяем, чтобы получить 27
        for _ in range(2):
            patterns.extend(specials)
        # Обрезаем до 27 (если overshoot)
        patterns = patterns[:31]  # 4 + 27 = 31? На самом деле 4 + 27*? В классическом Gutmann 35 проходов:
        # 4 случайных, затем 27 специальных (повторяются 3 раза?), затем 4 случайных.
        # Для простоты реализуем стандартную последовательность:
        # Gutmann: проходы 1-4: случайные; 5-31: специальные (повтор набора); 32-35: случайные.
        # Итого 4 + 27 + 4 = 35.
        # В специальных 15 паттернов, нужно повторить их 27 раз? Нет, обычно они идут по порядку,
        # затем повторяются, всего 27 проходов = 15 + 12 (повтор первых 12). Реализуем упрощённо:
        # Создадим список из 35 элементов.
        # Очистим и пересоберём:
        patterns = []
        # 4 случайных
        for _ in range(4):
            patterns.append(random.randint(0, 255))
        # 27 специальных (повторяем список specials пока не наберём 27)
        specials = [0x55, 0xAA, 0x92, 0x49, 0x24, 0x12, 0x09, 0x04,
                    0x02, 0x01, 0x80, 0x40, 0x20, 0x10, 0x08]
        while len(patterns) < 31:  # 4 + 27 = 31? Подожди, 4+27=31, но нужно 35, значит потом ещё 4 = 35.
            patterns.extend(specials)
        patterns = patterns[:31]  # обрезаем до 31 (первые 4 + 27)
        # Добавляем ещё 4 случайных в конец
        for _ in range(4):
            patterns.append(random.randint(0, 255))
        return patterns[:35]  # гарантируем 35

    def _write_pattern(self, pattern: int):
        """Запись одного байтового паттерна на весь диск блоками"""
        chunk_size = 64 * 1024 * 1024  # 64 MB
        data = bytes([pattern]) * chunk_size
        total_chunks = (self.stats['total_bytes'] + chunk_size - 1) // chunk_size

        for chunk_num in range(total_chunks):
            if self.stop_requested:
                break

            offset = chunk_num * chunk_size
            # Последний блок может быть меньше
            current_chunk_size = min(chunk_size, self.stats['total_bytes'] - offset)
            if current_chunk_size <= 0:
                break

            try:
                self.device_handle.seek(offset)
                self.device_handle.write(data[:current_chunk_size])
                self.device_handle.flush()
                if hasattr(os, 'fdatasync'):
                    os.fdatasync(self.device_handle.fileno())
                else:
                    os.fsync(self.device_handle.fileno())
            except OSError as e:
                # Ошибка ввода/вывода – возможно, битый сектор
                self.stats['bad_sectors'] += 1
                self.stats['errors'].append({
                    'offset': offset,
                    'error': str(e)
                })
                self._send_message('log', f"Ошибка записи в секторе {offset//512}: {e}", 'error')

            # Прогресс в рамках прохода
            progress = ((chunk_num + 1) / total_chunks) * 100
            self._send_message('progress', progress)

    def _verify_pattern(self, pattern: int):
        """Верификация последнего записанного паттерна чтением и сравнением"""
        chunk_size = 64 * 1024 * 1024
        data_expected = bytes([pattern]) * chunk_size
        total_chunks = (self.stats['total_bytes'] + chunk_size - 1) // chunk_size

        errors = 0
        for chunk_num in range(total_chunks):
            if self.stop_requested:
                break

            offset = chunk_num * chunk_size
            current_chunk_size = min(chunk_size, self.stats['total_bytes'] - offset)

            try:
                self.device_handle.seek(offset)
                read_data = self.device_handle.read(current_chunk_size)
                if read_data != data_expected[:current_chunk_size]:
                    # Несовпадение данных
                    errors += 1
                    self._send_message('log', f"Ошибка верификации в секторе {offset//512}", 'error')
            except OSError as e:
                errors += 1
                self._send_message('log', f"Ошибка чтения в секторе {offset//512}: {e}", 'error')

            # Можно отправлять прогресс верификации, но для простоты не будем

        if errors == 0:
            self._send_message('log', "Верификация пройдена успешно", 'success')
        else:
            self._send_message('log', f"Верификация завершена с {errors} ошибками", 'warning')

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
        """Остановка затирания"""
        if self.running:
            self.stop_requested = True
            self._send_message('log', "Запрошена остановка...", 'warning')

    def is_running(self) -> bool:
        """Проверка, выполняется ли затирание"""
        return self.running

    def get_statistics(self) -> Dict:
        """Получение статистики"""
        return self.stats.copy()