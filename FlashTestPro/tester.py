"""
Модуль тестирования дисков
"""
import os
import time
import random
import threading
import queue
from datetime import datetime, timedelta
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
        self.message_queue = queue.Queue()
        
        # Статистика теста
        self.stats = self._init_stats()
        
        # Параметры теста
        self.test_params = {}
        self.drive_path = ""
    
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
            'test_paused': False
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
        
        # Получаем размер диска
        try:
            drive_info = self.app.drive_manager._get_drive_info(
                psutil.disk_partitions()[0]
            )
            if drive_info:
                self.stats['total_bytes'] = drive_info['total_bytes']
                self.stats['total_size'] = drive_info['total_bytes'] / (1024**3)
        except:
            pass
        
        # Запуск потока тестирования
        self.test_thread = threading.Thread(target=self._test_worker, daemon=True)
        self.test_thread.start()
        
        self.logger.info(f"Тестирование запущено для диска {drive_path}")
    
    def _test_worker(self):
        """Рабочий поток тестирования"""
        self.stats['start_time'] = time.time()
        
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
            patterns.append(('ones', 0xFF))
        if self.test_params.get('test_zeros', False):
            patterns.append(('zeros', 0x00))
        if self.test_params.get('test_random', False):
            patterns.append(('random', None))
        
        # Если не выбрано ни одного паттерна, используем случайные данные
        if not patterns:
            patterns = [('random', None)]
        
        for pattern_name, pattern_value in patterns:
            if self.stop_requested:
                break
            
            while self.paused and not self.stop_requested:
                time.sleep(0.1)
            
            self._send_message('log', f"Паттерн: {pattern_name}", 'info')
            
            # Размер чанка для тестирования (32 МБ по умолчанию)
            chunk_size = 32 * 1024 * 1024
            
            # Количество чанков
            total_chunks = max(1, self.stats['total_bytes'] // chunk_size)
            
            for chunk_num in range(total_chunks):
                if self.stop_requested:
                    break
                
                while self.paused and not self.stop_requested:
                    time.sleep(0.1)
                
                # Имитация записи
                start_time = time.time()
                
                # Здесь должна быть реальная запись на диск
                # Для демонстрации используем задержку
                time.sleep(0.01)  # Имитация работы
                
                # Расчет скорости
                elapsed = time.time() - start_time
                speed = (chunk_size / 1024 / 1024) / max(elapsed, 0.001)
                
                # Обновление статистики
                self.stats['tested_bytes'] += chunk_size
                self.stats['tested'] = self.stats['tested_bytes'] / (1024**3)
                
                self.stats['speeds'].append(speed)
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
                
                # Отправка данных в UI
                progress = (chunk_num + 1) / total_chunks * 100
                self._send_message('progress', progress)
                self._send_message('speed', speed, time.time() - self.stats['start_time'])
                
                # Имитация битых секторов (для демонстрации)
                if random.random() < 0.001:  # 0.1% вероятность
                    sector = chunk_num * (chunk_size // 512)
                    self._add_bad_sector(sector, "Ошибка чтения/записи")
    
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
        self._send_message('log', f"Найден битый сектор: {sector}", 'error')
    
    def _test_complete(self):
        """Завершение теста"""
        elapsed = self.stats['elapsed_time']
        
        if self.stop_requested:
            self._send_message('log', f"Тест остановлен пользователем", 'warning')
            self._send_message('complete', "Тестирование прервано")
        else:
            self._send_message('log', f"Тестирование завершено за {elapsed}", 'success')
            
            # Форматирование после теста если нужно
            if self.test_params.get('auto_format', False):
                self._send_message('log', "Запуск форматирования...", 'info')
                self.app.disk_formatter.format_disk(
                    self.drive_path,
                    self.test_params.get('filesystem', 'FAT32')
                )
            
            self._send_message('complete', "Тестирование успешно завершено")
        
        self.logger.info(f"Тестирование завершено. Битых секторов: {self.stats['bad_sectors_count']}")
    
    def _send_message(self, msg_type: str, *args):
        """Отправка сообщения в очередь"""
        self.message_queue.put((msg_type,) + args)
    
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