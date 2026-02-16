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
        # Текстовое поле для лога
        self.text = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=15
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
        
        self.text.tag_configure("info", foreground=colors["fg"])
        self.text.tag_configure("success", foreground=colors["success"])
        self.text.tag_configure("warning", foreground=colors["warning"])
        self.text.tag_configure("error", foreground=colors["error"])
        self.text.tag_configure("debug", foreground="#888888")
        self.text.tag_configure("system", foreground=colors["accent"])
    
    def log(self, message, level="info"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Определяем тег
        tag = level if level in ["info", "success", "warning", "error", "debug", "system"] else "info"
        
        # Вставляем сообщение
        self.text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        
        # Прокрутка вниз
        self.text.see(tk.END)
    
    def clear(self):
        """Очистка лога"""
        self.text.delete(1.0, tk.END)
    
    def get_content(self):
        """Получение содержимого лога"""
        return self.text.get(1.0, tk.END)
    
    def update_theme(self):
        """Обновление темы"""
        self._configure_tags()