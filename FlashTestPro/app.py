"""
Главный класс приложения FlashTest Pro
"""
import tkinter as tk
from tkinter import ttk, messagebox
import platform
import os
from datetime import datetime

from core.drive_manager import DriveManager
from core.tester import DiskTester
from core.formatter import DiskFormatter
from core.wiper import DataWiper
from ui.main_window import MainWindow
from utils.config import ConfigManager
from utils.logger import get_logger
from utils.i18n import I18n
from ui.themes import ThemeManager

class FlashTestProApp:
    """Основной класс приложения"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("=" * 50)
        self.logger.info("ЗАПУСК FlashTest Pro")
        self.logger.info("=" * 50)
        
        # Загрузка конфигурации
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Инициализация менеджера языков
        self.i18n = I18n(self.config.get("ui", {}).get("language", "ru"))
        
        # Инициализация менеджера тем
        self.theme_manager = ThemeManager(self.config.get("ui", {}).get("theme", "dark"))
        
        # Создание корневого окна
        self.root = tk.Tk()
        self.root.title(self.i18n.get("app_title", "FlashTest Pro"))
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Установка иконки
        self._setup_icon()
        
        # Применение темы
        self.theme_manager.apply_to_root(self.root)
        
        # Инициализация менеджеров устройств
        self.drive_manager = DriveManager()
        self.disk_tester = DiskTester(self)
        self.disk_formatter = DiskFormatter(self)
        self.data_wiper = DataWiper(self)
        
        # Создание главного окна интерфейса
        self.main_window = MainWindow(self)
        
        # Проверка прав администратора
        self._check_admin_rights()
        
        # Обновление списка дисков при запуске
        self.root.after(100, self.refresh_drives)
        
        self.logger.info("Приложение инициализировано успешно")
    
    def _setup_icon(self):
        """Установка иконки приложения"""
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                if platform.system() == "Windows":
                    self.root.iconbitmap(icon_path)
                else:
                    img = tk.PhotoImage(file=icon_path.replace('.ico', '.png'))
                    self.root.iconphoto(True, img)
            except Exception as e:
                self.logger.warning(f"Не удалось загрузить иконку: {e}")
    
    def _check_admin_rights(self):
        """Проверка прав администратора"""
        is_admin = self.drive_manager.is_admin()
        if not is_admin:
            self.logger.warning("Приложение запущено без прав администратора")
            self.main_window.show_admin_warning()
    
    def refresh_drives(self):
        """Обновление списка дисков"""
        drives = self.drive_manager.get_drives_list()
        self.main_window.update_drive_list(drives)
        return drives
    
    def get_selected_drive(self):
        """Получение выбранного диска"""
        return self.main_window.get_selected_drive()
    
    def run(self):
        """Запуск главного цикла приложения"""
        # Центрирование окна
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.logger.info("Запуск главного цикла")
        self.root.mainloop()
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.disk_tester.is_running():
            if messagebox.askyesno(
                self.i18n.get("confirm_exit_title", "Подтверждение"),
                self.i18n.get("confirm_exit_text", "Тестирование выполняется. Вы уверены, что хотите выйти?")
            ):
                self.disk_tester.stop()
                self.root.quit()
        else:
            self.root.quit()
    
    def change_language(self, lang_code):
        """Изменение языка интерфейса"""
        self.i18n.set_language(lang_code)
        self.config_manager.update_config("ui", "language", lang_code)
        self.main_window.update_ui_language()
    
    def change_theme(self, theme_name):
        """Изменение темы оформления"""
        self.theme_manager.set_theme(theme_name)
        self.config_manager.update_config("ui", "theme", theme_name)
        self.main_window.update_theme()