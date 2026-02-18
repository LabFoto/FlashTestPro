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
import matplotlib.font_manager as fm
import platform

class SpeedChart(ttk.Frame):
    """Виджет графика скорости"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.speed_data = []
        self.time_data = []
        
        # Настройка шрифтов для matplotlib
        self._setup_matplotlib_fonts()
        
        self._create_chart()
    
    def _setup_matplotlib_fonts(self):
        """Настройка шрифтов для matplotlib для поддержки разных языков"""
        system = platform.system()
        
        # Список шрифтов для разных ОС
        if system == "Windows":
            # Windows шрифты
            font_list = ['Segoe UI', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        elif system == "Linux":
            # Linux шрифты
            font_list = ['WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'DejaVu Sans']
        elif system == "Darwin":  # macOS
            font_list = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'DejaVu Sans']
        else:
            font_list = ['DejaVu Sans']
        
        # Пытаемся найти доступный шрифт
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        font_found = False
        
        for font in font_list:
            if font in available_fonts:
                plt.rcParams['font.family'] = font
                font_found = True
                break
        
        if not font_found:
            # Если ничего не найдено, используем шрифт по умолчанию и надеемся на лучшее
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # Настройка поддержки Unicode
        plt.rcParams['axes.unicode_minus'] = False
    
    def _create_chart(self):
        """Создание графика с уменьшенной высотой"""
        # Создание фигуры с уменьшенной высотой
        self.figure = Figure(figsize=(5, 2.5), dpi=100)
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
        
        # Локализация надписей с проверкой наличия перевода
        xlabel = self.app.i18n.get("time_sec", "Время (с)")
        ylabel = self.app.i18n.get("speed_mbs", "Скорость (MB/s)")
        title = self.app.i18n.get("speed_chart", "График скорости")
        
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        
        self.ax.grid(True, alpha=0.3)
        
        # Подавление предупреждений о шрифтах
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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
    
    def update_language(self):
        """Обновление языка"""
        # Перенастройка шрифтов при смене языка
        self._setup_matplotlib_fonts()
        self._redraw()