"""
Менеджер дисков – получение информации о накопителях.
Поддержка неотформатированных (RAW) дисков и S.M.A.R.T. данных.
"""
import os
import platform
import psutil
import subprocess
from typing import List, Dict, Optional
from utils.logger import get_logger

class DriveManager:
    """Класс для работы с дисками (включая неотформатированные и S.M.A.R.T.)"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.system = platform.system()
        # Попытка импортировать WMI для Windows (если доступен)
        if self.system == "Windows":
            try:
                import wmi
                self.wmi_conn = wmi.WMI()
            except ImportError:
                self.wmi_conn = None
                self.logger.warning("Модуль wmi не установлен. Некоторые диски могут не отображаться.")
        else:
            self.wmi_conn = None

    def get_drives_list(self, show_all: bool = False) -> List[Dict]:
        """
        Получение списка доступных дисков.
        Если show_all=False – показываем только логические диски (с буквами / точками монтирования).
        Если show_all=True – показываем все устройства, включая неразмеченные и RAW.
        """
        all_drives = self._get_all_drives()

        if show_all:
            return all_drives

        # Фильтруем: оставляем только диски с обычными путями (буквами)
        filtered = []
        for d in all_drives:
            path = d['path']
            if self.system == "Windows":
                # Исключаем физические диски без буквы
                if path.startswith("PHYSICALDRIVE") or path.startswith("\\\\.\\PhysicalDrive"):
                    continue
            # Исключаем записи с типом raw_disk / raw_partition (если они есть)
            if d.get('type') in ('raw_disk', 'raw_partition'):
                continue
            filtered.append(d)
        return filtered

    def _get_all_drives(self) -> List[Dict]:
        """Получение ВСЕХ дисков (логические + физические, включая неразмеченные)."""
        drives = []

        if self.system == "Windows" and self.wmi_conn:
            drives = self._get_drives_windows()
        else:
            drives = self._get_drives_psutil_all()

        drives.sort(key=lambda d: (d.get('is_system', False), d['path']))
        return drives

    def _get_drives_psutil_all(self) -> List[Dict]:
        """Получение дисков через psutil.disk_partitions(all=True) + обработка ошибок."""
        drives = []
        try:
            partitions = psutil.disk_partitions(all=True)
        except Exception as e:
            self.logger.error(f"Ошибка вызова psutil.disk_partitions: {e}")
            return drives

        for part in partitions:
            usage = None
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except Exception:
                pass

            drive_info = self._build_drive_info(part, usage)
            if drive_info:
                drives.append(drive_info)
        return drives

    def _get_drives_windows(self) -> List[Dict]:
        """
        Получение дисков в Windows через WMI:
        - логические диски (Win32_LogicalDisk)
        - физические диски без разделов
        - RAW-разделы без буквы
        """
        drives = []
        try:
            # 1. Логические диски
            for logical_disk in self.wmi_conn.Win32_LogicalDisk():
                drive_info = self._disk_from_wmi_logical(logical_disk)
                if drive_info:
                    drives.append(drive_info)

            # 2. Физические диски без разделов
            for disk in self.wmi_conn.Win32_DiskDrive():
                partitions = disk.associators("Win32_DiskDriveToDiskPartition")
                if not partitions:
                    drive_info = self._disk_from_wmi_physical_unallocated(disk)
                    if drive_info:
                        drives.append(drive_info)
                else:
                    for part in partitions:
                        logical_disks = part.associators("Win32_LogicalDiskToPartition")
                        if not logical_disks:
                            drive_info = self._partition_from_wmi_raw(part, disk)
                            if drive_info:
                                drives.append(drive_info)
        except Exception as e:
            self.logger.error(f"Ошибка при получении дисков через WMI: {e}")
            drives.extend(self._get_drives_psutil_all())
        return drives

    def _build_drive_info(self, partition, usage=None) -> Optional[Dict]:
        """Сбор информации о разделе в единый словарь."""
        try:
            drive_type = self._get_drive_type(partition)
            is_system = self._is_system_drive(partition.mountpoint)
            label = self._get_volume_label(partition.mountpoint)
            is_removable = self._is_removable(partition.mountpoint)

            if usage is None:
                total_bytes = 0
                used_bytes = 0
                free_bytes = 0
                percent_used = 0
                total_size = "N/A"
                used = "N/A"
                free = "N/A"
            else:
                total_bytes = usage.total
                used_bytes = usage.used
                free_bytes = usage.free
                percent_used = usage.percent
                total_size = self._format_bytes(usage.total)
                used = self._format_bytes(usage.used)
                free = self._format_bytes(usage.free)

            return {
                "path": partition.mountpoint,
                "device": partition.device,
                "type": drive_type,
                "fs": partition.fstype if partition.fstype else "RAW",
                "opts": partition.opts,
                "total_size": total_size,
                "total_bytes": total_bytes,
                "used": used,
                "used_bytes": used_bytes,
                "free": free,
                "free_bytes": free_bytes,
                "percent_used": percent_used,
                "is_system": is_system,
                "label": label,
                "is_removable": is_removable
            }
        except Exception as e:
            self.logger.debug(f"Не удалось собрать информацию для {partition.mountpoint}: {e}")
            return None

    def _disk_from_wmi_logical(self, logical_disk) -> Optional[Dict]:
        """Создание информации о логическом диске из WMI Win32_LogicalDisk."""
        try:
            path = logical_disk.DeviceID + "\\"
            fs = logical_disk.FileSystem or "RAW"
            total_bytes = int(logical_disk.Size) if logical_disk.Size else 0
            free_bytes = int(logical_disk.FreeSpace) if logical_disk.FreeSpace else 0
            used_bytes = total_bytes - free_bytes
            percent_used = (used_bytes / total_bytes * 100) if total_bytes else 0
            drive_type = self._get_drive_type_from_wmi(logical_disk.DriveType)
            is_system = self._is_system_drive(path)
            if is_system:
                drive_type = 'system'  # ← исправление: системный диск получает тип 'system'
            label = logical_disk.VolumeName or ""
            is_removable = (logical_disk.DriveType == 2)

            return {
                "path": path,
                "device": path,
                "type": drive_type,
                "fs": fs,
                "opts": "",
                "total_size": self._format_bytes(total_bytes),
                "total_bytes": total_bytes,
                "used": self._format_bytes(used_bytes),
                "used_bytes": used_bytes,
                "free": self._format_bytes(free_bytes),
                "free_bytes": free_bytes,
                "percent_used": percent_used,
                "is_system": is_system,
                "label": label,
                "is_removable": is_removable
            }
        except Exception as e:
            self.logger.debug(f"Ошибка обработки WMI LogicalDisk: {e}")
            return None

    def _disk_from_wmi_physical_unallocated(self, disk) -> Optional[Dict]:
        """Создание записи для физического диска без разделов (неразмеченная область)."""
        try:
            path = f"\\\\.\\PhysicalDrive{disk.Index}"
            total_bytes = int(disk.Size) if disk.Size else 0
            is_system = (disk.Index == 0)
            label = f"Неразмеченный диск {disk.Index}"
            is_removable = (disk.MediaType and "Removable" in disk.MediaType)

            return {
                "path": f"PHYSICALDRIVE{disk.Index}",
                "device": path,
                "type": "raw_disk",
                "fs": "RAW (не размечен)",
                "opts": "",
                "total_size": self._format_bytes(total_bytes),
                "total_bytes": total_bytes,
                "used": "0 B",
                "used_bytes": 0,
                "free": self._format_bytes(total_bytes),
                "free_bytes": total_bytes,
                "percent_used": 0,
                "is_system": is_system,
                "label": label,
                "is_removable": is_removable
            }
        except Exception as e:
            self.logger.debug(f"Ошибка создания записи для неразмеченного диска: {e}")
            return None

    def _partition_from_wmi_raw(self, partition, disk) -> Optional[Dict]:
        """Создание записи для раздела без буквы (RAW)."""
        try:
            total_bytes = int(partition.Size) if partition.Size else 0
            path = f"\\\\.\\{partition.Name}"
            is_system = (disk.Index == 0)
            label = f"RAW раздел на диске {disk.Index}"

            return {
                "path": path,
                "device": path,
                "type": "raw_partition",
                "fs": "RAW",
                "opts": "",
                "total_size": self._format_bytes(total_bytes),
                "total_bytes": total_bytes,
                "used": "0 B",
                "used_bytes": 0,
                "free": self._format_bytes(total_bytes),
                "free_bytes": total_bytes,
                "percent_used": 0,
                "is_system": is_system,
                "label": label,
                "is_removable": (disk.MediaType and "Removable" in disk.MediaType)
            }
        except Exception as e:
            self.logger.debug(f"Ошибка создания записи для RAW раздела: {e}")
            return None

    def _get_drive_type_from_wmi(self, drive_type_code: int) -> str:
        """Преобразование кода типа диска WMI в строку."""
        mapping = {
            2: "removable",
            3: "fixed",
            4: "network",
            5: "cdrom"
        }
        return mapping.get(drive_type_code, "unknown")

    def _get_drive_type(self, partition) -> str:
        """Определение типа диска (системный, съёмный, CD-ROM и т.д.)"""
        if self._is_system_drive(partition.mountpoint):
            return 'system'

        if self.system == "Windows":
            if 'removable' in partition.opts:
                return 'removable'
            elif 'cdrom' in partition.opts:
                return 'cdrom'
            else:
                return 'fixed'
        else:
            mountpoint = partition.mountpoint
            if mountpoint.startswith('/media') or mountpoint.startswith('/run/media'):
                return 'removable'
            else:
                return 'fixed'

    def _is_system_drive(self, mountpoint: str) -> bool:
        """Проверка, является ли диск системным."""
        if self.system == "Windows":
            system_drive = os.environ.get('SystemDrive', 'C:') + '\\'
            return mountpoint.upper() == system_drive.upper()
        else:
            return mountpoint == '/'

    def _is_removable(self, mountpoint: str) -> bool:
        """Проверка, является ли диск съёмным."""
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
            return 'removable' in mountpoint.lower() or '/media/' in mountpoint

    def _get_volume_label(self, mountpoint: str) -> str:
        """Получение метки тома."""
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
            else:
                result = subprocess.run(
                    ['lsblk', '-no', 'label', mountpoint],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
        except:
            return ""

    def _format_bytes(self, bytes_value: int) -> str:
        """Форматирование байтов в читаемый вид."""
        if bytes_value == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def is_admin(self) -> bool:
        """Проверка прав администратора."""
        try:
            if self.system == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False

    def get_smart_data(self, drive_path: str) -> Dict:
        """
        Получение S.M.A.R.T. данных для диска.
        Поддерживаются Windows (WMI), Linux/macOS (smartctl).
        Возвращает словарь с ключами: status, temperature, power_on_hours, raw_read_error_rate, reallocated_sectors, и др.
        """
        smart_info = {
            "status": "Неизвестно",
            "temperature": None,
            "power_on_hours": None,
            "raw_read_error_rate": None,
            "reallocated_sectors": None,
            "spin_retry_count": None,
            "start_stop_count": None,
            "health": None
        }

        if self.system == "Windows" and self.wmi_conn:
            smart_info = self._get_smart_windows(drive_path)
        elif self.system in ("Linux", "Darwin"):
            smart_info = self._get_smart_posix(drive_path)
        else:
            self.logger.warning(f"S.M.A.R.T. не поддерживается для ОС {self.system}")

        return smart_info

    def _get_smart_windows(self, drive_path: str) -> Dict:
        """Получение S.M.A.R.T. через WMI."""
        smart = {
            "status": "Неизвестно",
            "temperature": None,
            "power_on_hours": None,
            "raw_read_error_rate": None,
            "reallocated_sectors": None,
            "spin_retry_count": None,
            "start_stop_count": None,
            "health": None
        }
        try:
            import re
            match = re.search(r'PhysicalDrive(\d+)', drive_path, re.IGNORECASE)
            if match:
                disk_index = int(match.group(1))
            else:
                disk_index = self._get_physical_drive_index_from_path(drive_path)
                if disk_index is None:
                    return smart

            # Win32_DiskDrive
            for disk in self.wmi_conn.Win32_DiskDrive(Index=disk_index):
                smart["status"] = disk.Status
                smart["health"] = disk.Status
                break

            # MSStorageDriver_FailurePredictStatus
            try:
                for pred in self.wmi_conn.MSStorageDriver_FailurePredictStatus():
                    if pred.Index == disk_index:
                        smart["health"] = "Predicted Failure" if pred.PredictFailure else "OK"
                        break
            except:
                pass
        except Exception as e:
            self.logger.error(f"Ошибка получения S.M.A.R.T. через WMI: {e}")
        return smart

    def _get_smart_posix(self, drive_path: str) -> Dict:
        """Получение S.M.A.R.T. через smartctl."""
        smart = {
            "status": "Неизвестно",
            "temperature": None,
            "power_on_hours": None,
            "raw_read_error_rate": None,
            "reallocated_sectors": None,
            "spin_retry_count": None,
            "start_stop_count": None,
            "health": None
        }
        try:
            device = self._get_device_path(drive_path)
            if not device:
                return smart

            result = subprocess.run(
                ['smartctl', '-a', device],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return smart

            output = result.stdout
            import re

            health_match = re.search(r'SMART overall-health self-assessment test result:\s*(\w+)', output, re.IGNORECASE)
            if health_match:
                smart["health"] = health_match.group(1)
                smart["status"] = "OK" if "PASSED" in health_match.group(1).upper() else "FAIL"

            temp_match = re.search(r'Temperature_Celsius\s+0x...\s+(\d+)', output)
            if not temp_match:
                temp_match = re.search(r'Airflow_Temperature_Cel.*?(\d+)', output)
            if temp_match:
                smart["temperature"] = int(temp_match.group(1))

            poh_match = re.search(r'Power_On_Hours.*?(\d+)', output)
            if poh_match:
                smart["power_on_hours"] = int(poh_match.group(1))

            realloc_match = re.search(r'Reallocated_Sector_Ct.*?(\d+)', output)
            if realloc_match:
                smart["reallocated_sectors"] = int(realloc_match.group(1))

        except Exception as e:
            self.logger.error(f"Ошибка получения S.M.A.R.T. через smartctl: {e}")
        return smart

    def _get_physical_drive_index_from_path(self, drive_path: str) -> Optional[int]:
        """Для Windows: по букве диска определяет индекс физического диска."""
        if self.system != "Windows" or not self.wmi_conn:
            return None
        try:
            drive_letter = drive_path[0].upper()
            logical_disks = self.wmi_conn.Win32_LogicalDisk(DeviceID=f"{drive_letter}:")
            for ld in logical_disks:
                for partition in ld.associators("Win32_LogicalDiskToPartition"):
                    for disk_drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                        return int(disk_drive.Index)
        except Exception as e:
            self.logger.debug(f"Не удалось определить индекс физического диска для {drive_path}: {e}")
        return None

    def _get_device_path(self, mountpoint: str) -> Optional[str]:
        """Вспомогательный метод для получения пути к блочному устройству по точке монтирования."""
        if self.system == "Windows":
            return self._get_physical_drive_path_from_mountpoint(mountpoint)
        elif self.system == "Linux":
            try:
                with open('/proc/mounts') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) > 1 and parts[1] == mountpoint:
                            return parts[0]
            except:
                pass
        elif self.system == "Darwin":
            try:
                result = subprocess.run(
                    ['mount'],
                    capture_output=True, text=True
                )
                for line in result.stdout.split('\n'):
                    if f' on {mountpoint} ' in line:
                        return line.split()[0]
            except:
                pass
        return None

    def _get_physical_drive_path_from_mountpoint(self, mountpoint: str) -> Optional[str]:
        r"""
        Для Windows: преобразует "C:\" в "\\.\PhysicalDriveN".
        """
        if self.system != "Windows" or not self.wmi_conn:
            return None
        idx = self._get_physical_drive_index_from_path(mountpoint)
        if idx is not None:
            return f"\\\\.\\PhysicalDrive{idx}"
        return None

    def get_partition_offsets(self, device_path):
        """
        Для Windows: возвращает список кортежей (start, end) в байтах для каждого раздела на физическом диске.
        Для Linux: пока не реализовано (возвращает пустой список).
        """
        if self.system != "Windows" or not self.wmi_conn:
            return []
        import re
        match = re.search(r'PhysicalDrive(\d+)', device_path, re.IGNORECASE)
        if not match:
            return []
        disk_index = int(match.group(1))
        offsets = []
        try:
            partitions = self.wmi_conn.Win32_DiskPartition()
            for part in partitions:
                if part.DiskIndex == disk_index:
                    start = int(part.StartingOffset)
                    size = int(part.Size)
                    end = start + size
                    offsets.append((start, end))
        except Exception as e:
            self.logger.error(f"Ошибка получения разделов: {e}")
        return offsets
