"""
Виджет для отображения графика скорости
"""
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class SpeedChart(ttk.Frame):
    """Виджет графика скорости"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.speed_data = []
        self.time_data = []
        
        self._create_chart()
    
    def _create_chart(self):
        """Создание графика"""
        # Создание фигуры
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Настройка цветов
        self._apply_theme()
        
        # Создание холста
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _apply_theme(self):
        """Применение темы к графику"""
        colors = self.app.theme_manager.colors
        
        self.figure.patch.set_facecolor(colors["bg"])
        self.ax.set_facecolor(colors["bg"])
        
        self.ax.tick_params(colors=colors["fg"])
        self.ax.xaxis.label.set_color(colors["fg"])
        self.ax.yaxis.label.set_color(colors["fg"])
        self.ax.title.set_color(colors["fg"])
        
        for spine in self.ax.spines.values():
            spine.set_color(colors["fg"])
    
    def add_data_point(self, time_sec, speed_mb):
        """Добавление точки данных"""
        self.time_data.append(time_sec)
        self.speed_data.append(speed_mb)
        
        # Ограничиваем количество точек
        max_points = self.app.config.get("testing", {}).get("speed_chart_points", 100)
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.speed_data = self.speed_data[-max_points:]
        
        self._redraw()
    
    def _redraw(self):
        """Перерисовка графика"""
        self.ax.clear()
        self._apply_theme()
        
        if self.speed_data:
            self.ax.plot(self.time_data, self.speed_data, 'b-', linewidth=2)
            self.ax.fill_between(self.time_data, 0, self.speed_data, alpha=0.3)
            
            # Добавление средней линии
            if len(self.speed_data) > 0:
                avg_speed = sum(self.speed_data) / len(self.speed_data)
                self.ax.axhline(y=avg_speed, color='r', linestyle='--', alpha=0.7)
        
        self.ax.set_xlabel(self.app.i18n.get("time_sec", "Время (с)"))
        self.ax.set_ylabel(self.app.i18n.get("speed_mbs", "Скорость (MB/s)"))
        self.ax.set_title(self.app.i18n.get("speed_chart", "График скорости"))
        
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def clear(self):
        """Очистка графика"""
        self.time_data = []
        self.speed_data = []
        self._redraw()
    
    def update_theme(self):
        """Обновление темы"""
        self._apply_theme()
        self._redraw()