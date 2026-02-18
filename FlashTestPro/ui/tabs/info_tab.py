"""
Вкладка с информацией о системе и программе
"""
import tkinter as tk
from tkinter import ttk
import platform
import psutil
from datetime import datetime

class InfoTab(ttk.Frame):
    """Вкладка информации"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.create_widgets()
        self.update_info()
    
    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Информация о программе
        program_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("program_info", "Информация о программе")
        )
        program_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.program_labels = {}
        prog_info = [
            ("name", "Название:"),
            ("version", "Версия:"),
            ("author", "Автор:"),
            ("license", "Лицензия:"),
        ]
        
        for key, label in prog_info:
            row_frame = ttk.Frame(program_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(row_frame, text=label, font=("Segoe UI", 10, "bold"), width=15).pack(side=tk.LEFT)
            self.program_labels[key] = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            self.program_labels[key].pack(side=tk.LEFT, padx=(10, 0))
        
        # Информация о системе
        system_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("system_info", "Информация о системе")
        )
        system_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.system_labels = {}
        sys_info = [
            ("os", "ОС:"),
            ("python", "Python:"),
            ("processor", "Процессор:"),
            ("memory", "Память:"),
            ("disks", "Дисков:"),
            ("admin", "Администратор:"),
        ]
        
        for key, label in sys_info:
            row_frame = ttk.Frame(system_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(row_frame, text=label, font=("Segoe UI", 10, "bold"), width=15).pack(side=tk.LEFT)
            self.system_labels[key] = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            self.system_labels[key].pack(side=tk.LEFT, padx=(10, 0))
        
        # Кнопка обновления
        ttk.Button(
            main_frame,
            text=self.app.i18n.get("refresh", "🔄 Обновить"),
            command=self.update_info
        ).pack(pady=10)
        
        # Копирайт
        copyright_frame = ttk.Frame(main_frame)
        copyright_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(
            copyright_frame,
            text="© 2024 FlashTest Pro Team. " + self.app.i18n.get("all_rights_reserved", "Все права защищены."),
            font=("Segoe UI", 8),
            foreground="#888888"
        ).pack()
    
    def update_info(self):
        """Обновление информации"""
        # Информация о программе
        self.program_labels["name"].config(text=self.app.config.get("app", {}).get("name", "FlashTest Pro"))
        self.program_labels["version"].config(text=self.app.config.get("app", {}).get("version", "1.0.0"))
        self.program_labels["author"].config(text="DeepSeek")
        self.program_labels["license"].config(text="MIT")
        
        # Информация о системе
        self.system_labels["os"].config(text=f"{platform.system()} {platform.release()}")
        self.system_labels["python"].config(text=platform.python_version())
        self.system_labels["processor"].config(text=platform.processor() or "Неизвестно")
        
        # Память
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3)
        mem_used = mem.used / (1024**3)
        self.system_labels["memory"].config(text=f"{mem_used:.1f} GB / {mem_total:.1f} GB ({mem.percent}%)")
        
        # Количество дисков
        disks = len(psutil.disk_partitions())
        self.system_labels["disks"].config(text=str(disks))
        
        # Права администратора
        is_admin = self.app.drive_manager.is_admin()
        admin_text = self.app.i18n.get("yes", "Да") if is_admin else self.app.i18n.get("no", "Нет")
        self.system_labels["admin"].config(text=admin_text)
    
    def on_drive_selected(self, drive_info):
        """Обработка выбора диска"""
        pass
    
    def update_language(self):
        """Обновление языка"""
        # TODO: Обновить заголовки
        pass
    
    def update_theme(self):
        """Обновление темы"""
        pass