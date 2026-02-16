"""
Модуль тестирования дисков
"""
import os
import time
import random
import threading
import queue
import tempfile
import string
from datetime import datetime
from typing import Dict, Optional
from utils.logger import get_logger

class DiskTester:
    """Класс для тестирования дисков"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        
        # Поток тестирования
        self.test_thread = None
        self.running = False
        self.paused = False
        self.stop_requested = False
        
        # Очередь сообщений для UI
        self.message_queue = queue.Queue(maxsize=100)
        
        # Статистика теста
        self.stats = self._init_stats()
        
        # Параметры теста
        self.test_params = {}
        self.drive_path = ""
        
        # Для оптимизации обновлений
        self.last_update_time = 0
        self.update_interval = 0.1  # Обновление UI каждые 100мс
        
        # Временный файл для тестирования
        self.test_file = None
    
    def _init_stats(self) -> Dict:
        """Инициализация статистики"""
        return {
            'total_size': 0,
            'total_bytes': 0,
            'tested': 0,
            'tested_bytes': 0,
            'avg_speed': 0,
            'max_speed': 0,
            'min_speed': float('inf'),
            'speeds': [],
            'start_time': None,
            'elapsed_time': "00:00:00",
            'elapsed_seconds': 0,
            'bad_sectors': [],
            'bad_sectors_count': 0,
            'current_pass': 0,
            'total_passes': 1,
            'test_paused': False,
            'drive_path': '',
            'status': 'idle'
        }
    
    def start_test(self, drive_path: str, params: Dict):
        """Запуск тестирования"""
        if self.running:
            return
        
        self.drive_path = drive_path
        self.test_params = params
        self.running = True
        self.stop_requested = False
        self.paused = False
        
        # Сброс статистики
        self.stats = self._init_stats()
        self.stats['total_passes'] = params.get('passes', 1)
        self.stats['drive_path'] = drive_path
        
        # Получаем размер диска
        try:
            drive_info = None
            for drive in self.app.drive_manager.get_drives_list():
                if drive['path'] == drive_path:
                    drive_info = drive
                    break
            
            if drive_info:
                # Используем 10% от свободного места для теста, но не более 10GB
                free_bytes = drive_info['free_bytes']
                test_size = min(int(free_bytes * 0.1), 10 * 1024 * 1024 * 1024)  # 10GB максимум
                self.stats['total_bytes'] = test_size
                self.stats['total_size'] = test_size / (1024**3)
                self.logger.info(f"Размер теста: {self.stats['total_size']:.2f} GB")
        except Exception as e:
            self.logger.error(f"Ошибка получения размера диска: {e}")
            self.stats['total_bytes'] = 1024 * 1024 * 1024  # 1 GB для теста
        
        # Запуск потока тестирования
        self.test_thread = threading.Thread(target=self._test_worker, daemon=True)
        self.test_thread.start()
        
        self.logger.info(f"Тестирование запущено для диска {drive_path}")
    
    def _test_worker(self):
        """Рабочий поток тестирования"""
        self.stats['start_time'] = time.time()
        self.last_update_time = time.time()
        
        try:
            for pass_num in range(1, self.stats['total_passes'] + 1):
                if self.stop_requested:
                    break
                
                self.stats['current_pass'] = pass_num
                self._send_message('log', f"Проход {pass_num} из {self.stats['total_passes']}", 'info')
                
                # Выполнение прохода теста
                self._run_test_pass()
                
                if self.stop_requested:
                    break
            
            # Завершение теста
            self._test_complete()
            
        except Exception as e:
            self.logger.error(f"Ошибка в потоке тестирования: {e}", exc_info=True)
            self._send_message('error', str(e))
        finally:
            self.running = False
    
    def _run_test_pass(self):
        """Выполнение одного прохода теста"""
        patterns = []
        
        if self.test_params.get('test_ones', False):
            patterns.append(('ones', b'\xFF'))
        if self.test_params.get('test_zeros', False):
            patterns.append(('zeros', b'\x00'))
        if self.test_params.get('test_random', False):
            patterns.append(('random', None))
        
        # Если не выбрано ни одного паттерна, используем случайные данные
        if not patterns:
            patterns = [('random', None)]
        
        # Создаем временный файл для тестирования
        test_file_path = os.path.join(self.drive_path, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tmp")
        
        try:
            for pattern_name, pattern_value in patterns:
                if self.stop_requested:
                    break
                
                while self.paused and not self.stop_requested:
                    time.sleep(0.1)
                
                self._send_message('log', f"Паттерн: {pattern_name}", 'info')
                
                # Размер чанка для тестирования (64 МБ для реальной записи)
                chunk_size = 64 * 1024 * 1024
                
                # Количество чанков
                total_chunks = max(1, self.stats['total_bytes'] // chunk_size)
                
                # Подготовка данных для записи
                if pattern_name == 'ones':
                    data = pattern_value * chunk_size
                elif pattern_name == 'zeros':
                    data = pattern_value * chunk_size
                else:  # random
                    data = os.urandom(chunk_size)
                
                with open(test_file_path, 'wb') as f:
                    for chunk_num in range(total_chunks):
                        if self.stop_requested:
                            break
                        
                        while self.paused and not self.stop_requested:
                            time.sleep(0.1)
                        
                        # Запись данных
                        start_time = time.time()
                        
                        try:
                            f.write(data)
                            f.flush()
                            os.fsync(f.fileno())  # Принудительная запись на диск
                            
                            # Проверка чтения если включена
                            if self.test_params.get('test_verify', True):
                                f.seek(chunk_num * chunk_size)
                                read_data = f.read(chunk_size)
                                if read_data != data[:len(read_data)]:
                                    raise Exception("Ошибка верификации данных")
                            
                        except Exception as e:
                            # Ошибка записи/чтения - битый сектор
                            sector = chunk_num * (chunk_size // 512)
                            self._add_bad_sector(sector, str(e))
                            continue
                        
                        # Расчет скорости
                        elapsed = time.time() - start_time
                        speed = (chunk_size / 1024 / 1024) / max(elapsed, 0.001)
                        
                        # Обновление статистики
                        self.stats['tested_bytes'] += chunk_size
                        self.stats['tested'] = self.stats['tested_bytes'] / (1024**3)
                        
                        self.stats['speeds'].append(speed)
                        if self.stats['speeds']:
                            self.stats['avg_speed'] = sum(self.stats['speeds']) / len(self.stats['speeds'])
                        
                        if speed > self.stats['max_speed']:
                            self.stats['max_speed'] = speed
                        if speed < self.stats['min_speed']:
                            self.stats['min_speed'] = speed
                        
                        # Обновление времени
                        self.stats['elapsed_seconds'] = time.time() - self.stats['start_time']
                        hours = int(self.stats['elapsed_seconds'] // 3600)
                        minutes = int((self.stats['elapsed_seconds'] % 3600) // 60)
                        seconds = int(self.stats['elapsed_seconds'] % 60)
                        self.stats['elapsed_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        # Отправка данных в UI с ограничением частоты
                        current_time = time.time()
                        if current_time - self.last_update_time >= self.update_interval or chunk_num == total_chunks - 1:
                            progress = ((chunk_num + 1) / total_chunks) * 100
                            self._send_message('progress', progress)
                            self._send_message('speed', speed, self.stats['elapsed_seconds'])
                            self.last_update_time = current_time
                
                # Удаляем временный файл после каждого паттерна
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
                    
        except Exception as e:
            self.logger.error(f"Ошибка при тестировании: {e}")
            self._send_message('error', str(e))
        finally:
            # Очистка временного файла
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except:
                    pass
    
    def _add_bad_sector(self, sector: int, error_type: str):
        """Добавление битого сектора в статистику"""
        bad_sector = {
            'sector': sector,
            'error_type': error_type,
            'time': datetime.now().strftime("%H:%M:%S"),
            'attempts': 1
        }
        self.stats['bad_sectors'].append(bad_sector)
        self.stats['bad_sectors_count'] = len(self.stats['bad_sectors'])
        
        self._send_message('bad_sector', sector, error_type, 1)
        self._send_message('log', f"Найден битый сектор: {sector} - {error_type}", 'error')
    
    def _test_complete(self):
        """Завершение теста"""
        elapsed = self.stats['elapsed_time']
        
        if self.stop_requested:
            self._send_message('log', "Тест остановлен пользователем", 'warning')
            self._send_message('complete', "Тестирование прервано")
        else:
            self._send_message('log', f"Тестирование завершено за {elapsed}", 'success')
            
            # Форматирование после теста если нужно
            if self.test_params.get('auto_format', False):
                self._send_message('log', "Запуск форматирования...", 'info')
                # Запускаем форматирование
                self.app.disk_formatter.format_disk(
                    self.drive_path,
                    self.test_params.get('filesystem', 'FAT32')
                )
            
            self._send_message('complete', "Тестирование успешно завершено")
        
        self.logger.info(f"Тестирование завершено. Битых секторов: {self.stats['bad_sectors_count']}")
    
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
    
    def pause(self):
        """Пауза теста"""
        if self.running and not self.stop_requested:
            self.paused = not self.paused
            self.stats['test_paused'] = self.paused
            status = "приостановлен" if self.paused else "продолжен"
            self._send_message('log', f"Тест {status}", 'info')
            return self.paused
        return None
    
    def stop(self):
        """Остановка теста"""
        if self.running:
            self.stop_requested = True
            self._send_message('log', "Запрошена остановка теста...", 'warning')
    
    def is_running(self) -> bool:
        """Проверка, выполняется ли тест"""
        return self.running
    
    def get_statistics(self) -> Dict:
        """Получение текущей статистики"""
        return self.stats.copy()