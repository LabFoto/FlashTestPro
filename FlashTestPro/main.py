import os
import platform
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import sys
import time
import psutil
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json
import webbrowser
import locales
from locales import get_translation, get_available_languages
from error_logger import get_logger, log_errors, ErrorContext

class ErrorReportDialog:
    """Диалог просмотра ошибок"""

    def __init__(self, parent, logger):
        self.parent = parent
        self.logger = logger
        self.dialog = None
        self.create_dialog()

    def create_dialog(self):
        """Создание диалога"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Журнал ошибок")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg="#1e1e1e")

        # Центрирование
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Заголовок
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            title_frame,
            text="📋 Журнал ошибок и предупреждений",
            font=("Segoe UI", 14, "bold"),
            foreground="#00bcd4"
        ).pack(side="left")

        # Статистика
        stats = self.logger.get_error_statistics()
        stats_frame = ttk.LabelFrame(self.dialog, text=" Статистика ", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Общая статистика
        stats_text = f"""
            Всего ошибок: {stats['total_errors']}
            Всего предупреждений: {stats['total_warnings']}
        """
        ttk.Label(stats_frame, text=stats_text, justify="left").pack(anchor="w")

        # Топ ошибок по типу
        if stats['errors_by_type']:
            ttk.Label(stats_frame, text="\nЧастые ошибки:",
                      font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
            for error, count in list(stats['errors_by_type'].items())[:5]:  # Показываем только топ-5
                ttk.Label(stats_frame, text=f"  • {error}: {count}",
                          foreground="#f44336").pack(anchor="w")

        # Топ модулей с ошибками
        if stats['errors_by_module']:
            ttk.Label(stats_frame, text="\nМодули с ошибками:",
                      font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 2))
            for module, count in list(stats['errors_by_module'].items())[:5]:  # Топ-5
                ttk.Label(stats_frame, text=f"  • {module}: {count}",
                          foreground="#ff9800").pack(anchor="w")

    def load_errors(self):
        """Загрузка ошибок в текстовое поле"""
        self.log_text.delete("1.0", "end")
        errors = self.logger.get_recent_errors(100)

        if errors:
            for error in errors:
                # Раскрашиваем в зависимости от уровня
                if "ERROR" in error:
                    self.log_text.insert("end", error, "error")
                    self.log_text.tag_configure("error", foreground="#f44336")
                elif "WARNING" in error:
                    self.log_text.insert("end", error, "warning")
                    self.log_text.tag_configure("warning", foreground="#ff9800")
                elif "CRITICAL" in error:
                    self.log_text.insert("end", error, "critical")
                    self.log_text.tag_configure("critical", foreground="#ff0000", font=("Consolas", 10, "bold"))
                else:
                    self.log_text.insert("end", error)
        else:
            self.log_text.insert("end", "Ошибок не найдено\n")

    def clear_old_logs(self):
        """Очистка старых логов"""
        if messagebox.askyesno("Подтверждение", "Удалить логи старше 7 дней?"):
            self.logger.clear_old_logs(7)
            self.load_errors()
            messagebox.showinfo("Готово", "Старые логи удалены")

    def open_logs_folder(self):
        """Открытие папки с логами"""
        import subprocess
        import os
        log_dir = os.path.abspath("logs")

        if platform.system() == "Windows":
            os.startfile(log_dir)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", log_dir])
        else:  # Linux
            subprocess.run(["xdg-open", log_dir])

# Глобальный логгер
error_logger = get_logger()

class AdvancedSDCardTester:
    def __init__(self):
        self.stat_speed_avg = None
        self.root = tk.Tk()
        self.root.title("SD Card Tester Pro")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)

        # Локализация
        self.current_language = "ru"
        self.translations = locales.TRANSLATIONS

        # Очередь для обмена данными
        self.message_queue = queue.Queue()

        # Переменные состояния
        self.test_running = False
        self.test_paused = False
        self.cancel_requested = False

        # Данные тестирования
        self.speed_data = []
        self.bad_sectors = []
        self.test_start_time = None
        self.current_pass = 0
        self.total_passes = 1
        self.current_position = 0
        self.total_size = 0

        # Конфигурация
        self.config = self.load_config()

        # Стили и цвета
        self.setup_styles()

        # Иконка (если есть)
        self.setup_icon()

        # Создание интерфейса
        self.create_widgets()

        # Запуск проверки очереди
        self.check_queue()

        # Проверка прав администратора
        self.check_admin_permissions()

    def open_settings(self):
        """Открытие окна настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.colors["bg_dark"])

        # Центрирование окна
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f"{width}x{height}+{x}+{y}")

        # Вкладки настроек
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Общие настройки
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Общие")

        # Настройки тестирования
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="Тестирование")

        # Кнопки
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Сохранить",
            command=lambda: self.save_settings(settings_window),
        ).pack(side="right", padx=(5, 0))

        ttk.Button(button_frame, text="Отмена", command=settings_window.destroy).pack(
            side="right"
        )

    def save_settings(self, window):
        """Сохранение настроек"""
        self.save_config()
        self.log_message("Настройки сохранены", "success")
        window.destroy()

    def open_documentation(self):
        """Открытие документации"""
        try:
            webbrowser.open("https://github.com/yourusername/sd-card-tester-pro/wiki")
        except:
            self.log_message("Не удалось открыть документацию", "warning")

    def show_about(self):
        """Показать информацию о программе"""
        about_text = f"""
    SD Card Tester Pro v1.0
    
    Профессиональный инструмент для тестирования 
    карт памяти и других накопителей.
    
    Автор: SD Card Tester Team
    Лицензия: MIT
    
    ОС: {platform.system()} {platform.release()}
    Python: {platform.python_version()}
    
    © 2024 Все права защищены.
    """
        messagebox.showinfo("О программе", about_text)

    def check_for_updates(self):
        """Проверка обновлений"""
        self.log_message("Проверка обновлений...", "info")
        # TODO: Реализовать проверку через GitHub API
        self.root.after(2000, lambda: self.log_message("Обновлений не найдено", "info"))

    def report_bug(self):
        """Сообщить об ошибке"""
        try:
            webbrowser.open("https://github.com/yourusername/sd-card-tester-pro/issues/new")
            self.log_message("Открыта страница отчетов об ошибках", "info")
        except:
            self.log_message(
                "Не удалось открыть страницу отчетов об ошибках", "warning"
            )

    def load_config(self):
        """Загрузка конфигурации из файла"""
        default_config = {
            "app": {
                "name": "SD Card Tester Pro",
                "version": "1.0.0",
                "auto_save_log": True,
                "auto_update_stats": True,
            },
            "testing": {
                "default_passes": 1,
                "chunk_size_mb": 1024,
                "test_patterns": [],
                "verify_read": False,
                "auto_format": False,
                "default_filesystem": "FAT32",
            },
            "ui": {
                "theme": "dark",
                "language": "ru",
                "chart_points": 100,
                "font_size": 9,
                "show_warnings": True,
            },
        }

        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self.merge_configs(default_config, user_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")

        return default_config

    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Главное меню
        self.create_menu()

        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ========== ЛЕВАЯ ПАНЕЛЬ С ПРОКРУТКОЙ ==========
        # Создаем Canvas и Scrollbar для левой панели
        left_canvas = tk.Canvas(
            main_container,
            bg=self.colors["bg_dark"],
            highlightthickness=0,
            width=800  # Увеличена ширина в 2 раза
        )
        left_scrollbar = ttk.Scrollbar(
            main_container,
            orient="vertical",
            command=left_canvas.yview
        )
        left_scrollable_frame = ttk.Frame(left_canvas)

        left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )

        left_canvas.create_window((0, 0), window=left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        # Упаковываем левую панель
        left_canvas.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_scrollbar.pack(side="left", fill="y")

        # Правая панель - графики и статистика
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)

        # ========== ЛЕВАЯ ПАНЕЛЬ - СОДЕРЖИМОЕ ==========

        # Заголовок
        header_frame = ttk.Frame(left_scrollable_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        self.main_title_label = ttk.Label(
            header_frame,
            text=get_translation(self.current_language, "main_title", "🔧 SD CARD TESTER PRO"),
            font=("Segoe UI", 20, "bold"),
            foreground=self.colors["accent"],
        )
        self.main_title_label.pack(anchor="w")

        self.subtitle_label = ttk.Label(
            header_frame,
            text=get_translation(self.current_language, "subtitle", "Профессиональное тестирование накопителей"),
            font=("Segoe UI", 10),
        )
        self.subtitle_label.pack(anchor="w")

        # Выбор языка
        language_frame = ttk.Frame(left_scrollable_frame)
        language_frame.pack(fill="x", pady=(0, 15))

        self.language_label = ttk.Label(
            language_frame,
            text=get_translation(self.current_language, "language", "Язык / Language / 语言:")
        )
        self.language_label.pack(side="left", padx=(0, 10))

        self.language_var = tk.StringVar(value=self.current_language)
        self.language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=["ru", "en", "zh"],
            state="readonly",
            width=10,
        )
        self.language_combo.pack(side="right")
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # Выбор диска
        self.drive_frame = ttk.LabelFrame(
            left_scrollable_frame,
            text=" " + get_translation(self.current_language, "drive_selection", "ВЫБОР НАКОПИТЕЛЯ") + " ",
            padding=15
        )
        self.drive_frame.pack(fill="x", pady=(0, 15))

        self.refresh_button = ttk.Button(
            self.drive_frame,
            text=get_translation(self.current_language, "refresh_list", "🔄 Обновить список"),
            command=self.refresh_drives_list,
            width=25,
        )
        self.refresh_button.pack(pady=(0, 10))

        # Treeview для дисков
        columns = ("drive", "type", "size", "filesystem")
        self.drive_tree = ttk.Treeview(
            self.drive_frame,
            columns=columns,
            show="headings",
            height=8,
            selectmode="browse",
        )

        # Настройка колонок
        self.drive_tree.heading("drive", text=get_translation(self.current_language, "drive", "Диск"))
        self.drive_tree.heading("type", text=get_translation(self.current_language, "type", "Тип"))
        self.drive_tree.heading("size", text=get_translation(self.current_language, "size", "Размер"))
        self.drive_tree.heading("filesystem", text=get_translation(self.current_language, "filesystem", "ФС"))

        self.drive_tree.column("drive", width=100)
        self.drive_tree.column("type", width=120)
        self.drive_tree.column("size", width=120)
        self.drive_tree.column("filesystem", width=100)

        self.drive_tree.pack(fill="x")

        scrollbar = ttk.Scrollbar(
            self.drive_frame, orient="vertical", command=self.drive_tree.yview
        )
        self.drive_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Информация о выбранном диске
        info_frame = ttk.Frame(self.drive_frame)
        info_frame.pack(fill="x", pady=(10, 0))

        self.drive_info_label = ttk.Label(
            info_frame,
            text=get_translation(self.current_language, "select_drive", "Выберите накопитель для тестирования"),
            font=("Segoe UI", 9),
            foreground=self.colors["warning"],
            wraplength=350
        )
        self.drive_info_label.pack(anchor="w")

        self.drive_tree.bind("<<TreeviewSelect>>", self.on_drive_select)

        # ========== НАСТРОЙКИ ТЕСТА ==========
        self.settings_frame = ttk.LabelFrame(
            left_scrollable_frame,
            text=" " + get_translation(self.current_language, "test_settings", "НАСТРОЙКИ ТЕСТА") + " ",
            padding=15
        )
        self.settings_frame.pack(fill="x", pady=(0, 15))

        # КНОПКА ПЕРЕИМЕНОВАНИЯ
        rename_button_frame = ttk.Frame(self.settings_frame)
        rename_button_frame.pack(fill="x", pady=(0, 10))

        self.rename_button = ttk.Button(
            rename_button_frame,
            text=get_translation(self.current_language, "rename", "✏️ Переименовать диск"),
            command=self.rename_drive,
            width=30,
        )
        self.rename_button.pack(anchor="center")

        ttk.Separator(self.settings_frame, orient='horizontal').pack(fill='x', pady=(0, 10))

        # Количество проходов
        self.passes_label = ttk.Label(
            self.settings_frame,
            text=get_translation(self.current_language, "passes_label", "Количество проходов:")
        )
        self.passes_label.pack(anchor="w")

        self.passes_var = tk.IntVar(value=self.config["testing"]["default_passes"])
        passes_frame = ttk.Frame(self.settings_frame)
        passes_frame.pack(fill="x", pady=(5, 10))

        self.fast_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=get_translation(self.current_language, "fast_pass", "Быстрый (1 проход)"),
            variable=self.passes_var, value=1
        )
        self.fast_pass_radio.pack(anchor="w", pady=2)

        self.standard_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=get_translation(self.current_language, "standard_pass", "Стандартный (3 прохода)"),
            variable=self.passes_var, value=3
        )
        self.standard_pass_radio.pack(anchor="w", pady=2)

        self.full_pass_radio = ttk.Radiobutton(
            passes_frame,
            text=get_translation(self.current_language, "full_pass", "Полный (7 проходов)"),
            variable=self.passes_var, value=7
        )
        self.full_pass_radio.pack(anchor="w", pady=2)

        custom_frame = ttk.Frame(passes_frame)
        custom_frame.pack(anchor="w", pady=(5, 0))

        self.or_label = ttk.Label(
            custom_frame,
            text=get_translation(self.current_language, "or_label", "или:")
        )
        self.or_label.pack(side="left")

        self.custom_passes_var = tk.StringVar(value="")
        custom_entry = ttk.Entry(
            custom_frame, textvariable=self.custom_passes_var, width=6
        )
        custom_entry.pack(side="left", padx=(5, 0))

        self.passes_suffix_label = ttk.Label(
            custom_frame,
            text=get_translation(self.current_language, "passes_suffix", "проходов")
        )
        self.passes_suffix_label.pack(side="left", padx=(2, 0))

        # Типы тестов
        test_types_frame = ttk.LabelFrame(self.settings_frame, text=" Типы тестов ", padding=10)
        test_types_frame.pack(fill="x", pady=(5, 10))

        self.test_write_ones = tk.BooleanVar(value=False)
        self.test_write_zeros = tk.BooleanVar(value=False)
        self.test_random = tk.BooleanVar(value=False)
        self.test_verify = tk.BooleanVar(value=False)

        self.test_ones_check = ttk.Checkbutton(
            test_types_frame,
            text=get_translation(self.current_language, "test_ones", "Запись единиц (0xFF)"),
            variable=self.test_write_ones,
        )
        self.test_ones_check.pack(anchor="w", pady=2)

        self.test_zeros_check = ttk.Checkbutton(
            test_types_frame,
            text=get_translation(self.current_language, "test_zeros", "Запись нулей (0x00)"),
            variable=self.test_write_zeros,
        )
        self.test_zeros_check.pack(anchor="w", pady=2)

        self.test_random_check = ttk.Checkbutton(
            test_types_frame,
            text=get_translation(self.current_language, "test_random", "Случайные данные"),
            variable=self.test_random,
        )
        self.test_random_check.pack(anchor="w", pady=2)

        self.test_verify_check = ttk.Checkbutton(
            test_types_frame,
            text=get_translation(self.current_language, "test_verify", "Проверка после записи"),
            variable=self.test_verify,
        )
        self.test_verify_check.pack(anchor="w", pady=2)

        # Форматирование
        format_frame = ttk.LabelFrame(self.settings_frame, text=" Форматирование ", padding=10)
        format_frame.pack(fill="x", pady=(0, 10))

        self.format_var = tk.BooleanVar(value=False)
        self.format_check = ttk.Checkbutton(
            format_frame,
            text=get_translation(self.current_language, "format_after", "Форматировать после теста"),
            variable=self.format_var
        )
        self.format_check.pack(anchor="w", pady=2)

        fs_frame = ttk.Frame(format_frame)
        fs_frame.pack(fill="x", pady=(5, 0))

        self.fs_label = ttk.Label(
            fs_frame,
            text=get_translation(self.current_language, "filesystem", "Файловая система:")
        )
        self.fs_label.pack(side="left", padx=(0, 10))

        self.fs_var = tk.StringVar(value=self.config["testing"]["default_filesystem"])
        self.fs_combo = ttk.Combobox(
            fs_frame,
            textvariable=self.fs_var,
            values=["FAT32", "exFAT", "NTFS", "EXT4", "Don't format"],
            state="readonly",
            width=15,
        )
        self.fs_combo.pack(side="left")

        # Управление тестом
        control_frame = ttk.Frame(left_scrollable_frame)
        control_frame.pack(fill="x", pady=(0, 15))

        self.start_button = tk.Button(
            control_frame,
            text=get_translation(self.current_language, "start_test", "🚀 НАЧАТЬ"),
            command=self.start_test,
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            height=2,
            width=20,
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.pause_button = tk.Button(
            control_frame,
            text=get_translation(self.current_language, "pause", "⏸ ПАУЗА"),
            command=self.pause_test,
            bg="#555555",
            fg="white",
            font=("Segoe UI", 11),
            relief="flat",
            state="disabled",
            width=12,
        )
        self.pause_button.pack(side="left", padx=(0, 10))

        self.stop_button = tk.Button(
            control_frame,
            text=get_translation(self.current_language, "stop", "⏹ ОСТАНОВИТЬ"),
            command=self.stop_test,
            bg=self.colors["danger"],
            fg="white",
            font=("Segoe UI", 11),
            relief="flat",
            state="disabled",
            width=12,
        )
        self.stop_button.pack(side="left")

        # Прогресс
        self.progress_frame = ttk.LabelFrame(
            left_scrollable_frame,
            text=" " + get_translation(self.current_language, "progress", "ПРОГРЕСС") + " ",
            padding=15
        )
        self.progress_frame.pack(fill="x", pady=(0, 15))

        self.progress_label = ttk.Label(
            self.progress_frame,
            text=get_translation(self.current_language, "waiting", "Ожидание начала теста..."),
            font=("Segoe UI", 10),
            wraplength=350
        )
        self.progress_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, length=350, mode="determinate"
        )
        self.progress_bar.pack(fill="x", pady=(5, 0))

        self.time_label = ttk.Label(
            self.progress_frame,
            text=get_translation(self.current_language, "time_remaining", "Осталось: --:--:--"),
            font=("Segoe UI", 9)
        )
        self.time_label.pack(anchor="w", pady=(5, 0))

        # ========== ПРАВАЯ ПАНЕЛЬ ==========
        self.setup_right_panel(right_panel)

        # Обновить список дисков
        self.refresh_drives_list()

        # Контекстное меню для дисков
        self.create_drive_context_menu()

        # Привязываем колесо мыши для прокрутки
        self._bind_mousewheel(left_canvas)

    def _bind_mousewheel(self, canvas):
        """Привязка колеса мыши для прокрутки"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_enter(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_leave(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

    def setup_stats_tab(self, parent):
        """Настройка вкладки статистики с переводом"""
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(parent, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем колесо мыши
        self._bind_mousewheel(canvas)

        # Заголовок статистики
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(
            header_frame,
            text=get_translation(self.current_language, "statistics", "📊 СТАТИСТИКА"),
            font=("Segoe UI", 14, "bold"),
            foreground=self.colors["accent"]
        ).pack(anchor="w")

        # Статистика в две колонки
        stats_container = ttk.Frame(scrollable_frame)
        stats_container.pack(fill="x", padx=20, pady=(0, 20))

        # Левая колонка
        left_stats = ttk.Frame(stats_container)
        left_stats.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Правая колонка
        right_stats = ttk.Frame(stats_container)
        right_stats.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Статистические переменные
        stats_items = [
            ("stats_total_size", "size_total", left_stats, 0),
            ("stats_tested", "size_tested", left_stats, 1),
            ("stats_speed_avg", "speed_avg", left_stats, 2),
            ("stats_speed_max", "speed_max", left_stats, 3),
            ("stats_speed_min", "speed_min", left_stats, 4),
            ("stats_time_total", "time_total", right_stats, 0),
            ("stats_bad_sectors", "bad_sectors", right_stats, 1),
            ("stats_passes_complete", "passes_complete", right_stats, 2),
            ("stats_passes_remaining", "passes_remaining", right_stats, 3),
            ("stats_status", "status", right_stats, 4),
        ]

        for key, var_name, parent_frame, row in stats_items:
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)

            ttk.Label(
                frame,
                text=get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=22,
                anchor="w"
            ).pack(side="left")

            var = tk.StringVar(value="---")
            setattr(self, f"stat_{var_name}", var)

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
            text="🔴 " + get_translation(self.current_language, "stats_bad_sectors", "Битые сектора"),
            font=("Segoe UI", 12, "bold"),
            foreground=self.colors["danger"]
        ).pack(side="left")

        columns = ("sector", "status", "attempts")
        self.bad_sectors_tree = ttk.Treeview(
            scrollable_frame,
            columns=columns,
            show="headings",
            height=8
        )

        self.bad_sectors_tree.heading("sector", text=get_translation(self.current_language, "sector", "Сектор"))
        self.bad_sectors_tree.heading("status", text=get_translation(self.current_language, "status", "Статус"))
        self.bad_sectors_tree.heading("attempts", text=get_translation(self.current_language, "attempts", "Попыток"))

        self.bad_sectors_tree.column("sector", width=150)
        self.bad_sectors_tree.column("status", width=150)
        self.bad_sectors_tree.column("attempts", width=120)

        self.bad_sectors_tree.pack(fill="x", padx=20, pady=(0, 20))

    def setup_info_tab(self, parent):
        """Настройка вкладки информации с переводом"""
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(parent, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем колесо мыши
        self._bind_mousewheel(canvas)

        # Контейнер с отступами
        info_container = ttk.Frame(scrollable_frame)
        info_container.pack(fill="both", expand=True, padx=30, pady=30)

        # ===== ИНФОРМАЦИЯ О СИСТЕМЕ =====
        system_frame = ttk.LabelFrame(
            info_container,
            text=" " + get_translation(self.current_language, "system_info", "💻 ИНФОРМАЦИЯ О СИСТЕМЕ") + " ",
            padding=20
        )
        system_frame.pack(fill="x", pady=(0, 20))

        # Системная информация в две колонки
        sys_container = ttk.Frame(system_frame)
        sys_container.pack(fill="x")

        # Левая колонка
        left_sys = ttk.Frame(sys_container)
        left_sys.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Правая колонка
        right_sys = ttk.Frame(sys_container)
        right_sys.pack(side="right", fill="both", expand=True, padx=(20, 0))

        # Информация о системе
        import psutil
        import time

        # Время работы системы
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]

        sys_info = [
            ("system_os", f"{platform.system()} {platform.release()}", left_sys),
            ("system_python", platform.python_version(), left_sys),
            ("system_architecture", platform.architecture()[0], left_sys),
            ("system_processor", platform.processor() or "Unknown", left_sys),
            ("system_memory", f"{psutil.virtual_memory().total / (1024**3):.1f} GB", right_sys),
            ("system_disks", str(len(psutil.disk_partitions())), right_sys),
            ("system_uptime", uptime_str, right_sys),
            ("system_hostname", platform.node(), right_sys),
        ]

        for key, value, parent_frame in sys_info:
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)

            ttk.Label(
                frame,
                text=get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=20,
                anchor="w"
            ).pack(side="left")

            ttk.Label(
                frame,
                text=value,
                font=("Segoe UI", 10),
                foreground=self.colors["accent"],
                anchor="w",
                wraplength=250
            ).pack(side="left", padx=(10, 0))

        # ===== О ПРОГРАММЕ =====
        about_frame = ttk.LabelFrame(
            info_container,
            text=" " + get_translation(self.current_language, "about_program", "ℹ️ О ПРОГРАММЕ") + " ",
            padding=20
        )
        about_frame.pack(fill="x", pady=(0, 20))

        # Информация о программе в две колонки
        about_container = ttk.Frame(about_frame)
        about_container.pack(fill="x")

        left_about = ttk.Frame(about_container)
        left_about.pack(side="left", fill="both", expand=True, padx=(0, 20))

        right_about = ttk.Frame(about_container)
        right_about.pack(side="right", fill="both", expand=True, padx=(20, 0))

        # Дата сборки (текущая дата)
        build_date = datetime.now().strftime("%Y-%m-%d")

        app_info = [
            ("program_version", "1.0.0", left_about),
            ("program_author", "SD Card Tester Team", left_about),
            ("program_license", "MIT", right_about),
            ("program_github", "github.com/yourusername/sd-card-tester-pro", right_about),
            ("program_build", build_date, right_about),
        ]

        for key, value, parent_frame in app_info:
            frame = ttk.Frame(parent_frame)
            frame.pack(fill="x", pady=8)

            ttk.Label(
                frame,
                text=get_translation(self.current_language, key, key.replace("_", " ").title()),
                font=("Segoe UI", 10, "bold"),
                width=20,
                anchor="w"
            ).pack(side="left")

            ttk.Label(
                frame,
                text=value,
                font=("Segoe UI", 10),
                foreground=self.colors["accent"],
                anchor="w",
                wraplength=250
            ).pack(side="left", padx=(10, 0))

        # ===== КНОПКИ =====
        button_frame = ttk.Frame(info_container)
        button_frame.pack(fill="x", pady=(20, 0))

        # Создаем grid для кнопок
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        buttons = [
            ("btn_documentation", "📖", self.open_documentation, 0, 0),
            ("btn_check_updates", "🔄", self.check_for_updates, 0, 1),
            ("btn_report_bug", "🐛", self.report_bug, 1, 0),
            ("btn_error_log", "📋", self.show_error_log, 1, 1),
        ]

        for key, icon, command, row, col in buttons:
            btn = tk.Button(
                button_frame,
                text=f"{icon} {get_translation(self.current_language, key, key.replace('_', ' ').title())}",
                command=command,
                bg=self.colors["bg_light"],
                fg="white",
                font=("Segoe UI", 10),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2"
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            # Эффекты наведения
            def on_enter(e, btn=btn):
                btn['background'] = self.colors["accent"]

            def on_leave(e, btn=btn):
                btn['background'] = self.colors["bg_light"]

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # ===== ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ =====
        copyright_frame = ttk.Frame(info_container)
        copyright_frame.pack(fill="x", pady=(30, 0))

        ttk.Label(
            copyright_frame,
            text="© 2024 SD Card Tester Pro. " + get_translation(self.current_language, "all_rights_reserved", "Все права защищены."),
            font=("Segoe UI", 9),
            foreground="#888888"
        ).pack()

        ttk.Label(
            copyright_frame,
            text=get_translation(self.current_language, "warning_admin_short", "Для полного доступа запустите от администратора/root"),
            font=("Segoe UI", 9, "italic"),
            foreground=self.colors["warning"]
        ).pack(pady=(5, 0))

    def setup_right_panel(self, parent):
        """Настройка правой панели с вкладками"""
        # Вкладки
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Вкладка 1: График скорости
        speed_tab = ttk.Frame(self.notebook)
        self.notebook.add(speed_tab, text=get_translation(self.current_language, "tab_speed", "📈 ГРАФИК СКОРОСТИ"))
        self.setup_speed_chart(speed_tab)

        # Вкладка 2: Статистика
        stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(stats_tab, text=get_translation(self.current_language, "tab_stats", "📊 СТАТИСТИКА"))
        self.setup_stats_tab(stats_tab)

        # Вкладка 3: Лог
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text=get_translation(self.current_language, "tab_log", "📝 ЛОГ СОБЫТИЙ"))
        self.setup_log_tab(log_tab)

        # Вкладка 4: Информация
        info_tab = ttk.Frame(self.notebook)
        self.notebook.add(info_tab, text=get_translation(self.current_language, "tab_info", "ℹ️ ИНФОРМАЦИЯ"))
        self.setup_info_tab(info_tab)

    def create_menu(self):
        """Создание главного меню"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])

        # Меню Файл
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_file", "Файл"), menu=self.file_menu)
        self.file_menu.add_command(label=t.get("menu_save_log", "Сохранить лог..."), command=self.save_log)
        self.file_menu.add_command(label=t.get("menu_export", "Экспорт отчета..."), command=self.export_report)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=t.get("menu_settings", "Настройки..."), command=self.open_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=t.get("menu_exit", "Выход"), command=self.on_closing)

        # Меню Вид
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_view", "Вид"), menu=self.view_menu)
        self.view_menu.add_command(label=t.get("refresh_list", "Обновить список дисков"), command=self.refresh_drives_list)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=t.get("clear_log", "Очистить лог"), command=self.clear_log)
        self.view_menu.add_command(label=t.get("reset_stats", "Сбросить статистику"), command=self.reset_stats)

        # Меню Тестирование
        self.test_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label=t.get("menu_test", "Тестирование"), menu=self.test_menu
        )
        self.test_menu.add_command(
            label=t.get(
                "fast_pass", "Быстрый тест (1 проход)"),
            command=lambda: self.set_test_passes(1)
        )
        self.test_menu.add_command(
            label=t.get("standard_pass", "Стандартный тест (3 прохода)"),
            command=lambda: self.set_test_passes(3)
        )
        self.test_menu.add_command(
            label=t.get("full_pass", "Полный тест (7 проходов)"),
            command=lambda: self.set_test_passes(7)
        )
        self.test_menu.add_separator()
        self.test_menu.add_command(
            label=t.get("start_test", "Начать тест"), command=self.start_test
        )
        self.test_menu.add_command(
            label=t.get("pause", "Приостановить тест"), command=self.pause_test
        )
        self.test_menu.add_command(
            label=t.get("stop", "Остановить тест"), command=self.stop_test
        )

        # Меню Справка
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(
            label=t.get("menu_help", "Справка"), menu=self.help_menu
        )
        self.help_menu.add_command(label=t.get(
            "documentation", "Документация"), command=self.open_documentation
        )
        self.help_menu.add_command(
            label="📋 Журнал ошибок", command=self.show_error_log
        )
        self.help_menu.add_separator()
        self.help_menu.add_command(
            label=t.get("about", "О программе"), command=self.show_about
        )
        self.help_menu.add_command(
            label=t.get("check_updates", "Проверить обновления"),
            command=self.check_for_updates
        )

    def rename_drive(self):
        """Переименование выбранного диска"""
        selection = self.drive_tree.selection()
        if not selection:
            messagebox.showwarning(
                get_translation(self.current_language, "warning", "Предупреждение"),
                get_translation(self.current_language, "select_drive", "Выберите диск для переименования!")
            )
            return

        item = self.drive_tree.item(selection[0])
        values = item["values"]
        drive_path = values[0]

        # Проверка на системный диск
        if "system" in item["tags"]:
            messagebox.showerror(
                get_translation(self.current_language, "error", "Ошибка"),
                get_translation(self.current_language, "error_system_drive", "Нельзя переименовать системный диск!")
            )
            return

        # Диалог ввода нового имени
        dialog = tk.Toplevel(self.root)
        dialog.title(get_translation(self.current_language, "rename_drive_title", "Переименовать диск"))
        dialog.geometry("450x180")
        dialog.configure(bg=self.colors["bg_dark"])
        dialog.resizable(False, False)

        # Центрирование
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Текущее имя (метка тома)
        current_label = self.get_volume_label(drive_path)

        # Интерфейс
        ttk.Label(
            dialog,
            text=f"{get_translation(self.current_language, 'drive', 'Диск')}: {drive_path}",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(15, 5))

        ttk.Label(
            dialog,
            text=f"{get_translation(self.current_language, 'current_label', 'Текущая метка')}: {current_label}"
        ).pack(pady=(0, 10))

        frame = ttk.Frame(dialog)
        frame.pack(pady=10)

        ttk.Label(
            frame,
            text=get_translation(self.current_language, 'new_name', 'Новое имя:')
        ).pack(side="left", padx=(0, 10))

        name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=name_var, width=25)
        name_entry.pack(side="left")
        name_entry.focus()

        def do_rename():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showwarning(
                    get_translation(self.current_language, "warning", "Предупреждение"),
                    get_translation(self.current_language, "enter_drive_name", "Введите имя диска!")
                )
                return

            # Остальная логика переименования...
            try:
                if platform.system() == "Windows":
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    root_path = drive_path if drive_path.endswith('\\') else drive_path + '\\'
                    result = kernel32.SetVolumeLabelW(root_path, new_name + '\0')

                    if result:
                        messagebox.showinfo(
                            get_translation(self.current_language, "success", "Успех"),
                            f"{get_translation(self.current_language, 'drive_renamed', 'Диск переименован в')} '{new_name}'"
                        )
                    else:
                        error_code = ctypes.GetLastError()
                        messagebox.showerror(
                            get_translation(self.current_language, "error", "Ошибка"),
                            f"Не удалось переименовать диск (код ошибки: {error_code})"
                        )

                dialog.destroy()
                self.refresh_drives_list()
            except Exception as e:
                messagebox.showerror(
                    get_translation(self.current_language, "error", "Ошибка"),
                    f"Не удалось переименовать диск:\n{str(e)}"
                )

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(15, 10))

        ttk.Button(
            btn_frame,
            text=get_translation(self.current_language, "rename", "Переименовать"),
            command=do_rename
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text=get_translation(self.current_language, "cancel", "Отмена"),
            command=dialog.destroy
        ).pack(side="left", padx=5)

        name_entry.bind('<Return>', lambda e: do_rename())

    def on_language_change(self, event):
        """Обработка изменения языка"""
        new_lang = self.language_var.get()
        self.change_language(new_lang)

    def change_language(self, lang):
        """Изменить язык интерфейса"""
        if lang in locales.TRANSLATIONS:
            self.current_language = lang
            self.config["ui"]["language"] = lang

            # Обновляем все тексты в интерфейсе
            self.update_ui_language()

            # Пересоздаем меню
            self.recreate_menu()

            self.save_config()
            self.log_message(f"Язык изменен на {lang}", "info")

    def update_ui_language(self):
        """Обновление всех текстов в интерфейсе"""
        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])

        # Заголовок окна
        self.root.title(t.get("app_title", "SD Card Tester Pro"))

        # Заголовок программы
        if hasattr(self, 'main_title_label'):
            self.main_title_label.config(text=t.get("main_title", "🔧 SD CARD TESTER PRO"))

        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.config(text=t.get("subtitle", "Профессиональное тестирование накопителей"))

        # Фреймы
        if hasattr(self, 'drive_frame'):
            self.drive_frame.config(text=" " + t.get("drive_selection", "ВЫБОР НАКОПИТЕЛЯ") + " ")

        if hasattr(self, 'settings_frame'):
            self.settings_frame.config(text=" " + t.get("test_settings", "НАСТРОЙКИ ТЕСТА") + " ")

        if hasattr(self, 'progress_frame'):
            self.progress_frame.config(text=" " + t.get("progress", "ПРОГРЕСС") + " ")

        # Метки языков
        if hasattr(self, 'language_label'):
            self.language_label.config(text=t.get("language", "Язык / Language / 语言:"))

        # Кнопки
        if hasattr(self, 'refresh_button'):
            self.refresh_button.config(text=t.get("refresh_list", "🔄 Обновить список"))

        if hasattr(self, 'rename_button'):
            self.rename_button.config(text=t.get("rename", "✏️ Переименовать диск"))

        if hasattr(self, 'start_button'):
            self.start_button.config(text=t.get("start_test", "🚀 НАЧАТЬ ТЕСТ"))

        if hasattr(self, 'pause_button'):
            if self.test_paused:
                self.pause_button.config(text=t.get("resume", "▶ ПРОДОЛЖИТЬ"))
            else:
                self.pause_button.config(text=t.get("pause", "⏸ ПАУЗА"))

        if hasattr(self, 'stop_button'):
            self.stop_button.config(text=t.get("stop", "⏹ ОСТАНОВИТЬ"))

        # Заголовки колонок Treeview
        if hasattr(self, 'drive_tree'):
            self.drive_tree.heading("drive", text=t.get("drive", "Диск"))
            self.drive_tree.heading("type", text=t.get("type", "Тип"))
            self.drive_tree.heading("size", text=t.get("size", "Размер"))
            self.drive_tree.heading("filesystem", text=t.get("filesystem", "ФС"))

        # Метка информации о диске
        if hasattr(self, 'drive_info_label'):
            selection = self.drive_tree.selection()
            if not selection:
                self.drive_info_label.config(text=t.get("select_drive", "Выберите накопитель для тестирования"))

        # Настройки теста
        if hasattr(self, 'passes_label'):
            self.passes_label.config(text=t.get("passes_label", "Количество проходов:"))

        if hasattr(self, 'fast_pass_radio'):
            self.fast_pass_radio.config(text=t.get("fast_pass", "Быстрый (1 проход)"))

        if hasattr(self, 'standard_pass_radio'):
            self.standard_pass_radio.config(text=t.get("standard_pass", "Стандартный (3 прохода)"))

        if hasattr(self, 'full_pass_radio'):
            self.full_pass_radio.config(text=t.get("full_pass", "Полный (7 проходов)"))

        if hasattr(self, 'or_label'):
            self.or_label.config(text=t.get("or_label", "или:"))

        if hasattr(self, 'passes_suffix_label'):
            self.passes_suffix_label.config(text=t.get("passes_suffix", "проходов"))

        # Чекбоксы тестов
        if hasattr(self, 'test_ones_check'):
            self.test_ones_check.config(text=t.get("test_ones", "Запись единиц (0xFF)"))

        if hasattr(self, 'test_zeros_check'):
            self.test_zeros_check.config(text=t.get("test_zeros", "Запись нулей (0x00)"))

        if hasattr(self, 'test_random_check'):
            self.test_random_check.config(text=t.get("test_random", "Случайные данные"))

        if hasattr(self, 'test_verify_check'):
            self.test_verify_check.config(text=t.get("test_verify", "Проверка после записи"))

        # Форматирование
        if hasattr(self, 'format_check'):
            self.format_check.config(text=t.get("format_after", "Форматировать после теста"))

        if hasattr(self, 'fs_label'):
            self.fs_label.config(text=t.get("filesystem", "Файловая система:"))

        # Прогресс
        if hasattr(self, 'progress_label'):
            if not self.test_running:
                self.progress_label.config(text=t.get("waiting", "Ожидание начала теста..."))

        if hasattr(self, 'time_label'):
            self.time_label.config(text=t.get("time_remaining", "Осталось: --:--:--"))

        # Вкладки
        if hasattr(self, 'notebook'):
            tabs = self.notebook.tabs()
            if len(tabs) >= 1:
                self.notebook.tab(tabs[0], text=t.get("tab_speed", "📈 ГРАФИК СКОРОСТИ"))
            if len(tabs) >= 2:
                self.notebook.tab(tabs[1], text=t.get("tab_stats", "📊 СТАТИСТИКА"))
            if len(tabs) >= 3:
                self.notebook.tab(tabs[2], text=t.get("tab_log", "📝 ЛОГ СОБЫТИЙ"))
            if len(tabs) >= 4:
                self.notebook.tab(tabs[3], text=t.get("tab_info", "ℹ️ ИНФОРМАЦИЯ"))

        # Обновление статистики (если переменные существуют)
        stats_vars = [
            ("stat_size_total", "stats_total_size"),
            ("stat_size_tested", "stats_tested"),
            ("stat_speed_avg", "stats_speed_avg"),
            ("stat_speed_max", "stats_speed_max"),
            ("stat_speed_min", "stats_speed_min"),
            ("stat_time_total", "stats_time_total"),
            ("stat_bad_sectors", "stats_bad_sectors"),
            ("stat_passes_complete", "stats_passes_complete"),
            ("stat_passes_remaining", "stats_passes_remaining"),
            ("stat_status", "stats_status"),
        ]

        for var_name, key in stats_vars:
            if hasattr(self, var_name):
                # Значение остается, обновляется только если нужно сбросить
                pass

    def recreate_menu(self):
        """Пересоздание меню при смене языка"""
        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])

        # Удаляем старое меню
        self.root.config(menu=None)

        # Создаем новое меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t.get("menu_file", "Файл"), menu=file_menu)
        file_menu.add_command(label=t.get("menu_save_log", "Сохранить лог..."), command=self.save_log)
        file_menu.add_command(label=t.get("menu_export", "Экспорт отчета..."), command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label=t.get("menu_settings", "Настройки..."), command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label=t.get("menu_exit", "Выход"), command=self.on_closing)

        # Меню Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t.get("menu_view", "Вид"), menu=view_menu)
        view_menu.add_command(label=t.get("refresh_list", "Обновить список дисков"), command=self.refresh_drives_list)
        view_menu.add_separator()
        view_menu.add_command(label=t.get("clear_log", "Очистить лог"), command=self.clear_log)
        view_menu.add_command(label=t.get("reset_stats", "Сбросить статистику"), command=self.reset_stats)

        # Меню Тестирование
        test_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t.get("menu_test", "Тестирование"), menu=test_menu)
        test_menu.add_command(label=t.get("fast_pass", "Быстрый тест (1 проход)"), command=lambda: self.set_test_passes(1))
        test_menu.add_command(label=t.get("standard_pass", "Стандартный тест (3 прохода)"), command=lambda: self.set_test_passes(3))
        test_menu.add_command(label=t.get("full_pass", "Полный тест (7 проходов)"), command=lambda: self.set_test_passes(7))
        test_menu.add_separator()
        test_menu.add_command(label=t.get("start_test", "Начать тест"), command=self.start_test)
        test_menu.add_command(label=t.get("pause", "Приостановить тест"), command=self.pause_test)
        test_menu.add_command(label=t.get("stop", "Остановить тест"), command=self.stop_test)

        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t.get("menu_help", "Справка"), menu=help_menu)
        help_menu.add_command(label=t.get("documentation", "Документация"), command=self.open_documentation)
        help_menu.add_command(label="📋 Журнал ошибок", command=self.show_error_log)
        help_menu.add_separator()
        help_menu.add_command(label=t.get("about", "О программе"), command=self.show_about)
        help_menu.add_command(label=t.get("check_updates", "Проверить обновления"), command=self.check_for_updates)

        self.menubar = menubar

    def log_message(self, message, level="info"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "white",
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["danger"],
            "debug": "#888888",
            "system": "#2196f3",
        }

        tags = {
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "error",
            "debug": "debug",
            "system": "system",
        }

        tag = tags.get(level, "info")
        color = colors.get(level, "white")

        if hasattr(self, 'log_text'):
            if not self.log_text.tag_names() or tag not in self.log_text.tag_names():
                self.log_text.tag_configure(tag, foreground=color)

            self.log_text.insert("end", f"[{timestamp}] {message}\n", tag)
            self.log_text.see("end")

        print(f"[{timestamp}] [{level.upper()}] {message}")

    def setup_icon(self):
        """Настройка иконки приложения"""
        icon_files = {
            "Windows": "icon.ico",
            "Linux": "icon.png",
            "Darwin": "icon.icns",  # macOS
        }

        current_os = platform.system()
        icon_file = icon_files.get(current_os, "icon.ico")

        if os.path.exists(icon_file):
            try:
                if current_os == "Windows":
                    self.root.iconbitmap(icon_file)
                elif current_os == "Linux":
                    # Для Linux можно использовать PhotoImage
                    icon = tk.PhotoImage(file=icon_file)
                    self.root.iconphoto(True, icon)
            except Exception as e:
                print(f"Не удалось загрузить иконку: {e}")

    def merge_configs(self, default, user):
        """Рекурсивное объединение конфигураций"""
        for key, value in user.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                self.merge_configs(default[key], value)
            else:
                default[key] = value

    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    def check_write_permissions(self, drive_path):
        """Проверка прав на запись"""
        try:
            test_file = os.path.join(drive_path, ".write_test")
            with open(test_file, 'wb') as f:
                f.write(b'test')
            os.remove(test_file)
            self.log_message("Права на запись есть", "success")
            return True
        except Exception as e:
            self.log_message(f"Нет прав на запись: {e}", "error")
            return False

    def check_admin_permissions(self):
        """Проверка прав администратора"""
        is_admin = False

        if platform.system() == "Windows":
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            except:
                pass
        elif platform.system() == "Linux":
            is_admin = self.check_admin_linux()
        elif platform.system() == "Darwin":  # macOS
            is_admin = os.getuid() == 0

        if not is_admin:
            warning_msg = (
                "⚠️  Предупреждение:\n"
                "Для полного доступа к устройствам рекомендуется запустить программу от имени администратора/root.\n"
                "Некоторые функции могут быть недоступны."
            )
            self.log_message(warning_msg, "warning")  # Исправлено

        return is_admin

    def check_admin_linux(self):
        """Проверка прав администратора на Linux"""
        if platform.system() == "Linux":
            try:
                # Проверка EUID (самый надежный способ)
                if os.geteuid() == 0:
                    return True

                # Дополнительная проверка через группы
                import pwd
                import grp

                # Получаем имя текущего пользователя
                try:
                    username = pwd.getpwuid(os.getuid()).pw_name
                except KeyError:
                    username = os.getenv("USER") or os.getenv("LOGNAME") or ""

                if not username:
                    return False

                admin_groups = ["root", "sudo", "admin", "wheel"]

                # Получаем группы пользователя
                user_groups = []
                try:
                    user_groups = [
                        g.gr_name for g in grp.getgrall() if username in g.gr_mem
                    ]
                except:
                    pass

                # Проверяем наличие админских групп
                return any(group in admin_groups for group in user_groups)

            except (ImportError, KeyError):
                # Fallback: проверка только по EUID
                return os.geteuid() == 0
        return False

    def setup_styles(self):
        """Настройка стилей и цветов"""
        self.colors = {
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

        self.root.configure(bg=self.colors["bg_dark"])

        # Стиль для ttk
        style = ttk.Style()
        style.theme_use("clam")

        # Настройка стилей виджетов
        style.configure(
            "TLabel", background=self.colors["bg_dark"], foreground=self.colors["fg"]
        )
        style.configure("TFrame", background=self.colors["bg_dark"])
        style.configure(
            "TLabelframe",
            background=self.colors["bg_dark"],
            foreground=self.colors["accent"],
        )
        style.configure(
            "TLabelframe.Label",
            background=self.colors["bg_dark"],
            foreground=self.colors["accent"],
        )

        # Стили для кнопок
        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "Danger.TButton",
            background=self.colors["danger"],
            foreground="white",
            font=("Segoe UI", 10),
        )
        # Добавляем выбор языка в настройки конфигурации
        if "language" in self.config["ui"]:
            self.current_language = self.config["ui"]["language"]

    def set_test_passes(self, passes):
        """Установка количества проходов"""
        self.passes_var.set(passes)
        self.custom_passes_var.set("")

    def setup_speed_chart(self, parent):
        """Настройка графика скорости"""
        self.fig, self.ax = plt.subplots(figsize=(8, 5), dpi=80)
        self.fig.patch.set_facecolor(self.colors["bg_light"])
        self.ax.set_facecolor(self.colors["bg_light"])

        self.ax.set_xlabel("Время (сек)", color="white")
        self.ax.set_ylabel("Скорость (MB/s)", color="white")
        self.ax.set_title("График скорости записи", color="white", pad=20)

        self.ax.tick_params(colors="white")
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["top"].set_color("white")
        self.ax.spines["left"].set_color("white")
        self.ax.spines["right"].set_color("white")

        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def setup_log_tab(self, parent):
        """Настройка вкладки лога"""
        # Текстовое поле с цветным выводом
        self.log_text = tk.Text(
            parent,
            bg=self.colors["bg_light"],
            fg="white",
            font=("Consolas", 9),
            wrap="word",
            height=20,
        )

        scrollbar = ttk.Scrollbar(parent, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления логом
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Button(button_frame, text="Очистить лог", command=self.clear_log).pack(
            side="left", padx=2
        )

        ttk.Button(button_frame, text="Сохранить лог", command=self.save_log).pack(
            side="left", padx=2
        )

        ttk.Button(
            button_frame, text="Экспорт отчета", command=self.export_report
        ).pack(side="left", padx=2)

        ttk.Button(
            button_frame, text="Копировать лог", command=self.copy_log_to_clipboard
        ).pack(side="left", padx=2)

    def setup_info_tab(self, parent):
        """Настройка вкладки информации"""
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Информация о системе
        ttk.Label(
            info_frame, text="Информация о системе", font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 15))

        sys_info = [
            ("ОС:", platform.system() + " " + platform.release()),
            ("Версия Python:", platform.python_version()),
            ("Архитектура:", platform.architecture()[0]),
            ("Процессор:", platform.processor()),
            ("Память:", f"{psutil.virtual_memory().total / (1024**3):.1f} GB"),
            ("Дисков:", len(psutil.disk_partitions())),
        ]

        for label, value in sys_info:
            frame = ttk.Frame(info_frame)
            frame.pack(fill="x", pady=5)

            ttk.Label(frame, text=label, font=("Segoe UI", 10, "bold"), width=15).pack(
                side="left"
            )

            ttk.Label(frame, text=value, font=("Segoe UI", 10)).pack(
                side="left", padx=(10, 0)
            )

        # Информация о программе
        ttk.Label(info_frame, text="\nО программе", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(20, 15)
        )

        app_info = [
            ("Версия:", "1.0.0"),
            ("Автор:", "SD Card Tester Team"),
            ("Лицензия:", "MIT"),
            ("GitHub:", "github.com/yourusername/sd-card-tester-pro"),
        ]

        for label, value in app_info:
            frame = ttk.Frame(info_frame)
            frame.pack(fill="x", pady=5)

            ttk.Label(frame, text=label, font=("Segoe UI", 10, "bold"), width=15).pack(
                side="left"
            )

            ttk.Label(frame, text=value, font=("Segoe UI", 10)).pack(
                side="left", padx=(10, 0)
            )

        # Кнопки
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            button_frame,
            text="📖 Открыть документацию",
            command=self.open_documentation,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame, text="🔄 Проверить обновления", command=self.check_for_updates
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            button_frame, text="🐛 Сообщить об ошибке", command=self.report_bug
        ).pack(side="left")

    def refresh_drives_list(self):
        """Обновление списка дисков с выделением системных"""
        # Очистка текущего списка
        for item in self.drive_tree.get_children():
            self.drive_tree.delete(item)

        # Получение информации о дисках
        drives = []

        if platform.system() == "Windows":
            try:
                import win32api
                import win32file
                import string

                for drive in string.ascii_uppercase:
                    drive_path = f"{drive}:\\"
                    try:
                        drive_type = win32file.GetDriveType(drive_path)

                        if drive_type in [
                            win32file.DRIVE_REMOVABLE,
                            win32file.DRIVE_FIXED,
                            win32file.DRIVE_CDROM,
                        ]:
                            # Получение информации о диске
                            try:
                                free_bytes, total_bytes, _ = (
                                    win32api.GetDiskFreeSpaceEx(drive_path)
                                )
                                size_gb = total_bytes / (1024**3)

                                # Определение типа
                                if drive_type == win32file.DRIVE_REMOVABLE:
                                    drive_type_str = "Съемный"
                                    tag_color = self.colors["removable_drive"]
                                elif drive_type == win32file.DRIVE_FIXED:
                                    drive_type_str = "Внутренний"
                                    tag_color = self.colors["system_drive"]
                                else:
                                    drive_type_str = "CD/DVD"
                                    tag_color = "#888888"

                                # Получение файловой системы
                                fs = ""
                                try:
                                    volume_info = win32api.GetVolumeInformation(
                                        drive_path
                                    )
                                    fs = volume_info[4]
                                except:
                                    fs = "Неизвестно"

                                # Определение системного диска
                                is_system = False
                                try:
                                    if os.path.exists(
                                        os.path.join(drive_path, "Windows")
                                    ):
                                        is_system = True
                                        drive_type_str = "СИСТЕМНЫЙ"
                                        tag_color = self.colors["danger"]
                                except:
                                    pass

                                drives.append(
                                    {
                                        "path": drive_path,
                                        "type": drive_type_str,
                                        "size": f"{size_gb:.1f} GB",
                                        "fs": fs,
                                        "color": tag_color,
                                        "is_system": is_system,
                                    }
                                )

                            except:
                                continue

                    except:
                        continue

            except ImportError:
                self.log_message(
                    "pywin32 не установлен. Некоторые функции Windows недоступны.",
                    "warning",
                )
                # Альтернативный метод для Windows без pywin32
                import string

                for drive in string.ascii_uppercase:
                    drive_path = f"{drive}:\\"
                    if os.path.exists(drive_path):
                        try:
                            total_bytes = psutil.disk_usage(drive_path).total
                            size_gb = total_bytes / (1024**3)

                            # Определение типа диска (упрощенно)
                            is_system = drive_path == "C:\\" or os.path.exists(
                                os.path.join(drive_path, "Windows")
                            )

                            drives.append(
                                {
                                    "path": drive_path,
                                    "type": "СИСТЕМНЫЙ" if is_system else "Неизвестно",
                                    "size": f"{size_gb:.1f} GB",
                                    "fs": "Неизвестно",
                                    "color": (
                                        self.colors["danger"]
                                        if is_system
                                        else "#888888"
                                    ),
                                    "is_system": is_system,
                                }
                            )
                        except:
                            continue

        else:
            # Для Linux/macOS
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    size_gb = usage.total / (1024**3)

                    # Определение системного диска
                    is_system = partition.mountpoint in [
                        "/",
                        "/boot",
                        "/etc",
                        "/System",
                    ]

                    drive_type = "Внутренний"
                    if "removable" in partition.opts or "usb" in partition.opts:
                        drive_type = "Съемный"

                    drives.append(
                        {
                            "path": partition.mountpoint,
                            "type": "СИСТЕМНЫЙ" if is_system else drive_type,
                            "size": f"{size_gb:.1f} GB",
                            "fs": partition.fstype,
                            "color": (
                                self.colors["danger"]
                                if is_system
                                else self.colors["system_drive"]
                            ),
                            "is_system": is_system,
                        }
                    )
                except:
                    continue

        # Добавление в Treeview
        for drive in drives:
            item_id = self.drive_tree.insert(
                "",
                "end",
                values=(drive["path"], drive["type"], drive["size"], drive["fs"]),
            )

            if drive["is_system"]:
                self.drive_tree.tag_configure(
                    "system", background="#330000", foreground="white"
                )
                self.drive_tree.item(item_id, tags=("system",))

        self.log_message(f"Найдено дисков: {len(drives)}", "info")

    def on_drive_select(self, event):
        """Обработка выбора диска"""
        selection = self.drive_tree.selection()
        if selection:
            item = self.drive_tree.item(selection[0])
            values = item["values"]

            # Проверка на системный диск
            tags = item.get("tags", [])
            if "system" in tags:
                self.drive_info_label.config(
                    text=f"⚠️  ВНИМАНИЕ: Выбран СИСТЕМНЫЙ диск! Тестирование запрещено!",
                    foreground=self.colors["danger"],
                )
                self.start_button.config(state="disabled")
            else:
                self.drive_info_label.config(
                    text=f"Выбран диск: {values[0]} ({values[1]}, {values[2]}, {values[3]})",
                    foreground=self.colors["success"],
                )
                self.start_button.config(state="normal")

    def auto_save_log(self, message, level):
        """Автосохранение важных сообщений"""
        try:
            log_file = "sd_card_tester_auto.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")
        except Exception as e:
            print(f"Ошибка автосохранения лога: {e}")

    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete("1.0", "end")
        self.log_message("Лог очищен", "info")

    def copy_log_to_clipboard(self):
        """Копирование лога в буфер обмена"""
        try:
            log_content = self.log_text.get("1.0", "end")
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.log_message("Лог скопирован в буфер обмена", "success")
        except Exception as e:
            self.log_message(f"Ошибка копирования: {str(e)}", "error")

    def save_log(self):
        """Сохранение лога в файл"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get("1.0", "end"))
                self.log_message(f"Лог сохранен: {filename}", "success")
            except Exception as e:
                self.log_message(f"Ошибка сохранения: {str(e)}", "error")

    def export_report(self):
        """Экспорт полного отчета"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("HTML files", "*.html"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*"),
            ],
        )

        if filename:
            try:
                if filename.endswith(".html"):
                    self.export_html_report(filename)
                elif filename.endswith(".pdf"):
                    self.export_pdf_report(filename)
                else:
                    self.export_text_report(filename)

                self.log_message(f"Отчет экспортирован: {filename}", "success")
            except Exception as e:
                self.log_message(f"Ошибка экспорта: {str(e)}", "error")

    def export_text_report(self, filename):
        """Экспорт отчета в текстовом формате"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("SD CARD TESTER PRO - ОТЧЕТ О ТЕСТИРОВАНИИ\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Версия программы: 1.0\n")
            f.write(
                f"Операционная система: {platform.system()} {platform.release()}\n\n"
            )

            # Статистика
            f.write("СТАТИСТИКА:\n")
            f.write("-" * 40 + "\n")
            for attr in dir(self):
                if attr.startswith("stat_"):
                    var = getattr(self, attr)
                    f.write(f"{attr[5:].replace('_', ' ').title()}: {var.get()}\n")

            # Информация о диске
            selection = self.drive_tree.selection()
            if selection:
                item = self.drive_tree.item(selection[0])
                values = item["values"]
                f.write(f"\nТестируемый диск: {values[0]}\n")
                f.write(f"Тип: {values[1]}\n")
                f.write(f"Размер: {values[2]}\n")
                f.write(f"Файловая система: {values[3]}\n")

            # Битые сектора
            f.write(f"\nБитые сектора ({len(self.bad_sectors)}):\n")
            f.write("-" * 40 + "\n")
            for sector in self.bad_sectors[:100]:  # Ограничим вывод
                f.write(f"Сектор {sector}\n")
            if len(self.bad_sectors) > 100:
                f.write(f"... и еще {len(self.bad_sectors) - 100} секторов\n")

            f.write("\nЛОГ СОБЫТИЙ:\n")
            f.write("-" * 40 + "\n")
            f.write(self.log_text.get("1.0", "end"))

    def export_html_report(self, filename):
        """Экспорт отчета в HTML формате"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SD Card Tester Pro - Отчет</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .statistics { background: #f5f5f5; padding: 20px; border-radius: 5px; }
                .log { background: #f9f9f9; padding: 20px; border-radius: 5px; }
                .warning { color: #ff9800; }
                .error { color: #f44336; }
                .success { color: #4caf50; }
            </style>
        </head>
        <body>
            <h1>SD Card Tester Pro - Отчет о тестировании</h1>
            <p>Дата: {date}</p>
            <p>Версия: 1.0</p>
            
            <div class="statistics">
                <h2>Статистика</h2>
                {statistics}
            </div>
            
            <div class="log">
                <h2>Лог событий</h2>
                <pre>{log}</pre>
            </div>
        </body>
        </html>
        """

        # Собираем статистику
        stats_html = ""
        for attr in dir(self):
            if attr.startswith("stat_"):
                var = getattr(self, attr)
                stats_html += f"<p><strong>{attr[5:].replace('_', ' ').title()}:</strong> {var.get()}</p>\n"

        html_content = html_template.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            statistics=stats_html,
            log=self.log_text.get("1.0", "end"),
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_pdf_report(self, filename):
        """Экспорт отчета в PDF формате"""
        self.log_message(
            "Экспорт в PDF временно недоступен. Используйте HTML или TXT формат.",
            "warning",
        )
        self.export_text_report(filename.replace(".pdf", ".txt"))

    def update_speed_chart(self, speed_mb, time_sec):
        """Обновление графика скорости"""
        self.speed_data.append((time_sec, speed_mb))

        if len(self.speed_data) > self.config["ui"]["chart_points"]:
            self.speed_data.pop(0)

        # Очистка графика
        self.ax.clear()

        if self.speed_data:
            times, speeds = zip(*self.speed_data)
            self.ax.plot(times, speeds, "b-", linewidth=2, label="Скорость записи")
            self.ax.fill_between(times, 0, speeds, alpha=0.3, color="blue")

            # Средняя скорость
            if len(speeds) > 0:
                avg_speed = sum(speeds) / len(speeds)
                self.ax.axhline(
                    y=avg_speed,
                    color="r",
                    linestyle="--",
                    label=f"Средняя: {avg_speed:.1f} MB/s",
                )

                # Максимальная скорость
                max_speed = max(speeds)
                self.ax.axhline(
                    y=max_speed,
                    color="g",
                    linestyle=":",
                    label=f"Макс: {max_speed:.1f} MB/s",
                )

        self.ax.set_xlabel("Время (сек)", color="white")
        self.ax.set_ylabel("Скорость (MB/s)", color="white")
        self.ax.set_title("График скорости записи", color="white", pad=20)
        self.ax.legend(facecolor=self.colors["bg_light"], edgecolor="white")
        self.ax.tick_params(colors="white")

        for spine in self.ax.spines.values():
            spine.set_color("white")

        self.fig.patch.set_facecolor(self.colors["bg_light"])
        self.ax.set_facecolor(self.colors["bg_light"])

        self.canvas.draw()

    def update_stats(self):
        """Обновление статистики"""
        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])
        if hasattr(self, "stat_size_total"):
            self.stat_size_total.set(
                f"{self.total_size:.1f} GB" if hasattr(self, "total_size") else "---"
            )

        if hasattr(self, "stat_size_tested"):
            tested = self.current_position if hasattr(self, "current_position") else 0
            self.stat_size_tested.set(f"{tested:.1f} GB")

        if hasattr(self, "stat_speed_avg"):
            if self.speed_data:
                speeds = [s[1] for s in self.speed_data]
                avg = sum(speeds) / len(speeds) if speeds else 0
                self.stat_speed_avg.set(f"{avg:.1f} MB/s")
            else:
                self.stat_speed_avg.set("---")

        if hasattr(self, "stat_speed_max"):
            if self.speed_data:
                max_speed = max([s[1] for s in self.speed_data])
                self.stat_speed_max.set(f"{max_speed:.1f} MB/s")
            else:
                self.stat_speed_max.set("---")

        if hasattr(self, "stat_speed_min"):
            if self.speed_data:
                min_speed = min([s[1] for s in self.speed_data])
                self.stat_speed_min.set(f"{min_speed:.1f} MB/s")
            else:
                self.stat_speed_min.set("---")

        if hasattr(self, "stat_time_total"):
            if self.test_start_time:
                elapsed = datetime.now() - self.test_start_time
                self.stat_time_total.set(str(elapsed).split(".")[0])
            else:
                self.stat_time_total.set("---")

        if hasattr(self, "stat_bad_sectors"):
            self.stat_bad_sectors.set(str(len(self.bad_sectors)))

        if hasattr(self, "stat_passes_complete"):
            self.stat_passes_complete.set(str(self.current_pass))

        if hasattr(self, "stat_passes_remaining"):
            remaining = self.total_passes - self.current_pass
            self.stat_passes_remaining.set(str(remaining))

        if hasattr(self, "stat_status"):
            if self.test_running:
                if self.test_paused:
                    self.stat_status.set(t.get("paused", "На паузе"))
                else:
                    self.stat_status.set(t.get("testing", "Тестирование..."))
            else:
                self.stat_status.set(t.get("waiting", "Ожидание"))

    def reset_stats(self):
        """Сброс статистики"""
        for attr in dir(self):
            if attr.startswith("stat_"):
                var = getattr(self, attr)
                var.set("---")

        self.speed_data = []
        self.bad_sectors = []
        self.bad_sectors_tree.delete(*self.bad_sectors_tree.get_children())
        self.ax.clear()
        self.canvas.draw()

        self.log_message("Статистика сброшена", "info")

    def start_test(self):
        """Начало тестирования"""
        selection = self.drive_tree.selection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите диск для тестирования!")
            return

        item = self.drive_tree.item(selection[0])
        values = item["values"]
        drive_path = values[0]

        # Проверка прав на запись
        if not self.check_write_permissions(drive_path):
            messagebox.showerror(
                "Ошибка доступа",
                f"Нет прав на запись на диск {drive_path}!\n"
                "Запустите программу от имени администратора/root."
            )
            return

        # Проверка на системный диск
        if "system" in item["tags"]:
            messagebox.showerror(
                "Ошибка безопасности",
                "Тестирование системных дисков запрещено!\n"
                "Выберите съемный носитель.",
            )
            return

        # Получение количества проходов
        try:
            if self.custom_passes_var.get() and self.custom_passes_var.get().isdigit():
                passes = int(self.custom_passes_var.get())
                if passes < 1 or passes > 100:
                    raise ValueError
            else:
                passes = self.passes_var.get()
        except:
            messagebox.showerror(
                "Ошибка", "Некорректное количество проходов. Введите число от 1 до 100."
            )
            return

        # Проверка, что выбран хотя бы один тип теста
        if not (
            self.test_write_ones.get()
            or self.test_write_zeros.get()
            or self.test_random.get()
        ):
            messagebox.showerror("Ошибка", "Выберите хотя бы один тип теста!")
            return

        # Подтверждение
        warning_text = f"""
⚠️  КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ  ⚠️

Все данные на диске {drive_path} будут 
БЕЗВОЗВРАТНО УНИЧТОЖЕНЫ!

Параметры теста:
• Проходов: {passes}
• Запись единиц: {'Да' if self.test_write_ones.get() else 'Нет'}
• Запись нулей: {'Да' if self.test_write_zeros.get() else 'Нет'}
• Случайные данные: {'Да' if self.test_random.get() else 'Нет'}
• Проверка чтения: {'Да' if self.test_verify.get() else 'Нет'}
• Форматирование: {'Да' if self.format_var.get() else 'Нет'}
• Файловая система: {self.fs_var.get()}

Вы уверены, что хотите продолжить?
"""

        if not messagebox.askyesno(
            "ПОДТВЕРЖДЕНИЕ УНИЧТОЖЕНИЯ", warning_text, icon="warning"
        ):
            return

        # Сброс данных
        self.speed_data = []
        self.bad_sectors = []
        self.bad_sectors_tree.delete(*self.bad_sectors_tree.get_children())
        self.current_pass = 0
        self.total_passes = passes
        self.current_position = 0

        # Настройка интерфейса
        self.test_running = True
        self.test_paused = False
        self.cancel_requested = False

        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")

        self.progress_bar["value"] = 0
        self.progress_label.config(text="Подготовка к тестированию...")

        # Очистка лога
        self.clear_log()
        self.log_message(f"Начало тестирования диска: {drive_path}", "info")
        self.log_message(f"Количество проходов: {self.total_passes}", "info")
        self.log_message(
            f"Типы тестов: "
            + ("Единицы " if self.test_write_ones.get() else "")
            + ("Нули " if self.test_write_zeros.get() else "")
            + ("Случайные " if self.test_random.get() else ""),
            "info",
        )

        # Запуск теста в отдельном потоке
        test_thread = threading.Thread(
            target=self.run_test, args=(drive_path,), daemon=True, name="TestThread"
        )
        test_thread.start()

        # Запуск таймера обновления
        self.test_start_time = datetime.now()
        self.update_stats_timer()

    def write_test_pattern(self, drive_path, pattern_type, chunk_size_mb=1024):
        """Реальная запись тестового паттерна на диск"""
        try:
            test_file = os.path.join(drive_path, "sd_test_temp.dat")
            chunk_size = min(chunk_size_mb * 1024 * 1024, 100 * 1024 * 1024)

            # Подготовка тестовых данных
            if pattern_type == "ones":
                data = b'\xFF' * 1024 * 1024
            elif pattern_type == "zeros":
                data = b'\x00' * 1024 * 1024
            else:  # random
                data = os.urandom(1024 * 1024)

            self.message_queue.put(("log", f"Запись на диск {drive_path}...", "info"))

            # Запись файла
            start_time = time.time()
            bytes_written = 0
            target_size = 100 * 1024 * 1024

            with open(test_file, 'wb') as f:
                while bytes_written < target_size:
                    if self.cancel_requested:
                        break

                    while self.test_paused:
                        time.sleep(0.1)
                        if self.cancel_requested:
                            break

                    write_size = min(chunk_size, target_size - bytes_written)
                    write_data = data[:write_size] if len(data) >= write_size else data * (write_size // len(data) + 1)
                    write_data = write_data[:write_size]

                    f.write(write_data)
                    f.flush()
                    os.fsync(f.fileno())

                    bytes_written += write_size
                    elapsed = time.time() - start_time
                    speed_mb = (bytes_written / (1024 * 1024)) / elapsed if elapsed > 0 else 0

                    self.message_queue.put(("speed", speed_mb, elapsed))
                    self.message_queue.put(("progress", (bytes_written / target_size) * 100))

            # Верификация
            if self.test_verify.get() and not self.cancel_requested:
                self.message_queue.put(("log", "Проверка чтения...", "info"))
                self.verify_test_file(test_file, data, bytes_written)

            # Удаление файла
            try:
                os.remove(test_file)
                self.message_queue.put(("log", "Тестовый файл удален", "info"))
            except Exception as e:
                self.message_queue.put(("log", f"Не удалось удалить тестовый файл: {e}", "warning"))

            return True

        except PermissionError:
            self.message_queue.put(("error", f"Нет прав на запись на диск {drive_path}! Запустите от администратора/root."))
            return False
        except Exception as e:
            self.message_queue.put(("error", f"Ошибка записи: {str(e)}"))
            return False

    def verify_test_file(self, test_file, data, expected_size):
        """Верификация записанного файла"""
        try:
            bytes_read = 0
            with open(test_file, 'rb') as f:
                while bytes_read < expected_size:
                    if self.cancel_requested:
                        break

                    read_data = f.read(1024 * 1024)
                    if not read_data:
                        break

                    if bytes_read < len(data) and read_data[:100] != data[:100]:
                        sector = bytes_read // 512
                        self.message_queue.put(("bad_sector", sector, "Ошибка", 1))

                    bytes_read += len(read_data)
        except Exception as e:
            self.message_queue.put(("log", f"Ошибка верификации: {e}", "error"))

    def run_test(self, drive_path):
        """Основная функция тестирования с реальной записью"""
        try:
            # Получаем реальный размер диска
            if platform.system() == "Windows":
                try:
                    import win32file
                    sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = \
                        win32file.GetDiskFreeSpace(drive_path)
                    self.total_size = (total_clusters * sectors_per_cluster * bytes_per_sector) / (1024**3)
                except ImportError:
                    # Fallback
                    self.total_size = psutil.disk_usage(drive_path).total / (1024**3)
            else:
                self.total_size = psutil.disk_usage(drive_path).total / (1024**3)

            self.message_queue.put(("log", f"Размер диска: {self.total_size:.1f} GB", "info"))
            self.message_queue.put(("log", f"Начинаем РЕАЛЬНУЮ запись на диск {drive_path}", "warning"))

            # Основной цикл тестирования
            for pass_num in range(1, self.total_passes + 1):
                if self.cancel_requested:
                    break

                while self.test_paused:
                    time.sleep(0.1)
                    if self.cancel_requested:
                        break

                self.current_pass = pass_num
                self.message_queue.put(("log", f"Проход {pass_num}/{self.total_passes} начат", "info"))

                # Запускаем тесты для выбранных паттернов
                if self.test_write_ones.get():
                    self.message_queue.put(("log", "Тест: запись единиц (0xFF)", "info"))
                    self.write_test_pattern(drive_path, "ones")

                if self.test_write_zeros.get():
                    self.message_queue.put(("log", "Тест: запись нулей (0x00)", "info"))
                    self.write_test_pattern(drive_path, "zeros")

                if self.test_random.get():
                    self.message_queue.put(("log", "Тест: случайные данные", "info"))
                    self.write_test_pattern(drive_path, "random")

                self.message_queue.put(("log", f"Проход {pass_num}/{self.total_passes} завершен", "success"))

                # Обновляем прогресс
                progress = (pass_num / self.total_passes) * 100
                self.message_queue.put(("progress", progress))

            # Форматирование
            if self.format_var.get() and self.fs_var.get() != "Don't format":
                self.message_queue.put(("log", f"Форматирование в {self.fs_var.get()}...", "info"))
                self.format_drive(drive_path, self.fs_var.get())
                self.message_queue.put(("log", "Форматирование завершено", "success"))

            if not self.cancel_requested:
                self.message_queue.put(("complete", "Тестирование успешно завершено!"))
            else:
                self.message_queue.put(("log", "Тест прерван пользователем", "warning"))

        except Exception as e:
            self.message_queue.put(("error", f"Ошибка тестирования: {str(e)}"))
            import traceback
            traceback.print_exc()

    def pause_test(self):
        """Пауза/продолжение теста"""
        if self.test_running:
            if not self.test_paused:
                self.test_paused = True
                self.pause_button.config(text="▶ ПРОДОЛЖИТЬ", bg=self.colors["success"])
                self.log_message("Тест приостановлен", "warning")
            else:
                self.test_paused = False
                self.pause_button.config(text="⏸ ПАУЗА", bg="#555555")
                self.log_message("Тест продолжен", "success")

    def stop_test(self):
        """Остановка теста"""
        if self.test_running:
            if messagebox.askyesno(
                "Подтверждение",
                "Прервать тестирование?\nТекущий проход будет завершен.",
            ):
                self.cancel_requested = True
                self.log_message("Запрошена остановка теста...", "warning")
                self.stop_button.config(state="disabled")

    def update_stats_timer(self):
        """Таймер обновления статистики"""
        if hasattr(self, 'stat_size_total') and hasattr(self, 'total_size'):
            self.stat_size_total.set(f"{self.total_size:.1f} GB")

            # Расчет оставшегося времени
            if hasattr(self, "current_position") and hasattr(self, "total_size"):
                if self.current_position > 0:
                    elapsed = (datetime.now() - self.test_start_time).total_seconds()
                    speed = self.current_position / elapsed if elapsed > 0 else 0
                    remaining_gb = (
                        self.total_size * (self.total_passes - self.current_pass + 1)
                        - self.current_position
                    )
                    remaining = remaining_gb / speed if speed > 0 else 0

                    if remaining > 0:
                        remaining_str = str(timedelta(seconds=int(remaining)))
                        self.time_label.config(text=f"Осталось: {remaining_str}")

        self.root.after(1000, self.update_stats_timer)

    def check_queue(self):
        """Проверка очереди сообщений с поддержкой различных форматов"""
        try:
            while True:
                msg = self.message_queue.get_nowait()

                # Поддержка разных форматов сообщений
                if isinstance(msg, tuple):
                    msg_type = msg[0]

                    if msg_type == "log":
                        # Форматы: (type, message, level) или (type, message, level, extra)
                        if len(msg) >= 3:
                            message, level = msg[1], msg[2]
                        else:
                            message, level = msg[1], "info"
                        self.log_message(message, level)

                    elif msg_type == "speed":
                        if len(msg) >= 3:
                            self.update_speed_chart(msg[1], msg[2])

                    elif msg_type == "progress":
                        self.progress_bar["value"] = msg[1]
                        self.progress_label.config(text=f"Прогресс: {msg[1]:.1f}%")

                    elif msg_type == "bad_sector":
                        if len(msg) >= 4:
                            sector, status, attempts = msg[1], msg[2], msg[3]
                        else:
                            continue

                        self.bad_sectors_tree.insert(
                            "", "end", values=(sector, status, attempts)
                        )
                        if sector not in self.bad_sectors:
                            self.bad_sectors.append(sector)

                    elif msg_type == "complete":
                        self.test_complete(msg[1])

                    elif msg_type == "error":
                        self.test_error(msg[1])

                elif isinstance(msg, dict):
                    # Альтернативный формат: словарь с ключами
                    msg_type = msg.get('type')
                    if msg_type == 'log':
                        self.log_message(msg.get('message'), msg.get('level', 'info'))
                    elif msg_type == 'speed':
                        self.update_speed_chart(msg.get('speed'), msg.get('time'))
                    # ... и т.д.

        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def test_complete(self, message):
        """Завершение теста"""
        self.test_running = False
        self.test_paused = False
        self.cancel_requested = False

        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸ ПАУЗА", bg="#555555")
        self.stop_button.config(state="disabled")

        self.progress_bar["value"] = 100
        self.progress_label.config(text="Тестирование завершено")
        self.time_label.config(text="Осталось: --:--:--")

        self.log_message(message, "success")

        # Финальное обновление статистики
        self.update_stats()

        # Показать итоговую статистику
        stats_text = f"""
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО

Итоговая статистика:
• Проходов выполнено: {self.current_pass}/{self.total_passes}
• Битых секторов: {len(self.bad_sectors)}
• Средняя скорость: {self.stat_speed_avg.get()}
• Максимальная скорость: {self.stat_speed_max.get()}
• Общее время: {self.stat_time_total.get()}
• Размер диска: {self.total_size:.1f} GB

Рекомендация: {'✅ Диск исправен' if len(self.bad_sectors) == 0 else f'⚠️ Найдено {len(self.bad_sectors)} битых секторов'}
"""

        messagebox.showinfo("Тестирование завершено", stats_text)

        # Автосохранение отчета если включено
        if self.config["app"]["auto_save_log"]:
            auto_filename = (
                f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            try:
                self.export_text_report(auto_filename)
                self.log_message(f"Автосохранен отчет: {auto_filename}", "info")
            except Exception as e:
                self.log_message(f"Ошибка автосохранения: {str(e)}", "error")

    def test_error(self, error_msg):
        """Обработка ошибки"""
        self.test_running = False
        self.test_paused = False
        self.cancel_requested = False

        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="⏸ ПАУЗА", bg="#555555")
        self.stop_button.config(state="disabled")

        self.log_message(f"Ошибка: {error_msg}", "error")
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error_msg}")

    def format_drive(self, drive_path, filesystem):
        """Форматирование диска"""
        try:
            self.message_queue.put(("log", f"Форматирование {drive_path} в {filesystem}...", "warning"))

            if platform.system() == "Windows":
                # Для Windows используем format.com
                import subprocess
                drive_letter = drive_path[0]
                self.message_queue.put(("log", f"Запуск format.com {drive_letter}:", "info"))

                # format.com требует интерактивного подтверждения, используем echo y
                cmd = f'cmd /c echo y | format.com {drive_letter}: /FS:{filesystem} /Q'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    self.message_queue.put(("log", f"Диск {drive_letter}: отформатирован", "success"))
                else:
                    self.message_queue.put(("log", f"Ошибка форматирования: {result.stderr}", "error"))

            elif platform.system() == "Linux":
                import subprocess
                if filesystem == "FAT32":
                    cmd = ['mkfs.vfat', '-F32', drive_path]
                elif filesystem == "EXT4":
                    cmd = ['mkfs.ext4', '-F', drive_path]
                elif filesystem == "exFAT":
                    cmd = ['mkfs.exfat', drive_path]
                else:
                    return False

                # Пытаемся с sudo, если не root
                if os.geteuid() != 0:
                    cmd = ['sudo'] + cmd

                subprocess.run(cmd, check=True)
                self.message_queue.put(("log", f"Диск {drive_path} отформатирован", "success"))

            elif platform.system() == "Darwin":  # macOS
                import subprocess
                disk_id = os.path.basename(drive_path)
                if filesystem == "FAT32":
                    cmd = ['diskutil', 'eraseDisk', 'FAT32', 'SD_CARD', disk_id]
                elif filesystem == "exFAT":
                    cmd = ['diskutil', 'eraseDisk', 'exFAT', 'SD_CARD', disk_id]
                else:
                    return False

                subprocess.run(cmd, check=True)
                self.message_queue.put(("log", f"Диск отформатирован", "success"))

            return True

        except Exception as e:
            self.message_queue.put(("error", f"Ошибка форматирования: {str(e)}"))
            return False

    def create_drive_context_menu(self):
        """Контекстное меню для списка дисков"""
        self.drive_context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors["bg_light"], fg="white")
        self.drive_context_menu.add_command(
            label="✏️ Переименовать",
            command=self.rename_drive
        )
        self.drive_context_menu.add_command(
            label="🔄 Обновить",
            command=self.refresh_drives_list
        )
        self.drive_context_menu.add_separator()
        self.drive_context_menu.add_command(
            label="📊 Свойства",
            command=self.show_drive_properties
        )

        # Привязываем правый клик
        self.drive_tree.bind("<Button-3>", self.show_drive_context_menu)

    def show_drive_context_menu(self, event):
        """Показать контекстное меню"""
        # Выделяем элемент под курсором
        item = self.drive_tree.identify_row(event.y)
        if item:
            self.drive_tree.selection_set(item)
            self.drive_context_menu.post(event.x_root, event.y_root)

    def show_drive_properties(self):
        """Показать свойства диска"""
        selection = self.drive_tree.selection()
        if not selection:
            return

        item = self.drive_tree.item(selection[0])
        values = item["values"]
        drive_path = values[0]

        try:
            usage = psutil.disk_usage(drive_path)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)

            props_text = f"""
    Свойства диска: {drive_path}
    
    Тип: {values[1]}
    Файловая система: {values[3]}
    Размер: {values[2]}
    
    Использовано: {used_gb:.1f} GB
    Свободно: {free_gb:.1f} GB
    Занято: {usage.percent}%
    
    Метка тома: {self.get_volume_label(drive_path)}
    """
            messagebox.showinfo("Свойства диска", props_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить свойства:\n{str(e)}")

    def get_volume_label(self, drive_path):
        """Получить метку тома"""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32

                # Буфер для имени тома
                volume_name_buffer = ctypes.create_unicode_buffer(256)

                root_path = drive_path
                if not root_path.endswith('\\'):
                    root_path += '\\'

                # GetVolumeInformationW API
                success = kernel32.GetVolumeInformationW(
                    root_path,
                    volume_name_buffer,
                    len(volume_name_buffer),
                    None, None, None, None, 0
                )

                if success and volume_name_buffer.value:
                    return volume_name_buffer.value
                return "Нет метки"

            elif platform.system() == "Linux":
                import subprocess
                result = subprocess.run(['blkid', '-o', 'value', '-s', 'LABEL', drive_path],
                                        capture_output=True, text=True)
                label = result.stdout.strip()
                return label if label else "Нет метки"

            elif platform.system() == "Darwin":
                import subprocess
                disk_id = os.path.basename(drive_path)
                result = subprocess.run(['diskutil', 'info', disk_id],
                                        capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Volume Name' in line:
                        label = line.split(':')[1].strip()
                        return label if label else "Нет метки"
                return "Нет метки"
        except Exception as e:
            print(f"Ошибка получения метки тома: {e}")
            return "Не определено"

    def run(self):
        """Запуск приложения"""
        # Центрирование окна
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.mainloop()

    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.test_running:
            if messagebox.askyesno(
                "Подтверждение",
                "Тестирование выполняется. Вы уверены, что хотите выйти?\n"
                "Текущий прогресс будет потерян.",
            ):
                self.cancel_requested = True
                time.sleep(0.5)  # Даем время для безопасного завершения
                self.root.quit()  # Используем quit вместо destroy
        else:
            self.root.quit()

    def show_error_log(self):
        """Показать журнал ошибок"""
        try:
            from error_logger import get_logger
            logger = get_logger()
            ErrorReportDialog(self.root, logger)
        except Exception as e:
            error_logger.log_exception(e, module="main")
            messagebox.showerror("Ошибка", f"Не удалось открыть журнал ошибок:\n{str(e)}")


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик необработанных исключений"""
    error_logger = get_logger()

    # Логируем критическую ошибку
    error_logger.log_error(
        f"Необработанное исключение: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

    # Создаем crash report
    crash_file = error_logger.create_crash_report(f"{exc_type.__name__}: {exc_value}")

    # Показываем сообщение пользователю
    try:
        import tkinter.messagebox as tkmb
        error_msg = f"Произошла критическая ошибка:\n\n{exc_type.__name__}: {exc_value}\n\n"
        if crash_file:
            error_msg += f"Отчет сохранен в:\n{crash_file}"
        else:
            error_msg += "Не удалось сохранить отчет об ошибке."

        tkmb.showerror("Критическая ошибка", error_msg)
    except:
        print(f"Критическая ошибка: {exc_type.__name__}: {exc_value}")
        if crash_file:
            print(f"Отчет сохранен: {crash_file}")

    # Вызываем стандартный обработчик
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def main():
    """Точка входа в программу"""

    # Устанавливаем глобальный обработчик исключений
    sys.excepthook = global_exception_handler

    try:
        # Инициализируем логгер
        from error_logger import get_logger
        logger = get_logger()

        # Логируем запуск
        logger.log_info("="*50)
        logger.log_info("ЗАПУСК SD CARD TESTER PRO")
        logger.log_info("="*50)

        # Проверка зависимостей
        required_modules = [
            ("tkinter", "tkinter"),
            ("psutil", "psutil"),
            ("matplotlib", "matplotlib"),
            ("numpy", "numpy"),
        ]

        missing_modules = []
        for import_name, package_name in required_modules:
            try:
                __import__(import_name)
                logger.log_debug(f"Модуль {package_name} загружен")
            except ImportError as e:
                missing_modules.append(package_name)
                logger.log_error(f"Модуль {package_name} не найден: {e}")

        if missing_modules:
            error_msg = f"Не установлены необходимые библиотеки: {', '.join(missing_modules)}\n"
            error_msg += "Установите их командой: pip install " + " ".join(missing_modules)
            logger.log_error(error_msg)
            print(error_msg)

            # Пытаемся предложить установку
            if platform.system() == "Windows":
                try:
                    import tkinter.messagebox as tkmb
                    if tkmb.askyesno(
                            "Ошибка зависимостей",
                            f"Не установлены: {', '.join(missing_modules)}\n"
                            "Хотите установить автоматически?"
                    ):
                        import subprocess
                        logger.log_info("Запуск автоматической установки зависимостей...")
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install"] + missing_modules
                        )
                        # Перезапуск после установки
                        logger.log_info("Перезапуск программы...")
                        os.execv(sys.executable, ["python"] + sys.argv)
                except:
                    pass

            sys.exit(1)

        # Запуск приложения
        logger.log_info("Инициализация приложения...")
        app = AdvancedSDCardTester()

        # Сохраняем логгер в app для доступа из других методов
        app.error_logger = logger

        logger.log_info("Запуск главного окна...")
        app.run()

    except Exception as e:
        logger = get_logger()
        logger.log_exception(e, module="main")
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
