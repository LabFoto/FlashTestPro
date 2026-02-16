"""
Модуль форматирования дисков
"""
import subprocess
import platform
import threading
import queue
import time
import os
from typing import Tuple
from utils.logger import get_logger

class DiskFormatter:
    """Класс для форматирования дисков"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        self.system = platform.system()
        
        self.format_thread = None
        self.running = False
        self.message_queue = queue.Queue(maxsize=100)
    
    def format_disk(self, drive_path: str, filesystem: str = "FAT32", 
                   quick: bool = True, label: str = "") -> Tuple[bool, str]:
        """Форматирование диска"""
        self.logger.info(f"Форматирование {drive_path} в {filesystem}")
        
        # Запускаем форматирование в отдельном потоке
        self.format_thread = threading.Thread(
            target=self._format_worker,
            args=(drive_path, filesystem, quick, label),
            daemon=True
        )
        self.format_thread.start()
        
        # Возвращаем сразу, результат будет через сообщения
        return True, "Форматирование запущено"
    
    def _format_worker(self, drive_path: str, filesystem: str, quick: bool, label: str):
        """Рабочий поток форматирования"""
        self.running = True
        
        try:
            self._send_message('log', f"Начало форматирования {drive_path} в {filesystem}", 'info')
            
            if self.system == "Windows":
                result = self._format_windows(drive_path, filesystem, quick, label)
            elif self.system == "Linux":
                result = self._format_linux(drive_path, filesystem, quick, label)
            elif self.system == "Darwin":  # macOS
                result = self._format_macos(drive_path, filesystem, quick, label)
            else:
                result = (False, f"Неподдерживаемая ОС: {self.system}")
            
            if result[0]:
                self._send_message('log', result[1], 'success')
                self._send_message('complete', result[1])
            else:
                self._send_message('log', f"Ошибка: {result[1]}", 'error')
                self._send_message('error', result[1])
                
        except Exception as e:
            self.logger.error(f"Ошибка форматирования: {e}")
            self._send_message('log', f"Ошибка: {str(e)}", 'error')
            self._send_message('error', str(e))
        finally:
            self.running = False
    
    def _format_windows(self, drive_path: str, filesystem: str, 
                       quick: bool, label: str) -> Tuple[bool, str]:
        """Форматирование в Windows"""
        try:
            drive_letter = drive_path[0]
            
            # Параметры команды format
            fs_option = f"/FS:{filesystem}"
            quick_option = "/Q" if quick else ""
            label_option = f"/V:{label}" if label else ""
            
            # Используем cmd /c для выполнения команды
            cmd = ["cmd", "/c", "format", f"{drive_letter}:"]
            if fs_option:
                cmd.append(fs_option)
            if quick_option:
                cmd.append(quick_option)
            if label_option:
                cmd.append(label_option)
            cmd.append("/Y")  # Автоматическое подтверждение
            
            self._send_message('log', f"Выполнение команды: {' '.join(cmd)}", 'info')
            
            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='cp866'  # Для русских букв в Windows
            )
            
            # Читаем вывод построчно
            for line in process.stdout:
                self._send_message('log', line.strip(), 'info')
                # Пытаемся определить прогресс
                if '%' in line:
                    try:
                        percent = int(''.join(filter(str.isdigit, line.split('%')[0])))
                        self._send_message('progress', percent)
                    except:
                        pass
            
            process.wait()
            
            if process.returncode == 0:
                return True, f"Диск {drive_path} успешно отформатирован в {filesystem}"
            else:
                error = process.stderr.read()
                return False, f"Ошибка форматирования: {error}"
                
        except Exception as e:
            return False, str(e)
    
    def _format_linux(self, drive_path: str, filesystem: str, 
                     quick: bool, label: str) -> Tuple[bool, str]:
        """Форматирование в Linux"""
        try:
            # Определяем команду в зависимости от файловой системы
            if filesystem == "FAT32":
                cmd = ["mkfs.vfat", "-F", "32", drive_path]
                if label:
                    cmd.extend(["-n", label])
            elif filesystem == "NTFS":
                cmd = ["mkfs.ntfs", "-f" if quick else "-Q", drive_path]
                if label:
                    cmd.extend(["-L", label])
            elif filesystem == "exFAT":
                cmd = ["mkfs.exfat", drive_path]
                if label:
                    cmd.extend(["-n", label])
            elif filesystem == "EXT4":
                cmd = ["mkfs.ext4", "-F", drive_path]
                if label:
                    cmd.extend(["-L", label])
            else:
                return False, f"Неподдерживаемая ФС: {filesystem}"
            
            self._send_message('log', f"Выполнение команды: {' '.join(cmd)}", 'info')
            
            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Читаем вывод
            for line in process.stdout:
                self._send_message('log', line.strip(), 'info')
            
            process.wait()
            
            if process.returncode == 0:
                return True, f"Диск {drive_path} успешно отформатирован в {filesystem}"
            else:
                error = process.stderr.read()
                return False, f"Ошибка форматирования: {error}"
                
        except Exception as e:
            return False, str(e)
    
    def _format_macos(self, drive_path: str, filesystem: str, 
                     quick: bool, label: str) -> Tuple[bool, str]:
        """Форматирование в macOS"""
        try:
            # Определяем формат для diskutil
            fs_map = {
                "FAT32": "MS-DOS FAT32",
                "exFAT": "ExFAT",
                "NTFS": "NTFS",
                "EXT4": "EXT4"
            }
            
            fs_format = fs_map.get(filesystem, "MS-DOS FAT32")
            
            # Получаем идентификатор диска
            disk_id = os.path.basename(drive_path)
            
            cmd = ["diskutil", "eraseDisk", fs_format, label or "UNTITLED", disk_id]
            
            self._send_message('log', f"Выполнение команды: {' '.join(cmd)}", 'info')
            
            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Читаем вывод
            for line in process.stdout:
                self._send_message('log', line.strip(), 'info')
            
            process.wait()
            
            if process.returncode == 0:
                return True, f"Диск {drive_path} успешно отформатирован в {filesystem}"
            else:
                error = process.stderr.read()
                return False, f"Ошибка форматирования: {error}"
                
        except Exception as e:
            return False, str(e)
    
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
    
    def is_running(self) -> bool:
        """Проверка, выполняется ли форматирование"""
        return self.running