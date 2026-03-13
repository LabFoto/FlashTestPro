"""
Ядро программы - модули для работы с дисками
"""
from .drive_manager import DriveManager
from .tester import DiskTester
from .formatter import DiskFormatter
from .wiper import DataWiper

__all__ = ['DriveManager', 'DiskTester', 'DiskFormatter', 'DataWiper']