"""
Виджет для отображения логов с цветовой маркировкой
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

class LogViewer(ttk.Frame):
    """Просмотрщик логов с цветовой маркировкой"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Получаем цвета из темы
        colors = self.app.theme_manager.colors
        
        # Текстовое поле для лога
        self.text = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=colors["log_bg"],
            fg=colors["log_fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"],
            relief=tk.FLAT,
            borderwidth=0
        )
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Настройка тегов для раскраски
        self._configure_tags()
    
    def _configure_tags(self):
        """Настройка цветовых тегов"""
        colors = self.app.theme_manager.colors
        
        # Основные теги для разных типов сообщений
        self.text.tag_configure("info", foreground=colors["log_info"])
        self.text.tag_configure("success", foreground=colors["log_success"])
        self.text.tag_configure("warning", foreground=colors["log_warning"])
        self.text.tag_configure("error", foreground=colors["log_error"])
        self.text.tag_configure("debug", foreground=colors["disabled_fg"])
        self.text.tag_configure("system", foreground=colors["log_system"])
        
        # Дополнительные теги для форматирования
        self.text.tag_configure("bold", font=("Consolas", 9, "bold"))
        self.text.tag_configure("timestamp", foreground=colors["accent"])
        
        # Настройка фона для выделения
        self.text.tag_configure("highlight", background=colors["select_bg"])
    
    def log(self, message, level="info"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Определяем тег
        tag = level if level in ["info", "success", "warning", "error", "debug", "system"] else "info"
        
        # Вставляем временную метку с отдельным тегом
        self.text.insert(tk.END, f"[", "timestamp")
        self.text.insert(tk.END, timestamp, "timestamp bold")
        self.text.insert(tk.END, f"] ", "timestamp")
        
        # Вставляем сообщение с соответствующим тегом
        self.text.insert(tk.END, f"{message}\n", tag)
        
        # Прокрутка вниз
        self.text.see(tk.END)
        
        # Принудительное обновление
        self.text.update_idletasks()
    
    def clear(self):
        """Очистка лога"""
        self.text.delete(1.0, tk.END)
    
    def get_content(self):
        """Получение содержимого лога"""
        return self.text.get(1.0, tk.END)
    
    def update_theme(self):
        """Обновление темы"""
        colors = self.app.theme_manager.colors
        
        # Обновление цветов текстового поля
        self.text.config(
            bg=colors["log_bg"],
            fg=colors["log_fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"]
        )
        
        # Обновление тегов
        self._configure_tags()