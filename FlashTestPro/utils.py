import os
import platform
import psutil

def get_drive_info(drive_path):
    """Получить информацию о диске"""
    try:
        usage = psutil.disk_usage(drive_path)
        return {
            'total': usage.total / (1024**3),
            'used': usage.used / (1024**3),
            'free': usage.free / (1024**3),
            'percent': usage.percent
        }
    except:
        return None

def is_admin():
    """Проверка прав администратора"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0

def format_bytes(bytes_value):
    """Форматирование байтов в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"