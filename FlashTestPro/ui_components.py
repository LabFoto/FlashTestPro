"""
Модуль UI компонентов для SD Card Tester Pro
Содержит все классы, отвечающие за отображение
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import platform
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import locales

class Theme:
    """Класс управления темой и цветами"""
    
    DARK_THEME = {
        "bg_dark": "#1e1e1e",
        "bg_light": "#2d2d2d",
        "fg": "#ffffff",
        "accent": "#00bcd4",
        "success": "#4caf50",
        "warning": "#ff9800",
        "danger": "#f44336",
        "system_drive": "#ff5252",
        "removable_drive": "#4caf50",
        "network_drive": "#2196f3",
    }
    
    LIGHT_THEME = {
        "bg_dark": "#f5f5f5",
        "bg_light": "#ffffff",
        "fg": "#333333",
        "accent": "#2196f3",
        "success": "#4caf50",
        "warning": "#ff9800",
        "danger": "#f44336",
        "system_drive": "#ff5252",
        "removable_drive": "#4caf50",
        "network_drive": "#2196f3",
    }
    
    @classmethod
    def get_colors(cls, theme_name="dark"):
        """Получение цветовой схемы"""
        return cls.DARK_THEME if theme_name == "dark" else cls.LIGHT_THEME
    
    @classmethod
    def apply_style(cls, root, colors):
        """Применение стиля к корневому окну"""
        root.configure(bg=colors["bg_dark"])
        
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TLabel", background=colors["bg_dark"], foreground=colors["fg"])
        style.configure("TFrame", background=colors["bg_dark"])
        style.configure("TLabelframe", background=colors["bg_dark"], foreground=colors["accent"])
        style.configure("TLabelframe.Label", background=colors["bg_dark"], foreground=colors["accent"])
        
        style.configure("Accent.TButton", background=colors["accent"], foreground="white")
        style.configure("Danger.TButton", background=colors["danger"], foreground="white")
        
        return style


class DriveTreeView(ttk.Frame):
    """Компонент отображения списка дисков"""
    
    def __init__(self, parent, colors, on_select_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.on_select_callback = on_select_callback
        self.current_language = "ru"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        columns = ("drive", "type", "size", "filesystem")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=8,
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("drive", text=locales.get_translation(self.current_language, "drive", "Диск"))
        self.tree.heading("type", text=locales.get_translation(self.current_language, "type", "Тип"))
        self.tree.heading("size", text=locales.get_translation(self.current_language, "size", "Размер"))
        self.tree.heading("filesystem", text=locales.get_translation(self.current_language, "filesystem", "ФС"))
        
        self.tree.column("drive", width=100)
        self.tree.column("type", width=120)
        self.tree.column("size", width=120)
        self.tree.column("filesystem", width=100)
        
        self.tree.pack(fill="both", expand=True)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка событий
        if self.on_select_callback:
            self.tree.bind("<<TreeviewSelect>>", self.on_select_callback)
        
        # Контекстное меню
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self, tearoff=0, bg=self.colors["bg_light"], fg="white")
        self.context_menu.add_command(label="✏️ Переименовать")
        self.context_menu.add_command(label="🔄 Обновить")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 Свойства")
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Показать контекстное меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def update_drives(self, drives_list):
        """Обновление списка дисков"""
        # Очистка текущего списка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Добавление новых дисков
        for drive in drives_list:
            item_id = self.tree.insert(
                "",
                "end",
                values=(drive["path"], drive["type"], drive["size"], drive["fs"])
            )
            
            if drive.get("is_system", False):
                self.tree.tag_configure("system", background="#330000", foreground="white")
                self.tree.item(item_id, tags=("system",))
    
    def get_selected_drive(self):
        """Получение выбранного диска"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item["values"]
            tags = item.get("tags", [])
            
            return {
                "path": values[0],
                "type": values[1],
                "size": values[2],
                "fs": values[3],
                "is_system": "system" in tags,
                "item_id": selection[0]
            }
        return None
    
    def update_language(self, lang):
        """Обновление языка заголовков"""
        self.current_language = lang
        self.tree.heading("drive", text=locales.get_translation(lang, "drive", "Диск"))
        self.tree.heading("type", text=locales.get_translation(lang, "type", "Тип"))
        self.tree.heading("size", text=locales.get_translation(lang, "size", "Размер"))
        self.tree.heading("filesystem", text=locales.get_translation(lang, "filesystem", "ФС"))


class SpeedChart(ttk.Frame):
    """Компонент графика скорости"""
    
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.speed_data = []
        self.current_language = "ru"
        
        self._create_chart()
    
    def _create_chart(self):
        """Создание графика"""
        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=80)
        self.fig.patch.set_facecolor(self.colors["bg_light"])
        self.ax.set_facecolor(self.colors["bg_light"])
        
        self.ax.set_xlabel(locales.get_translation(self.current_language, "chart_xlabel", "Время (сек)"), 
                          color="white")
        self.ax.set_ylabel(locales.get_translation(self.current_language, "chart_ylabel", "Скорость (MB/s)"), 
                          color="white")
        self.ax.set_title(locales.get_translation(self.current_language, "chart_title", "График скорости записи"), 
                         color="white", pad=20)
        
        self.ax.tick_params(colors="white")
        for spine in self.ax.spines.values():
            spine.set_color("white")
        
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def update_data(self, time_sec, speed_mb):
        """Обновление данных графика"""
        self.speed_data.append((time_sec, speed_mb))
        
        # Ограничиваем количество точек
        if len(self.speed_data) > 100:  # Максимум 100 точек
            self.speed_data = self.speed_data[-100:]
        
        self._redraw()
    
    def _redraw(self):
        """Перерисовка графика"""
        self.ax.clear()
        
        if self.speed_data:
            times, speeds = zip(*self.speed_data)
            self.ax.plot(times, speeds, "b-", linewidth=2, label="Скорость записи")
            self.ax.fill_between(times, 0, speeds, alpha=0.3, color="blue")
            
            if len(speeds) > 0:
                avg_speed = sum(speeds) / len(speeds)
                self.ax.axhline(y=avg_speed, color="r", linestyle="--",
                              label=f"Средняя: {avg_speed:.1f} MB/s")
                
                max_speed = max(speeds)
                self.ax.axhline(y=max_speed, color="g", linestyle=":",
                              label=f"Макс: {max_speed:.1f} MB/s")
        
        self.ax.set_xlabel(locales.get_translation(self.current_language, "chart_xlabel", "Время (сек)"), 
                          color="white")
        self.ax.set_ylabel(locales.get_translation(self.current_language, "chart_ylabel", "Скорость (MB/s)"), 
                          color="white")
        self.ax.set_title(locales.get_translation(self.current_language, "chart_title", "График скорости записи"), 
                         color="white", pad=20)
        self.ax.legend(facecolor=self.colors["bg_light"], edgecolor="white", labelcolor="white")
        self.ax.tick_params(colors="white")
        
        for spine in self.ax.spines.values():
            spine.set_color("white")
        
        self.canvas.draw()
    
    def clear(self):
        """Очистка графика"""
        self.speed_data = []
        self.ax.clear()
        self.canvas.draw()
    
    def update_language(self, lang):
        """Обновление языка подписей"""
        self.current_language = lang
        self._redraw()


class LogViewer(ttk.Frame):
    """Компонент просмотра логов"""
    
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Текстовое поле для лога
        self.text = tk.Text(
            self,
            bg=self.colors["bg_light"],
            fg="white",
            font=("Consolas", 9),
            wrap="word",
            height=20
        )
        
        scrollbar = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        self.text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Настройка тегов для раскраски
        self.text.tag_configure("info", foreground="white")
        self.text.tag_configure("success", foreground="#4caf50")
        self.text.tag_configure("warning", foreground="#ff9800")
        self.text.tag_configure("error", foreground="#f44336")
        self.text.tag_configure("debug", foreground="#888888")
        self.text.tag_configure("system", foreground="#2196f3")
        self.text.tag_configure("critical", foreground="#ff0000", font=("Consolas", 10, "bold"))
    
    def log(self, message, level="info", timestamp=None):
        """Добавление сообщения в лог"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        tag = level if level in ["info", "success", "warning", "error", "debug", "system", "critical"] else "info"
        
        self.text.insert("end", f"[{timestamp}] {message}\n", tag)
        self.text.see("end")
    
    def clear(self):
        """Очистка лога"""
        self.text.delete("1.0", "end")
    
    def get_content(self):
        """Получение содержимого лога"""
        return self.text.get("1.0", "end-1c")
    
    def copy_to_clipboard(self, root):
        """Копирование в буфер обмена"""
        content = self.get_content()
        root.clipboard_clear()
        root.clipboard_append(content)


class StatisticsPanel(ttk.Frame):
    """Панель статистики"""
    
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.current_language = "ru"
        self.stats_vars = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ttk.Label(
            header_frame,
            text=locales.get_translation(self.current_language, "statistics", "📊 СТАТИСТИКА"),
            font=("Segoe UI", 14, "bold"),
            foreground=self.colors["accent"]
        ).pack(anchor="w")
        
        # Контейнер для статистики
        stats_container = ttk.Frame(scrollable_frame)
        stats_container.pack(fill="x", padx=20, pady=(0, 20))
        
        # Левая колонка
        left_stats = ttk.Frame(stats_container)
        left_stats.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Правая колонка
        right_stats = ttk.Frame(stats_container)
        right_stats.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Создаем переменные статистики
        stats_items = [
            ("stats_total_size", "total_size", left_stats),
            ("stats_tested", "tested", left_stats),
            ("stats_speed_avg", "avg_speed", left_stats),
            ("stats_speed_max", "max_speed", left_stats),
            ("stats_speed_min", "min_speed", left_stats),
            ("stats_time_total", "time_total", right_stats),
            ("stats_bad_sectors", "bad_sectors", right_stats),
            ("stats_passes_complete", "passes_complete", right_stats),
            ("stats_passes_remaining", "passes_remaining", right_stats),
            ("stats_status", "status", right_stats),
        ]
        
        for i, (key, var_name, parent_frame) in enumerate(stats_items):
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)
            
            ttk.Label(
                frame,
                text=locales.get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=22,
                anchor="w"
            ).pack(side="left")
            
            var = tk.StringVar(value="---")
            self.stats_vars[var_name] = var
            
            ttk.Label(
                frame,
                textvariable=var,
                font=("Segoe UI", 10, "bold"),
                foreground=self.colors["accent"],
                anchor="w"
            ).pack(side="left", padx=(10, 0))
        
        # Таблица битых секторов
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=20, pady=(0, 20))
        
        bad_header = ttk.Frame(scrollable_frame)
        bad_header.pack(fill="x", padx=20, pady=(0, 10))
        
        ttk.Label(
            bad_header,
            text="🔴 " + locales.get_translation(self.current_language, "stats_bad_sectors", "Битые сектора"),
            font=("Segoe UI", 12, "bold"),
            foreground=self.colors["danger"]
        ).pack(side="left")
        
        # Создаем таблицу битых секторов
        columns = ("sector", "status", "attempts")
        self.bad_sectors_tree = ttk.Treeview(
            scrollable_frame,
            columns=columns,
            show="headings",
            height=8
        )
        
        self.bad_sectors_tree.heading("sector", text="Сектор")
        self.bad_sectors_tree.heading("status", text="Статус")
        self.bad_sectors_tree.heading("attempts", text="Попыток")
        
        self.bad_sectors_tree.column("sector", width=150)
        self.bad_sectors_tree.column("status", width=150)
        self.bad_sectors_tree.column("attempts", width=120)
        
        self.bad_sectors_tree.pack(fill="x", padx=20, pady=(0, 20))
    
    def update_stat(self, name, value):
        """Обновление значения статистики"""
        if name in self.stats_vars:
            self.stats_vars[name].set(str(value))
    
    def update_all(self, stats):
        """Обновление всей статистики"""
        mapping = {
            'total_size': lambda v: f"{v:.1f} GB",
            'tested': lambda v: f"{v:.1f} GB",
            'avg_speed': lambda v: f"{v:.1f} MB/s",
            'max_speed': lambda v: f"{v:.1f} MB/s",
            'min_speed': lambda v: f"{v:.1f} MB/s",
            'time_total': lambda v: v,
            'bad_sectors': lambda v: str(v),
            'passes_complete': lambda v: str(v),
            'passes_remaining': lambda v: str(v),
            'status': lambda v: v,
        }
        
        for key, formatter in mapping.items():
            if key in stats and key in self.stats_vars:
                self.stats_vars[key].set(formatter(stats[key]))
    
    def add_bad_sector(self, sector, status, attempts):
        """Добавление битого сектора в таблицу"""
        self.bad_sectors_tree.insert("", "end", values=(sector, status, attempts))
    
    def clear_bad_sectors(self):
        """Очистка таблицы битых секторов"""
        for item in self.bad_sectors_tree.get_children():
            self.bad_sectors_tree.delete(item)
    
    def reset(self):
        """Сброс статистики"""
        for var in self.stats_vars.values():
            var.set("---")
        self.clear_bad_sectors()
    
    def update_language(self, lang):
        """Обновление языка"""
        self.current_language = lang
        # TODO: Обновить заголовки


class InfoPanel(ttk.Frame):
    """Панель информации о системе"""
    
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.current_language = "ru"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Canvas для прокрутки
        canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Контейнер с отступами
        info_container = ttk.Frame(scrollable_frame)
        info_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Информация о системе
        self._create_system_info_section(info_container)
        
        # Информация о программе
        self._create_about_section(info_container)
        
        # Кнопки
        self._create_buttons(info_container)
        
        # Копирайт
        self._create_copyright(info_container)
    
    def _create_system_info_section(self, parent):
        """Создание секции системной информации"""
        system_frame = ttk.LabelFrame(
            parent,
            text=" " + locales.get_translation(self.current_language, "system_info", "💻 ИНФОРМАЦИЯ О СИСТЕМЕ") + " ",
            padding=20
        )
        system_frame.pack(fill="x", pady=(0, 20))
        
        self.system_labels = {}
        sys_container = ttk.Frame(system_frame)
        sys_container.pack(fill="x")
        
        left_sys = ttk.Frame(sys_container)
        left_sys.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        right_sys = ttk.Frame(sys_container)
        right_sys.pack(side="right", fill="both", expand=True, padx=(20, 0))
        
        sys_keys = [
            ("system_os", "os", left_sys),
            ("system_python", "python", left_sys),
            ("system_architecture", "architecture", left_sys),
            ("system_processor", "processor", left_sys),
            ("system_memory", "memory", right_sys),
            ("system_disks", "disks", right_sys),
            ("system_uptime", "uptime", right_sys),
            ("system_hostname", "hostname", right_sys),
            ("system_admin", "admin", right_sys),
        ]
        
        for key, var_name, parent_frame in sys_keys:
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)
            
            ttk.Label(
                frame,
                text=locales.get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=20,
                anchor="w"
            ).pack(side="left")
            
            var = tk.StringVar(value="---")
            self.system_labels[var_name] = var
            
            ttk.Label(
                frame,
                textvariable=var,
                font=("Segoe UI", 10),
                foreground=self.colors["accent"],
                anchor="w",
                wraplength=250
            ).pack(side="left", padx=(10, 0))
    
    def _create_about_section(self, parent):
        """Создание секции о программе"""
        about_frame = ttk.LabelFrame(
            parent,
            text=" " + locales.get_translation(self.current_language, "about_program", "ℹ️ О ПРОГРАММЕ") + " ",
            padding=20
        )
        about_frame.pack(fill="x", pady=(0, 20))
        
        about_container = ttk.Frame(about_frame)
        about_container.pack(fill="x")
        
        left_about = ttk.Frame(about_container)
        left_about.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        right_about = ttk.Frame(about_container)
        right_about.pack(side="right", fill="both", expand=True, padx=(20, 0))
        
        self.about_labels = {}
        app_keys = [
            ("program_version", "version", left_about),
            ("program_author", "author", left_about),
            ("program_license", "license", right_about),
            ("program_github", "github", right_about),
            ("program_build", "build", right_about),
        ]
        
        for key, var_name, parent_frame in app_keys:
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)
            
            ttk.Label(
                frame,
                text=locales.get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=20,
                anchor="w"
            ).pack(side="left")
            
            var = tk.StringVar(value="---")
            self.about_labels[var_name] = var
            
            ttk.Label(
                frame,
                textvariable=var,
                font=("Segoe UI", 10),
                foreground=self.colors["accent"],
                anchor="w",
                wraplength=250
            ).pack(side="left", padx=(10, 0))
    
    def _create_buttons(self, parent):
        """Создание кнопок"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(20, 0))
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        self.buttons = {}
        
        btn_configs = [
            ("btn_documentation", "📖", "documentation", 0, 0),
            ("btn_check_updates", "🔄", "check_updates", 0, 1),
            ("btn_report_bug", "🐛", "report_bug", 1, 0),
            ("btn_error_log", "📋", "error_log", 1, 1),
        ]
        
        for key, icon, name, row, col in btn_configs:
            btn = tk.Button(
                button_frame,
                text=f"{icon} {locales.get_translation(self.current_language, key, key.replace('_', ' ').title())}",
                bg=self.colors["bg_light"],
                fg="white",
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2"
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            self.buttons[name] = btn
    
    def _create_copyright(self, parent):
        """Создание копирайта"""
        copyright_frame = ttk.Frame(parent)
        copyright_frame.pack(fill="x", pady=(30, 0))
        
        self.copyright_label = ttk.Label(
            copyright_frame,
            text="© 2024 SD Card Tester Pro. Все права защищены.",
            font=("Segoe UI", 9),
            foreground="#888888"
        )
        self.copyright_label.pack()
        
        self.warning_label = ttk.Label(
            copyright_frame,
            text=locales.get_translation(self.current_language, "warning_admin_short", 
                                        "Для полного доступа запустите от администратора/root"),
            font=("Segoe UI", 9, "italic"),
            foreground=self.colors["warning"]
        )
        self.warning_label.pack(pady=(5, 0))
    
    def update_system_info(self, sys_info):
        """Обновление системной информации"""
        if 'os' in sys_info:
            self.system_labels['os'].set(sys_info['os'])
        if 'python' in sys_info:
            self.system_labels['python'].set(sys_info['python'])
        if 'architecture' in sys_info:
            self.system_labels['architecture'].set(sys_info['architecture'])
        if 'processor' in sys_info:
            self.system_labels['processor'].set(sys_info['processor'])
        if 'memory' in sys_info:
            self.system_labels['memory'].set(sys_info['memory'])
        if 'disks' in sys_info:
            self.system_labels['disks'].set(str(sys_info['disks']))
        if 'uptime' in sys_info:
            self.system_labels['uptime'].set(sys_info['uptime'])
        if 'hostname' in sys_info:
            self.system_labels['hostname'].set(sys_info['hostname'])
        if 'is_admin' in sys_info:
            admin_status = "Да" if sys_info['is_admin'] else "Нет (рекомендуется запуск от администратора)"
            self.system_labels['admin'].set(admin_status)
    
    def update_about_info(self, version="1.0.0", author="SD Card Tester Team", 
                         license="MIT", github="github.com/yourusername/sd-card-tester-pro"):
        """Обновление информации о программе"""
        self.about_labels['version'].set(version)
        self.about_labels['author'].set(author)
        self.about_labels['license'].set(license)
        self.about_labels['github'].set(github)
        self.about_labels['build'].set(datetime.now().strftime("%Y-%m-%d"))
    
    def update_language(self, lang):
        """Обновление языка"""
        self.current_language = lang
        # TODO: Обновить все тексты


class ProgressPanel(ttk.LabelFrame):
    """Панель прогресса тестирования"""
    
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.current_language = "ru"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        self.config(text=" " + locales.get_translation(self.current_language, "progress", "ПРОГРЕСС") + " ")
        self.configure(padding=15)
        
        self.status_label = ttk.Label(
            self,
            text=locales.get_translation(self.current_language, "waiting", "Ожидание начала теста..."),
            font=("Segoe UI", 10),
            wraplength=350
        )
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(self, length=350, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(5, 0))
        
        self.time_label = ttk.Label(
            self,
            text=locales.get_translation(self.current_language, "time_remaining", "Осталось: --:--:--"),
            font=("Segoe UI", 9)
        )
        self.time_label.pack(anchor="w", pady=(5, 0))
        
        self.detail_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 8),
            foreground="#888888"
        )
        self.detail_label.pack(anchor="w", pady=(5, 0))
    
    def update_progress(self, value, max_value=100):
        """Обновление прогресса"""
        self.progress_bar["value"] = value
        self.progress_bar["maximum"] = max_value
    
    def update_status(self, status):
        """Обновление статуса"""
        self.status_label.config(text=status)
    
    def update_time(self, remaining_str):
        """Обновление оставшегося времени"""
        self.time_label.config(text=f"{locales.get_translation(self.current_language, 'remaining', 'Осталось')}: {remaining_str}")
    
    def update_detail(self, detail):
        """Обновление детальной информации"""
        self.detail_label.config(text=detail)
    
    def reset(self):
        """Сброс прогресса"""
        self.progress_bar["value"] = 0
        self.status_label.config(text=locales.get_translation(self.current_language, "waiting", "Ожидание начала теста..."))
        self.time_label.config(text=locales.get_translation(self.current_language, "time_remaining", "Осталось: --:--:--"))
        self.detail_label.config(text="")
    
    def update_language(self, lang):
        """Обновление языка"""
        self.current_language = lang
        self.config(text=" " + locales.get_translation(lang, "progress", "ПРОГРЕСС") + " ")
        self.status_label.config(text=locales.get_translation(lang, "waiting", "Ожидание начала теста..."))
        self.time_label.config(text=locales.get_translation(lang, "time_remaining", "Осталось: --:--:--"))


class TestSettingsPanel(ttk.LabelFrame):
    """Панель настроек теста"""
    
    def __init__(self, parent, colors, on_start_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.on_start_callback = on_start_callback
        self.current_language = "ru"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        self.config(text=" " + locales.get_translation(self.current_language, "test_settings", "НАСТРОЙКИ ТЕСТА") + " ")
        self.configure(padding=15)
        
        # Кнопка переименования
        self.rename_button = ttk.Button(
            self,
            text=locales.get_translation(self.current_language, "rename", "✏️ Переименовать диск"),
            width=30
        )
        self.rename_button.pack(anchor="center", pady=(0, 10))
        
        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=(0, 10))
        
        # Количество проходов
        self.passes_label = ttk.Label(
            self,
            text=locales.get_translation(self.current_language, "passes_label", "Количество проходов:")
        )
        self.passes_label.pack(anchor="w")
        
        self.passes_var = tk.IntVar(value=1)
        passes_frame = ttk.Frame(self)
        passes_frame.pack(fill="x", pady=(5, 10))
        
        self.fast_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=locales.get_translation(self.current_language, "fast_pass", "Быстрый (1 проход)"),
            variable=self.passes_var, value=1
        )
        self.fast_pass_radio.pack(anchor="w", pady=2)
        
        self.standard_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=locales.get_translation(self.current_language, "standard_pass", "Стандартный (3 прохода)"),
            variable=self.passes_var, value=3
        )
        self.standard_pass_radio.pack(anchor="w", pady=2)
        
        self.full_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=locales.get_translation(self.current_language, "full_pass", "Полный (7 проходов)"),
            variable=self.passes_var, value=7
        )
        self.full_pass_radio.pack(anchor="w", pady=2)
        
        custom_frame = ttk.Frame(passes_frame)
        custom_frame.pack(anchor="w", pady=(5, 0))
        
        self.or_label = ttk.Label(
            custom_frame,
            text=locales.get_translation(self.current_language, "or_label", "или:")
        )
        self.or_label.pack(side="left")
        
        self.custom_passes_var = tk.StringVar(value="")
        custom_entry = ttk.Entry(
            custom_frame, textvariable=self.custom_passes_var, width=6
        )
        custom_entry.pack(side="left", padx=(5, 0))
        
        self.passes_suffix_label = ttk.Label(
            custom_frame,
            text=locales.get_translation(self.current_language, "passes_suffix", "проходов")
        )
        self.passes_suffix_label.pack(side="left", padx=(2, 0))
        
        # Типы тестов
        test_types_frame = ttk.LabelFrame(self, text=" Типы тестов ", padding=10)
        test_types_frame.pack(fill="x", pady=(5, 10))
        
        self.test_write_ones = tk.BooleanVar(value=False)
        self.test_write_zeros = tk.BooleanVar(value=False)
        self.test_random = tk.BooleanVar(value=False)
        self.test_verify = tk.BooleanVar(value=False)
        
        self.test_ones_check = ttk.Checkbutton(
            test_types_frame,
            text=locales.get_translation(self.current_language, "test_ones", "Запись единиц (0xFF)"),
            variable=self.test_write_ones,
        )
        self.test_ones_check.pack(anchor="w", pady=2)
        
        self.test_zeros_check = ttk.Checkbutton(
            test_types_frame,
            text=locales.get_translation(self.current_language, "test_zeros", "Запись нулей (0x00)"),
            variable=self.test_write_zeros,
        )
        self.test_zeros_check.pack(anchor="w", pady=2)
        
        self.test_random_check = ttk.Checkbutton(
            test_types_frame,
            text=locales.get_translation(self.current_language, "test_random", "Случайные данные"),
            variable=self.test_random,
        )
        self.test_random_check.pack(anchor="w", pady=2)
        
        self.test_verify_check = ttk.Checkbutton(
            test_types_frame,
            text=locales.get_translation(self.current_language, "test_verify", "Проверка после записи"),
            variable=self.test_verify,
        )
        self.test_verify_check.pack(anchor="w", pady=2)
        
        # Форматирование
        format_frame = ttk.LabelFrame(self, text=" Форматирование ", padding=10)
        format_frame.pack(fill="x", pady=(0, 10))
        
        self.format_var = tk.BooleanVar(value=False)
        self.format_check = ttk.Checkbutton(
            format_frame,
            text=locales.get_translation(self.current_language, "format_after", "Форматировать после теста"),
            variable=self.format_var
        )
        self.format_check.pack(anchor="w", pady=2)
        
        fs_frame = ttk.Frame(format_frame)
        fs_frame.pack(fill="x", pady=(5, 0))
        
        self.fs_label = ttk.Label(
            fs_frame,
            text=locales.get_translation(self.current_language, "filesystem", "Файловая система:")
        )
        self.fs_label.pack(side="left", padx=(0, 10))
        
        self.fs_var = tk.StringVar(value="FAT32")
        self.fs_combo = ttk.Combobox(
            fs_frame,
            textvariable=self.fs_var,
            values=["FAT32", "exFAT", "NTFS", "EXT4", "Don't format"],
            state="readonly",
            width=15,
        )
        self.fs_combo.pack(side="left")
    
    def get_test_params(self):
        """Получение параметров теста"""
        try:
            if self.custom_passes_var.get() and self.custom_passes_var.get().isdigit():
                passes = int(self.custom_passes_var.get())
                if passes < 1 or passes > 100:
                    passes = 1
            else:
                passes = self.passes_var.get()
        except:
            passes = 1
        
        return {
            'passes': passes,
            'test_ones': self.test_write_ones.get(),
            'test_zeros': self.test_write_zeros.get(),
            'test_random': self.test_random.get(),
            'test_verify': self.test_verify.get(),
            'auto_format': self.format_var.get(),
            'filesystem': self.fs_var.get(),
        }
    
    def validate_params(self):
        """Проверка параметров"""
        try:
            if self.custom_passes_var.get() and self.custom_passes_var.get().isdigit():
                passes = int(self.custom_passes_var.get())
                if passes < 1 or passes > 100:
                    return False, "Некорректное количество проходов. Введите число от 1 до 100."
        except:
            return False, "Некорректное количество проходов."
        
        if not (self.test_write_ones.get() or self.test_write_zeros.get() or self.test_random.get()):
            return False, "Выберите хотя бы один тип теста!"
        
        return True, "OK"
    
    def set_passes(self, passes):
        """Установка количества проходов"""
        self.passes_var.set(passes)
        self.custom_passes_var.set("")
    
    def update_language(self, lang):
        """Обновление языка"""
        self.current_language = lang
        self.config(text=" " + locales.get_translation(lang, "test_settings", "НАСТРОЙКИ ТЕСТА") + " ")
        self.rename_button.config(text=locales.get_translation(lang, "rename", "✏️ Переименовать диск"))
        self.passes_label.config(text=locales.get_translation(lang, "passes_label", "Количество проходов:"))
        self.fast_pass_radio.config(text=locales.get_translation(lang, "fast_pass", "Быстрый (1 проход)"))
        self.standard_pass_radio.config(text=locales.get_translation(lang, "standard_pass", "Стандартный (3 прохода)"))
        self.full_pass_radio.config(text=locales.get_translation(lang, "full_pass", "Полный (7 проходов)"))
        self.or_label.config(text=locales.get_translation(lang, "or_label", "или:"))
        self.passes_suffix_label.config(text=locales.get_translation(lang, "passes_suffix", "проходов"))
        self.test_ones_check.config(text=locales.get_translation(lang, "test_ones", "Запись единиц (0xFF)"))
        self.test_zeros_check.config(text=locales.get_translation(lang, "test_zeros", "Запись нулей (0x00)"))
        self.test_random_check.config(text=locales.get_translation(lang, "test_random", "Случайные данные"))
        self.test_verify_check.config(text=locales.get_translation(lang, "test_verify", "Проверка после записи"))
        self.format_check.config(text=locales.get_translation(lang, "format_after", "Форматировать после теста"))
        self.fs_label.config(text=locales.get_translation(lang, "filesystem", "Файловая система:"))