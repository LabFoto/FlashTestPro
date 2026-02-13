"""
Главный модуль приложения SD Card Tester Pro
Объединяет UI и бизнес-логику
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import platform
import os
import sys
import time
from datetime import datetime
import webbrowser
import psutil

from error_logger import get_logger, global_exception_handler
from business_logic import TesterLogic
from ui_components import (
    Theme, DriveTreeView, SpeedChart, LogViewer,
    StatisticsPanel, InfoPanel, ProgressPanel, TestSettingsPanel
)
from error_report_dialog import ErrorReportDialog
import locales

class SDCardTesterApp:
    """Главный класс приложения"""
    
    def __init__(self):
        # Устанавливаем глобальный обработчик исключений
        sys.excepthook = global_exception_handler
        
        # Логгер
        self.logger = get_logger()
        self.logger.log_info("=" * 50)
        self.logger.log_info("ЗАПУСК SD CARD TESTER PRO")
        self.logger.log_info("=" * 50)
        
        # Бизнес-логика
        self.logic = TesterLogic()
        self.logic.load_config()
        
        # Текущий язык
        self.current_language = self.logic.config["ui"].get("language", "ru")
        
        # Тема
        self.theme_name = self.logic.config["ui"].get("theme", "dark")
        self.colors = Theme.get_colors(self.theme_name)
        
        # Создание главного окна
        self.root = tk.Tk()
        self.root.title(locales.get_translation(self.current_language, "app_title", "SD Card Tester Pro"))
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        
        # Применение темы
        Theme.apply_style(self.root, self.colors)
        
        # Настройка иконки
        self._setup_icon()
        
        # Создание интерфейса
        self._create_ui()
        
        # Настройка обработки сообщений
        self._setup_message_handling()
        
        # Проверка прав администратора
        self._check_admin()
        
        # Обновление системной информации
        self._update_system_info()
        
        # Регистрация коллбеков
        self._register_callbacks()
        
        self.logger.log_info("Приложение инициализировано успешно")
    
    # ========== ИНИЦИАЛИЗАЦИЯ ==========
    
    def _setup_icon(self):
        """Настройка иконки приложения"""
        icon_files = {
            "Windows": "icon.ico",
            "Linux": "icon.png",
            "Darwin": "icon.icns",
        }
        
        current_os = platform.system()
        icon_file = icon_files.get(current_os, "icon.ico")
        
        if os.path.exists(icon_file):
            try:
                if current_os == "Windows":
                    self.root.iconbitmap(icon_file)
                elif current_os == "Linux":
                    icon = tk.PhotoImage(file=icon_file)
                    self.root.iconphoto(True, icon)
            except Exception as e:
                self.logger.log_debug(f"Не удалось загрузить иконку: {e}")
    
    def _check_admin(self):
        """Проверка прав администратора"""
        if not self.logic.is_admin():
            self.logger.log_warning(
                "Для полного доступа к устройствам рекомендуется запустить программу от имени администратора/root"
            )
            self._show_admin_warning()
    
    def _show_admin_warning(self):
        """Показ предупреждения о правах администратора"""
        warning_text = locales.get_translation(
            self.current_language,
            "warning_admin",
            "⚠️  Предупреждение:\nДля полного доступа к устройствам рекомендуется запустить программу от имени администратора/root.\nНекоторые функции могут быть недоступны."
        )
        self.log_viewer.log(warning_text, "warning")
    
    # ========== СОЗДАНИЕ ИНТЕРФЕЙСА ==========
    
    def _create_ui(self):
        """Создание пользовательского интерфейса"""
        # Главное меню
        self._create_menu()
        
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая панель с прокруткой
        self._create_left_panel(main_container)
        
        # Правая панель
        self._create_right_panel(main_container)
        
        # Обновление списка дисков
        self._refresh_drives()
    
    def _create_left_panel(self, parent):
        """Создание левой панели"""
        # Canvas и Scrollbar для левой панели
        left_canvas = tk.Canvas(
            parent,
            bg=self.colors["bg_dark"],
            highlightthickness=0,
            width=800
        )
        left_scrollbar = ttk.Scrollbar(
            parent,
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
        
        left_canvas.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_scrollbar.pack(side="left", fill="y")
        
        # Привязка колеса мыши
        self._bind_mousewheel(left_canvas)
        
        # Заголовок
        self._create_header(left_scrollable_frame)
        
        # Выбор языка
        self._create_language_selector(left_scrollable_frame)
        
        # Выбор диска
        self._create_drive_selector(left_scrollable_frame)
        
        # Настройки теста
        self._create_test_settings(left_scrollable_frame)
        
        # Управление тестом
        self._create_test_controls(left_scrollable_frame)
        
        # Прогресс
        self._create_progress_panel(left_scrollable_frame)
    
    def _create_header(self, parent):
        """Создание заголовка"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 15))
        
        self.main_title_label = ttk.Label(
            header_frame,
            text=locales.get_translation(self.current_language, "main_title", "🔧 SD CARD TESTER PRO"),
            font=("Segoe UI", 20, "bold"),
            foreground=self.colors["accent"],
        )
        self.main_title_label.pack(anchor="w")
        
        self.subtitle_label = ttk.Label(
            header_frame,
            text=locales.get_translation(self.current_language, "subtitle", "Профессиональное тестирование накопителей"),
            font=("Segoe UI", 10),
        )
        self.subtitle_label.pack(anchor="w")
    
    def _create_language_selector(self, parent):
        """Создание селектора языка"""
        language_frame = ttk.Frame(parent)
        language_frame.pack(fill="x", pady=(0, 15))
        
        self.language_label = ttk.Label(
            language_frame,
            text=locales.get_translation(self.current_language, "language", "Язык / Language / 语言:")
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
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
    
    def _create_drive_selector(self, parent):
        """Создание компонента выбора диска"""
        drive_frame = ttk.LabelFrame(
            parent,
            text=" " + locales.get_translation(self.current_language, "drive_selection", "ВЫБОР НАКОПИТЕЛЯ") + " ",
            padding=15
        )
        drive_frame.pack(fill="x", pady=(0, 15))
        
        # Кнопка обновления
        self.refresh_button = ttk.Button(
            drive_frame,
            text=locales.get_translation(self.current_language, "refresh_list", "🔄 Обновить список"),
            command=self._refresh_drives,
            width=25,
        )
        self.refresh_button.pack(pady=(0, 10))
        
        # Treeview для дисков
        self.drive_tree = DriveTreeView(
            drive_frame,
            self.colors,
            on_select_callback=self._on_drive_select
        )
        self.drive_tree.pack(fill="x")
        
        # Информация о выбранном диске
        self.drive_info_label = ttk.Label(
            drive_frame,
            text=locales.get_translation(self.current_language, "select_drive", "Выберите накопитель для тестирования"),
            font=("Segoe UI", 9),
            foreground=self.colors["warning"],
            wraplength=350
        )
        self.drive_info_label.pack(anchor="w", pady=(10, 0))
        
        # Привязка контекстного меню
        self.drive_tree.context_menu.entryconfigure(0, command=self._rename_drive)
        self.drive_tree.context_menu.entryconfigure(1, command=self._refresh_drives)
        self.drive_tree.context_menu.entryconfigure(3, command=self._show_drive_properties)
    
    def _create_test_settings(self, parent):
        """Создание панели настроек теста"""
        self.settings_panel = TestSettingsPanel(
            parent,
            self.colors,
            on_start_callback=self._start_test
        )
        self.settings_panel.pack(fill="x", pady=(0, 15))
        
        # Привязка кнопки переименования
        self.settings_panel.rename_button.config(command=self._rename_drive)
    
    def _create_test_controls(self, parent):
        """Создание панели управления тестом"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 15))
        
        self.start_button = tk.Button(
            control_frame,
            text=locales.get_translation(self.current_language, "start_test", "🚀 НАЧАТЬ"),
            command=self._start_test,
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
            text=locales.get_translation(self.current_language, "pause", "⏸ ПАУЗА"),
            command=self._pause_test,
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
            text=locales.get_translation(self.current_language, "stop", "⏹ ОСТАНОВИТЬ"),
            command=self._stop_test,
            bg=self.colors["danger"],
            fg="white",
            font=("Segoe UI", 11),
            relief="flat",
            state="disabled",
            width=12,
        )
        self.stop_button.pack(side="left")
    
    def _create_progress_panel(self, parent):
        """Создание панели прогресса"""
        self.progress_panel = ProgressPanel(parent, self.colors)
        self.progress_panel.pack(fill="x", pady=(0, 15))
    
    def _create_right_panel(self, parent):
        """Создание правой панели с вкладками"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)
        
        # Вкладка 1: График скорости
        speed_tab = ttk.Frame(self.notebook)
        self.notebook.add(speed_tab, text=locales.get_translation(self.current_language, "tab_speed", "📈 ГРАФИК СКОРОСТИ"))
        self.speed_chart = SpeedChart(speed_tab, self.colors)
        self.speed_chart.pack(fill="both", expand=True)
        
        # Вкладка 2: Статистика
        stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(stats_tab, text=locales.get_translation(self.current_language, "tab_stats", "📊 СТАТИСТИКА"))
        self.stats_panel = StatisticsPanel(stats_tab, self.colors)
        self.stats_panel.pack(fill="both", expand=True)
        
        # Вкладка 3: Лог
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text=locales.get_translation(self.current_language, "tab_log", "📝 ЛОГ СОБЫТИЙ"))
        self.log_viewer = LogViewer(log_tab, self.colors)
        self.log_viewer.pack(fill="both", expand=True)
        
        # Вкладка 4: Информация
        info_tab = ttk.Frame(self.notebook)
        self.notebook.add(info_tab, text=locales.get_translation(self.current_language, "tab_info", "ℹ️ ИНФОРМАЦИЯ"))
        self.info_panel = InfoPanel(info_tab, self.colors)
        self.info_panel.pack(fill="both", expand=True)
        
        # Привязка кнопок информации
        self._bind_info_buttons()
    
    def _bind_info_buttons(self):
        """Привязка кнопок на информационной панели"""
        if hasattr(self.info_panel, 'buttons'):
            if 'documentation' in self.info_panel.buttons:
                self.info_panel.buttons['documentation'].config(command=self._open_documentation)
            if 'check_updates' in self.info_panel.buttons:
                self.info_panel.buttons['check_updates'].config(command=self._check_updates)
            if 'report_bug' in self.info_panel.buttons:
                self.info_panel.buttons['report_bug'].config(command=self._report_bug)
            if 'error_log' in self.info_panel.buttons:
                self.info_panel.buttons['error_log'].config(command=self._show_error_log)
    
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
    
    # ========== МЕНЮ ==========
    
    def _create_menu(self):
        """Создание главного меню"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])
        
        # Меню Файл
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_file", "Файл"), menu=self.file_menu)
        self.file_menu.add_command(label=t.get("menu_save_log", "Сохранить лог..."), command=self._save_log)
        self.file_menu.add_command(label=t.get("menu_export", "Экспорт отчета..."), command=self._export_report)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=t.get("menu_settings", "Настройки..."), command=self._open_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=t.get("menu_exit", "Выход"), command=self._on_closing)
        
        # Меню Вид
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_view", "Вид"), menu=self.view_menu)
        self.view_menu.add_command(label=t.get("refresh_list", "Обновить список дисков"), command=self._refresh_drives)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=t.get("clear_log", "Очистить лог"), command=self._clear_log)
        self.view_menu.add_command(label=t.get("reset_stats", "Сбросить статистику"), command=self._reset_stats)
        
        # Меню Тестирование
        self.test_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_test", "Тестирование"), menu=self.test_menu)
        self.test_menu.add_command(
            label=t.get("fast_pass", "Быстрый тест (1 проход)"),
            command=lambda: self.settings_panel.set_passes(1)
        )
        self.test_menu.add_command(
            label=t.get("standard_pass", "Стандартный тест (3 прохода)"),
            command=lambda: self.settings_panel.set_passes(3)
        )
        self.test_menu.add_command(
            label=t.get("full_pass", "Полный тест (7 проходов)"),
            command=lambda: self.settings_panel.set_passes(7)
        )
        self.test_menu.add_separator()
        self.test_menu.add_command(
            label=t.get("start_test", "Начать тест"),
            command=self._start_test
        )
        self.test_menu.add_command(
            label=t.get("pause", "Приостановить тест"),
            command=self._pause_test
        )
        self.test_menu.add_command(
            label=t.get("stop", "Остановить тест"),
            command=self._stop_test
        )
        
        # Меню Справка
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t.get("menu_help", "Справка"), menu=self.help_menu)
        self.help_menu.add_command(
            label=t.get("documentation", "Документация"),
            command=self._open_documentation
        )
        self.help_menu.add_command(
            label="📋 Журнал ошибок",
            command=self._show_error_log
        )
        self.help_menu.add_separator()
        self.help_menu.add_command(
            label=t.get("about", "О программе"),
            command=self._show_about
        )
        self.help_menu.add_command(
            label=t.get("check_updates", "Проверить обновления"),
            command=self._check_updates
        )
    
    # ========== ОБРАБОТКА СОБЫТИЙ UI ==========
    
    def _refresh_drives(self):
        """Обновление списка дисков"""
        drives = self.logic.get_drives_list()
        self.drive_tree.update_drives(drives)
        self.log_viewer.log(f"Найдено дисков: {len(drives)}", "info")
    
    def _on_drive_select(self, event):
        """Обработка выбора диска"""
        drive = self.drive_tree.get_selected_drive()
        
        if drive:
            if drive["is_system"]:
                self.drive_info_label.config(
                    text=locales.get_translation(
                        self.current_language,
                        "system_drive_warning",
                        "⚠️  ВНИМАНИЕ: Выбран СИСТЕМНЫЙ диск! Тестирование запрещено!"
                    ),
                    foreground=self.colors["danger"],
                )
                self.start_button.config(state="disabled")
            else:
                self.drive_info_label.config(
                    text=locales.get_translation(
                        self.current_language,
                        "selected_drive",
                        "Выбран диск: {} (тип: {}, размер: {}, ФС: {})"
                    ).format(drive["path"], drive["type"], drive["size"], drive["fs"]),
                    foreground=self.colors["success"],
                )
                self.start_button.config(state="normal")
    
    def _on_language_change(self, event):
        """Обработка изменения языка"""
        new_lang = self.language_var.get()
        self._change_language(new_lang)
    
    def _change_language(self, lang):
        """Изменение языка интерфейса"""
        if lang in locales.TRANSLATIONS:
            self.current_language = lang
            self.logic.update_config("ui", "language", lang)
            self.logic.save_config()
            
            # Обновление UI компонентов
            self._update_ui_language()
            
            self.log_viewer.log(f"Язык изменен на {lang}", "info")
    
    def _update_ui_language(self):
        """Обновление языка во всех компонентах"""
        t = locales.TRANSLATIONS.get(self.current_language, locales.TRANSLATIONS["ru"])
        
        # Заголовок окна
        self.root.title(t.get("app_title", "SD Card Tester Pro"))
        
        # Заголовки
        self.main_title_label.config(text=t.get("main_title", "🔧 SD CARD TESTER PRO"))
        self.subtitle_label.config(text=t.get("subtitle", "Профессиональное тестирование накопителей"))
        
        # Язык
        self.language_label.config(text=t.get("language", "Язык / Language / 语言:"))
        
        # Компоненты
        self.drive_tree.update_language(self.current_language)
        self.speed_chart.update_language(self.current_language)
        self.stats_panel.update_language(self.current_language)
        self.info_panel.update_language(self.current_language)
        self.progress_panel.update_language(self.current_language)
        self.settings_panel.update_language(self.current_language)
        
        # Кнопки
        self.refresh_button.config(text=t.get("refresh_list", "🔄 Обновить список"))
        self.start_button.config(text=t.get("start_test", "🚀 НАЧАТЬ"))
        
        if self.logic.test_paused:
            self.pause_button.config(text=t.get("resume", "▶ ПРОДОЛЖИТЬ"))
        else:
            self.pause_button.config(text=t.get("pause", "⏸ ПАУЗА"))
        
        self.stop_button.config(text=t.get("stop", "⏹ ОСТАНОВИТЬ"))
        
        # Вкладки
        tabs = self.notebook.tabs()
        if len(tabs) >= 1:
            self.notebook.tab(tabs[0], text=t.get("tab_speed", "📈 ГРАФИК СКОРОСТИ"))
        if len(tabs) >= 2:
            self.notebook.tab(tabs[1], text=t.get("tab_stats", "📊 СТАТИСТИКА"))
        if len(tabs) >= 3:
            self.notebook.tab(tabs[2], text=t.get("tab_log", "📝 ЛОГ СОБЫТИЙ"))
        if len(tabs) >= 4:
            self.notebook.tab(tabs[3], text=t.get("tab_info", "ℹ️ ИНФОРМАЦИЯ"))
        
        # Пересоздание меню
        self._create_menu()
    
    def _rename_drive(self):
        """Переименование диска"""
        drive = self.drive_tree.get_selected_drive()
        if not drive:
            messagebox.showwarning(
                locales.get_translation(self.current_language, "warning", "Предупреждение"),
                locales.get_translation(self.current_language, "select_drive", "Выберите диск для переименования!")
            )
            return
        
        if drive["is_system"]:
            messagebox.showerror(
                locales.get_translation(self.current_language, "error", "Ошибка"),
                locales.get_translation(self.current_language, "error_system_drive", "Нельзя переименовать системный диск!")
            )
            return
        
        # Диалог ввода имени
        self._show_rename_dialog(drive)
    
    def _show_rename_dialog(self, drive):
        """Показать диалог переименования"""
        dialog = tk.Toplevel(self.root)
        dialog.title(locales.get_translation(self.current_language, "rename_drive_title", "Переименовать диск"))
        dialog.geometry("450x180")
        dialog.configure(bg=self.colors["bg_dark"])
        dialog.resizable(False, False)
        
        # Центрирование
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Текущее имя
        current_label = self.logic.get_volume_label(drive["path"])
        
        ttk.Label(
            dialog,
            text=f"{locales.get_translation(self.current_language, 'drive', 'Диск')}: {drive['path']}",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(15, 5))
        
        ttk.Label(
            dialog,
            text=f"{locales.get_translation(self.current_language, 'current_label', 'Текущая метка')}: {current_label}"
        ).pack(pady=(0, 10))
        
        frame = ttk.Frame(dialog)
        frame.pack(pady=10)
        
        ttk.Label(
            frame,
            text=locales.get_translation(self.current_language, 'new_name', 'Новое имя:')
        ).pack(side="left", padx=(0, 10))
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=name_var, width=25)
        name_entry.pack(side="left")
        name_entry.focus()
        
        def do_rename():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showwarning(
                    locales.get_translation(self.current_language, "warning", "Предупреждение"),
                    locales.get_translation(self.current_language, "enter_drive_name", "Введите имя диска!")
                )
                return
            
            success, message = self.logic.rename_drive(drive["path"], new_name)
            
            if success:
                messagebox.showinfo(
                    locales.get_translation(self.current_language, "success", "Успех"),
                    message
                )
                dialog.destroy()
                self._refresh_drives()
            else:
                messagebox.showerror(
                    locales.get_translation(self.current_language, "error", "Ошибка"),
                    message
                )
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(15, 10))
        
        ttk.Button(
            btn_frame,
            text=locales.get_translation(self.current_language, "rename", "Переименовать"),
            command=do_rename
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text=locales.get_translation(self.current_language, "cancel", "Отмена"),
            command=dialog.destroy
        ).pack(side="left", padx=5)
        
        name_entry.bind('<Return>', lambda e: do_rename())
    
    def _show_drive_properties(self):
        """Показать свойства диска"""
        drive = self.drive_tree.get_selected_drive()
        if not drive:
            return
        
        info = self.logic.get_drive_info(drive["path"])
        
        props_text = f"""
{locales.get_translation(self.current_language, 'drive', 'Диск')}: {drive['path']}

{locales.get_translation(self.current_language, 'type', 'Тип')}: {drive['type']}
{locales.get_translation(self.current_language, 'filesystem', 'ФС')}: {drive['fs']}
{locales.get_translation(self.current_language, 'size', 'Размер')}: {drive['size']}

{locales.get_translation(self.current_language, 'stats_tested', 'Использовано')}: {info['used_bytes'] / (1024**3):.1f} GB
{locales.get_translation(self.current_language, 'stats_tested', 'Свободно')}: {info['free_bytes'] / (1024**3):.1f} GB
{locales.get_translation(self.current_language, 'stats_tested', 'Занято')}: {info['percent_used']}%

{locales.get_translation(self.current_language, 'current_label', 'Метка тома')}: {info['label']}
"""
        messagebox.showinfo(
            locales.get_translation(self.current_language, 'drive_properties', 'Свойства диска'),
            props_text
        )
    
    # ========== ТЕСТИРОВАНИЕ ==========
    
    def _start_test(self):
        """Начало тестирования"""
        drive = self.drive_tree.get_selected_drive()
        if not drive:
            messagebox.showerror(
                locales.get_translation(self.current_language, "error", "Ошибка"),
                locales.get_translation(self.current_language, "error_no_drive", "Выберите диск для тестирования!")
            )
            return
        
        if drive["is_system"]:
            messagebox.showerror(
                locales.get_translation(self.current_language, "error", "Ошибка безопасности"),
                locales.get_translation(self.current_language, "error_system_drive", "Тестирование системных дисков запрещено!\nВыберите съемный носитель.")
            )
            return
        
        # Проверка прав на запись
        if not self.logic.check_write_permissions(drive["path"]):
            messagebox.showerror(
                locales.get_translation(self.current_language, "error", "Ошибка доступа"),
                f"Нет прав на запись на диск {drive['path']}!\nЗапустите программу от имени администратора/root."
            )
            return
        
        # Получение и проверка параметров теста
        params = self.settings_panel.get_test_params()
        valid, error_msg = self.settings_panel.validate_params()
        
        if not valid:
            messagebox.showerror(
                locales.get_translation(self.current_language, "error", "Ошибка"),
                error_msg
            )
            return
        
        # Подтверждение
        if not self._confirm_test_start(drive, params):
            return
        
        # Сброс UI
        self._reset_ui_for_test()
        
        # Запуск теста в логике
        self.logic.start_test(drive["path"], params)
        
        self.log_viewer.log(f"Начало тестирования диска: {drive['path']}", "info")
        self.log_viewer.log(f"Количество проходов: {params['passes']}", "info")
        
        # Запуск таймера обновления
        self._start_update_timer()
    
    def _confirm_test_start(self, drive, params):
        """Подтверждение начала теста"""
        warning_text = f"""
⚠️  КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ  ⚠️

Все данные на диске {drive['path']} будут 
БЕЗВОЗВРАТНО УНИЧТОЖЕНЫ!

Параметры теста:
• Проходов: {params['passes']}
• Запись единиц: {'Да' if params['test_ones'] else 'Нет'}
• Запись нулей: {'Да' if params['test_zeros'] else 'Нет'}
• Случайные данные: {'Да' if params['test_random'] else 'Нет'}
• Проверка чтения: {'Да' if params['test_verify'] else 'Нет'}
• Форматирование: {'Да' if params['auto_format'] else 'Нет'}
• Файловая система: {params['filesystem']}

Вы уверены, что хотите продолжить?
"""
        
        return messagebox.askyesno(
            locales.get_translation(self.current_language, "confirm_title", "ПОДТВЕРЖДЕНИЕ УНИЧТОЖЕНИЯ"),
            warning_text,
            icon="warning"
        )
    
    def _reset_ui_for_test(self):
        """Сброс UI перед тестом"""
        self.speed_chart.clear()
        self.stats_panel.reset()
        self.progress_panel.reset()
        self.log_viewer.clear()
        
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal", text=locales.get_translation(
            self.current_language, "pause", "⏸ ПАУЗА"
        ))
        self.stop_button.config(state="normal")
    
    def _pause_test(self):
        """Пауза/продолжение теста"""
        paused = self.logic.pause_test()
        
        if paused is not None:
            if paused:
                self.pause_button.config(
                    text=locales.get_translation(self.current_language, "resume", "▶ ПРОДОЛЖИТЬ"),
                    bg=self.colors["success"]
                )
            else:
                self.pause_button.config(
                    text=locales.get_translation(self.current_language, "pause", "⏸ ПАУЗА"),
                    bg="#555555"
                )
    
    def _stop_test(self):
        """Остановка теста"""
        if messagebox.askyesno(
            locales.get_translation(self.current_language, "confirm_title", "ПОДТВЕРЖДЕНИЕ"),
            locales.get_translation(self.current_language, "confirm_stop", "Прервать тестирование?\nТекущий проход будет завершен.")
        ):
            self.logic.stop_test()
            self.stop_button.config(state="disabled")
            self.log_viewer.log("Запрошена остановка теста...", "warning")
    
    def _start_update_timer(self):
        """Запуск таймера обновления статистики"""
        self._update_stats()
        self.root.after(1000, self._start_update_timer)
    
    def _update_stats(self):
        """Обновление статистики на UI"""
        if self.logic.test_running:
            stats = self.logic.get_statistics()
            
            # Форматирование для отображения
            display_stats = {
                'total_size': stats['total_size'],
                'tested': stats['current_position'],
                'avg_speed': stats['avg_speed'],
                'max_speed': stats['max_speed'],
                'min_speed': stats['min_speed'],
                'time_total': stats['elapsed_time'],
                'bad_sectors': stats['bad_sectors_count'],
                'passes_complete': stats['current_pass'],
                'passes_remaining': stats['total_passes'] - stats['current_pass'],
                'status': 'Тестирование...' if not stats['test_paused'] else 'На паузе'
            }
            
            self.stats_panel.update_all(display_stats)
            
            # Обновление времени
            if stats['elapsed_seconds'] > 0 and stats['avg_speed'] > 0:
                remaining_gb = stats['total_size'] * (stats['total_passes'] - stats['current_pass'] + 1) - stats['current_position']
                remaining_seconds = remaining_gb * 1024 / stats['avg_speed'] if stats['avg_speed'] > 0 else 0
                
                if remaining_seconds > 0:
                    remaining_str = str(timedelta(seconds=int(remaining_seconds)))
                    self.progress_panel.update_time(remaining_str)
    
    # ========== ОБРАБОТКА СООБЩЕНИЙ ==========
    
    def _setup_message_handling(self):
        """Настройка обработки сообщений из очереди"""
        self.root.after(100, self._process_messages)
    
    def _process_messages(self):
        """Обработка сообщений из очереди"""
        msg = self.logic.get_message()
        
        while msg:
            msg_type = msg[0]
            
            if msg_type == "log":
                if len(msg) >= 3:
                    self.log_viewer.log(msg[1], msg[2])
            
            elif msg_type == "speed":
                if len(msg) >= 3:
                    self.speed_chart.update_data(msg[2], msg[1])
            
            elif msg_type == "progress":
                self.progress_panel.update_progress(msg[1])
                self.progress_panel.update_status(f"Прогресс: {msg[1]:.1f}%")
            
            elif msg_type == "progress_detail":
                pass
            
            elif msg_type == "bad_sector":
                if len(msg) >= 4:
                    self.stats_panel.add_bad_sector(msg[1], msg[2], msg[3])
                    self.log_viewer.log(f"Найден битый сектор: {msg[1]}", "error")
            
            elif msg_type == "complete":
                self._on_test_complete(msg[1])
            
            elif msg_type == "error":
                self._on_test_error(msg[1])
            
            msg = self.logic.get_message()
        
        self.root.after(100, self._process_messages)
    
    def _register_callbacks(self):
        """Регистрация коллбеков для логики"""
        # Можно добавить прямые коллбеки, минуя очередь
        pass
    
    def _on_test_complete(self, message):
        """Обработка завершения теста"""
        self.log_viewer.log(message, "success")
        
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text=locales.get_translation(
            self.current_language, "pause", "⏸ ПАУЗА"
        ), bg="#555555")
        self.stop_button.config(state="disabled")
        
        self.progress_panel.update_progress(100)
        self.progress_panel.update_status("Тестирование завершено")
        self.progress_panel.update_time("--:--:--")
        
        # Показ итоговой статистики
        stats = self.logic.get_statistics()
        self._show_test_results(stats)
        
        # Автосохранение
        if self.logic.config["app"].get("auto_save_log", False):
            self._auto_save_report()
    
    def _on_test_error(self, error_msg):
        """Обработка ошибки теста"""
        self.log_viewer.log(f"Ошибка: {error_msg}", "error")
        
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text=locales.get_translation(
            self.current_language, "pause", "⏸ ПАУЗА"
        ), bg="#555555")
        self.stop_button.config(state="disabled")
        
        messagebox.showerror(
            locales.get_translation(self.current_language, "error", "Ошибка"),
            f"Произошла ошибка:\n{error_msg}"
        )
    
    def _show_test_results(self, stats):
        """Показать результаты теста"""
        results_text = f"""
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО

Итоговая статистика:
• Проходов выполнено: {stats['current_pass']}/{stats['total_passes']}
• Битых секторов: {stats['bad_sectors_count']}
• Средняя скорость: {stats['avg_speed']:.1f} MB/s
• Максимальная скорость: {stats['max_speed']:.1f} MB/s
• Общее время: {stats['elapsed_time']}

Рекомендация: {'✅ Диск исправен' if stats['bad_sectors_count'] == 0 else f'⚠️ Найдено {stats['bad_sectors_count']} битых секторов'}
"""
        
        messagebox.showinfo(
            locales.get_translation(self.current_language, "test_complete", "Тестирование завершено"),
            results_text
        )
    
    # ========== ОБНОВЛЕНИЕ ИНФОРМАЦИИ ==========
    
    def _update_system_info(self):
        """Обновление системной информации на панели"""
        sys_info = self.logic.get_system_info()
        
        # Форматирование памяти
        memory_total = sys_info['memory_total'] / (1024**3)
        memory_used = sys_info['memory_used'] / (1024**3)
        sys_info['memory'] = f"{memory_total:.1f} GB ({sys_info['memory_percent']}% used)"
        
        self.info_panel.update_system_info(sys_info)
        self.info_panel.update_about_info(
            version=self.logic.config["app"]["version"],
            author="SD Card Tester Team",
            license="MIT",
            github="github.com/yourusername/sd-card-tester-pro"
        )
    
    # ========== ДЕЙСТВИЯ ПОЛЬЗОВАТЕЛЯ ==========
    
    def _save_log(self):
        """Сохранение лога"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_viewer.get_content())
                self.log_viewer.log(f"Лог сохранен: {filename}", "success")
            except Exception as e:
                self.log_viewer.log(f"Ошибка сохранения: {str(e)}", "error")
    
    def _export_report(self):
        """Экспорт отчета"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("HTML files", "*.html"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )
        
        if filename:
            if filename.endswith(".html"):
                format_type = 'html'
            elif filename.endswith(".json"):
                format_type = 'json'
            else:
                format_type = 'txt'
            
            if self.logic.export_report(filename, format_type):
                self.log_viewer.log(f"Отчет экспортирован: {filename}", "success")
            else:
                self.log_viewer.log(f"Ошибка экспорта отчета", "error")
    
    def _auto_save_report(self):
        """Автосохранение отчета"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}.txt"
        
        if self.logic.export_report(filename, 'txt'):
            self.log_viewer.log(f"Автосохранен отчет: {filename}", "info")
    
    def _clear_log(self):
        """Очистка лога"""
        self.log_viewer.clear()
        self.log_viewer.log("Лог очищен", "info")
    
    def _reset_stats(self):
        """Сброс статистики"""
        self.speed_chart.clear()
        self.stats_panel.reset()
        self.progress_panel.reset()
        self.log_viewer.log("Статистика сброшена", "info")
    
    def _open_settings(self):
        """Открытие настроек"""
        # TODO: Реализовать окно настроек
        self.log_viewer.log("Настройки временно недоступны", "warning")
    
    def _open_documentation(self):
        """Открытие документации"""
        try:
            webbrowser.open("https://github.com/yourusername/sd-card-tester-pro/wiki")
            self.log_viewer.log("Открыта документация", "info")
        except:
            self.log_viewer.log("Не удалось открыть документацию", "warning")
    
    def _check_updates(self):
        """Проверка обновлений"""
        self.log_viewer.log("Проверка обновлений...", "info")
        # TODO: Реализовать проверку обновлений
        self.root.after(2000, lambda: self.log_viewer.log("Обновлений не найдено", "info"))
    
    def _report_bug(self):
        """Сообщить об ошибке"""
        try:
            webbrowser.open("https://github.com/yourusername/sd-card-tester-pro/issues/new")
            self.log_viewer.log("Открыта страница отчетов об ошибках", "info")
        except:
            self.log_viewer.log("Не удалось открыть страницу отчетов об ошибках", "warning")
    
    def _show_error_log(self):
        """Показать журнал ошибок"""
        try:
            ErrorReportDialog(self.root, self.logger)
        except Exception as e:
            self.logger.log_exception(e, module="main")
            messagebox.showerror("Ошибка", f"Не удалось открыть журнал ошибок:\n{str(e)}")
    
    def _show_about(self):
        """Показать информацию о программе"""
        about_text = f"""
SD Card Tester Pro v{self.logic.config["app"]["version"]}

Профессиональный инструмент для тестирования 
карт памяти и других накопителей.

Автор: SD Card Tester Team
Лицензия: MIT

ОС: {platform.system()} {platform.release()}
Python: {platform.python_version()}

© 2024 Все права защищены.
"""
        messagebox.showinfo(
            locales.get_translation(self.current_language, "about", "О программе"),
            about_text
        )
    
    # ========== УПРАВЛЕНИЕ ПРИЛОЖЕНИЕМ ==========
    
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
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.root.mainloop()
    
    def _on_closing(self):
        """Обработка закрытия приложения"""
        if self.logic.test_running:
            if messagebox.askyesno(
                locales.get_translation(self.current_language, "confirm_title", "Подтверждение"),
                "Тестирование выполняется. Вы уверены, что хотите выйти?\nТекущий прогресс будет потерян."
            ):
                self.logic.cancel_requested = True
                time.sleep(0.5)
                self.root.quit()
        else:
            self.root.quit()


def main():
    """Точка входа в программу"""
    try:
        app = SDCardTesterApp()
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