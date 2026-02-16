"""
Панель прогресса для отображения хода выполнения операций
"""
import tkinter as tk
from tkinter import ttk

class ProgressPanel(ttk.Frame):
    """Панель отображения прогресса"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self._create_widgets()
        self.reset()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Основной прогресс
        progress_frame = ttk.LabelFrame(self, text=self.app.i18n.get("progress", "Прогресс"))
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(pady=(0, 5))
        
        # Информация о скорости
        speed_frame = ttk.LabelFrame(self, text=self.app.i18n.get("speed", "Скорость"))
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.speed_label = ttk.Label(speed_frame, text="0 MB/s")
        self.speed_label.pack(padx=5, pady=5)
        
        # Информация о битых секторах
        bad_frame = ttk.LabelFrame(self, text=self.app.i18n.get("bad_sectors", "Битые сектора"))
        bad_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.bad_label = ttk.Label(bad_frame, text="0")
        self.bad_label.pack(padx=5, pady=5)
        
        # Информация о времени
        time_frame = ttk.LabelFrame(self, text=self.app.i18n.get("time", "Время"))
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.time_label = ttk.Label(time_frame, text="00:00:00")
        self.time_label.pack(padx=5, pady=5)
        
        # Детальная информация
        self.detail_label = ttk.Label(self, text="", font=("Segoe UI", 8))
        self.detail_label.pack(pady=5)
    
    def update_progress(self, value):
        """Обновление прогресса"""
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"{value:.1f}%")
        self.update_idletasks()
    
    def update_speed(self, speed):
        """Обновление скорости"""
        self.speed_label.config(text=f"{speed:.1f} MB/s")
        self.update_idletasks()
    
    def update_time(self, time_str):
        """Обновление времени"""
        self.time_label.config(text=time_str)
        self.update_idletasks()
    
    def add_bad_sector(self):
        """Увеличение счетчика битых секторов"""
        current = int(self.bad_label.cget("text"))
        self.bad_label.config(text=str(current + 1))
        self.update_idletasks()
    
    def update_detail(self, text):
        """Обновление детальной информации"""
        self.detail_label.config(text=text)
        self.update_idletasks()
    
    def reset(self):
        """Сброс панели"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
        self.speed_label.config(text="0 MB/s")
        self.bad_label.config(text="0")
        self.time_label.config(text="00:00:00")
        self.detail_label.config(text="")
        self.update_idletasks()
    
    def update_theme(self):
        """Обновление темы"""
        pass  # Тема обновляется автоматически через ttk