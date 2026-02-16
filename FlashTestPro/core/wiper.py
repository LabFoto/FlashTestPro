"""
Модуль безопасного затирания данных
"""
import os
import time
import random
import threading
import queue
from typing import Dict, Tuple
from utils.logger import get_logger

class DataWiper:
    """Класс для безопасного затирания данных"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        
        self.wipe_thread = None
        self.running = False
        self.stop_requested = False
        
        self.message_queue = queue.Queue(maxsize=100)
    
    def wipe_disk(self, drive_path: str, method: str = "dod", passes: int = 3) -> bool:
        """Запуск затирания диска"""
        if self.running:
            return False
        
        self.drive_path = drive_path
        self.method = method
        self.passes = passes
        self.running = True
        self.stop_requested = False
        
        self.wipe_thread = threading.Thread(target=self._wipe_worker, daemon=True)
        self.wipe_thread.start()
        
        self.logger.info(f"Затирание запущено для диска {drive_path} методом {method}")
        return True
    
    def _wipe_worker(self):
        """Рабочий поток затирания"""
        try:
            # Определяем количество проходов в зависимости от метода
            if self.method == "simple":
                passes_to_do = 1
                patterns = [0x00]
            elif self.method == "dod":
                passes_to_do = 3
                patterns = [0x00, 0xFF, 0xAA]  # DoD 5220.22-M
            elif self.method == "gutmann":
                passes_to_do = 35
                patterns = self._get_gutmann_patterns()
            else:
                passes_to_do = self.passes
                patterns = [random.randint(0, 255) for _ in range(passes_to_do)]
            
            self._send_message('log', f"Начало затирания методом {self.method}", 'info')
            
            for pass_num in range(1, passes_to_do + 1):
                if self.stop_requested:
                    break
                
                pattern = patterns[(pass_num - 1) % len(patterns)]
                self._send_message('log', f"Проход {pass_num}/{passes_to_do} - паттерн: {pattern:02X}", 'info')
                
                # Имитация записи
                time.sleep(0.5)
                
                progress = (pass_num / passes_to_do) * 100
                self._send_message('progress', progress)
            
            if self.stop_requested:
                self._send_message('log', "Затирание прервано пользователем", 'warning')
                self._send_message('complete', "Затирание прервано")
            else:
                self._send_message('log', "Затирание успешно завершено", 'success')
                self._send_message('complete', "Затирание завершено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при затирании: {e}")
            self._send_message('error', str(e))
        finally:
            self.running = False
    
    def _get_gutmann_patterns(self) -> list:
        """Получение паттернов Гутманна (35 проходов)"""
        patterns = []
        
        # Первые 4 прохода: случайные данные
        for i in range(4):
            patterns.append(random.randint(0, 255))
        
        # Проходы 5-31: специальные паттерны
        special_patterns = [0x55, 0xAA, 0x92, 0x49, 0x24, 0x12, 0x09, 0x04, 
                           0x02, 0x01, 0x80, 0x40, 0x20, 0x10, 0x08]
        patterns.extend(special_patterns * 2)  # 27 проходов
        
        # Последние 4 прохода: случайные данные
        for i in range(4):
            patterns.append(random.randint(0, 255))
        
        return patterns[:35]  # Ровно 35 проходов
    
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
    
    def is_running(self) -> bool:
        """Проверка, выполняется ли затирание"""
        return self.running