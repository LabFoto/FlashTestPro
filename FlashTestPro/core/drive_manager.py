"""
Менеджер дисков - получение информации о накопителях
"""
import os
import platform
import psutil
import subprocess
from typing import List, Dict, Optional
from utils.logger import get_logger

class DriveManager:
    """Класс для работы с дисками"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.system = platform.system()
    
    def get_drives_list(self) -> List[Dict]:
        """Получение списка доступных дисков"""
        drives = []
        
        try:
            partitions = psutil.disk_partitions(all=False)
            
            for partition in partitions:
                drive_info = self._get_drive_info(partition)
                if drive_info:
                    drives.append(drive_info)
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения списка дисков: {e}")
        
        return drives
    
    def _get_drive_info(self, partition) -> Optional[Dict]:
        """Получение информации о конкретном диске"""
        try:
            # Получаем информацию о использовании диска
            usage = psutil.disk_usage(partition.mountpoint)
            
            # Определяем тип диска
            drive_type = self._get_drive_type(partition)
            
            # Проверяем, является ли диск системным
            is_system = self._is_system_drive(partition.mountpoint)
            
            # Получаем метку тома
            label = self._get_volume_label(partition.mountpoint)
            
            # Проверяем, является ли диск съемным
            is_removable = self._is_removable(partition.mountpoint)
            
            return {
                "path": partition.mountpoint,
                "device": partition.device,
                "type": drive_type,
                "fs": partition.fstype,
                "opts": partition.opts,
                "total_size": self._format_bytes(usage.total),
                "total_bytes": usage.total,
                "used": self._format_bytes(usage.used),
                "used_bytes": usage.used,
                "free": self._format_bytes(usage.free),
                "free_bytes": usage.free,
                "percent_used": usage.percent,
                "is_system": is_system,
                "label": label,
                "is_removable": is_removable
            }
        except Exception as e:
            self.logger.debug(f"Не удалось получить информацию для {partition.mountpoint}: {e}")
            return None
    
    def _get_drive_type(self, partition) -> str:
        """Определение типа диска"""
        # Сначала проверяем, системный ли диск
        if self._is_system_drive(partition.mountpoint):
            return 'system'

        if self.system == "Windows":
            if 'removable' in partition.opts:
                return 'removable'
            elif 'cdrom' in partition.opts:
                return 'cdrom'
            else:
                return 'fixed'
        else:  # Linux/macOS
            mountpoint = partition.mountpoint
            if mountpoint.startswith('/media') or mountpoint.startswith('/run/media'):
                return 'removable'
            elif mountpoint == '/':
                # Уже обработано выше, но оставим для надёжности
                return 'system'
            else:
                return 'fixed'
    
    def _is_system_drive(self, mountpoint: str) -> bool:
        """Проверка, является ли диск системным"""
        if self.system == "Windows":
            system_drive = os.environ.get('SystemDrive', 'C:') + '\\'
            return mountpoint.upper() == system_drive.upper()
        else:
            return mountpoint == '/'
    
    def _is_removable(self, mountpoint: str) -> bool:
        """Проверка, является ли диск съемным"""
        if self.system == "Windows":
            try:
                import ctypes
                drive = mountpoint[0].upper()
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive}:\\")
                # DRIVE_REMOVABLE = 2
                return drive_type == 2
            except:
                return False
        else:
            # Для Linux можно проверить через /sys/block/
            return 'removable' in mountpoint.lower() or '/media/' in mountpoint
    
    def _get_volume_label(self, mountpoint: str) -> str:
        """Получение метки тома"""
        try:
            if self.system == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                volume_name_buffer = ctypes.create_unicode_buffer(1024)
                kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(mountpoint),
                    volume_name_buffer,
                    ctypes.sizeof(volume_name_buffer),
                    None, None, None, None, 0
                )
                return volume_name_buffer.value
            else:  # Linux/macOS
                # Можно использовать blkid или другую утилиту
                result = subprocess.run(
                    ['lsblk', '-no', 'label', mountpoint],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
        except:
            return ""
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Форматирование байтов в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def is_admin(self) -> bool:
        """Проверка прав администратора"""
        try:
            if self.system == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def get_disk_health(self, drive_path: str) -> Dict:
        """Получение информации о здоровье диска (S.M.A.R.T. если доступно)"""
        health = {
            "status": "Неизвестно",
            "temperature": None,
            "power_on_hours": None,
            "bad_sectors": None
        }
        
        # TODO: Реализовать получение S.M.A.R.T. данных
        # Для Windows можно использовать WMI
        # Для Linux - smartctl
        
        return health