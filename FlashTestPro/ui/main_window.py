"""
Главное окно приложения с вкладками
"""
import tkinter as tk
from tkinter import ttk, messagebox
import platform
import os

from ui.tabs.test_tab import TestTab
from ui.tabs.format_tab import FormatTab
from ui.tabs.wipe_tab import WipeTab
from ui.tabs.results_tab import ResultsTab
from ui.tabs.info_tab import InfoTab
from ui.tabs.capacity_tab import CapacityTab
from ui.widgets.drive_list import DriveListWidget
from utils.logger import get_logger


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, app):
        """
        Инициализация главного окна
        :param app: ссылка на главный объект приложения
        """
        self.app = app
        self.logger = get_logger(__name__)
        self.root = app.root

        # Текущий выбранный диск
        self.selected_drive = None

        # Создание всех элементов интерфейса
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()

        self.logger.info("Главное окно создано")

    def _create_menu(self):
        """Создание главного меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ----- Меню "Файл" -----
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.app.i18n.get("menu_file", "Файл"), menu=file_menu)

        file_menu.add_command(
            label=self.app.i18n.get("menu_refresh", "Обновить диски"),
            command=self.app.refresh_drives,
            accelerator="F5"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=self.app.i18n.get("menu_settings", "Настройки"),
            command=self._open_settings
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=self.app.i18n.get("menu_exit", "Выход"),
            command=self.app.on_closing,
            accelerator="Alt+F4"
        )

        # ----- Меню "Вид" -----
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.app.i18n.get("menu_view", "Вид"), menu=view_menu)

        # Подменю выбора темы оформления
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=self.app.i18n.get("menu_theme", "Тема"), menu=theme_menu)
        theme_menu.add_radiobutton(
            label="Темная",
            command=lambda: self.app.change_theme("dark")
        )
        theme_menu.add_radiobutton(
            label="Светлая",
            command=lambda: self.app.change_theme("light")
        )

        # Подменю выбора языка интерфейса
        lang_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label=self.app.i18n.get("menu_language", "Язык"), menu=lang_menu)
        lang_menu.add_radiobutton(
            label="Русский",
            command=lambda: self.app.change_language("ru")
        )
        lang_menu.add_radiobutton(
            label="English",
            command=lambda: self.app.change_language("en")
        )
        lang_menu.add_radiobutton(
            label="中文",
            command=lambda: self.app.change_language("zh")
        )

        # ----- Новый пункт: "Отображать всё" -----
        self.show_all_var = tk.BooleanVar(
            value=self.app.config['ui'].get('show_all_devices', False)
        )
        view_menu.add_checkbutton(
            label=self.app.i18n.get("menu_show_all", "Отображать всё"),
            variable=self.show_all_var,
            command=self._toggle_show_all
        )

        # ----- Меню "Инструменты" -----
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.app.i18n.get("menu_tools", "Инструменты"), menu=tools_menu)

        tools_menu.add_command(
            label=self.app.i18n.get("menu_check_health", "Проверка здоровья"),
            command=self._check_disk_health
        )
        tools_menu.add_command(
            label=self.app.i18n.get("menu_benchmark", "Бенчмарк"),
            command=self._run_benchmark
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label=self.app.i18n.get("menu_error_log", "Журнал ошибок"),
            command=self._show_error_log
        )

        # ----- Меню "Справка" -----
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.app.i18n.get("menu_help", "Справка"), menu=help_menu)

        help_menu.add_command(
            label=self.app.i18n.get("menu_documentation", "Документация"),
            command=self._open_documentation
        )
        help_menu.add_separator()
        help_menu.add_command(
            label=self.app.i18n.get("menu_about", "О программе"),
            command=self._show_about
        )

        # Привязка горячих клавиш
        self.root.bind("<F5>", lambda e: self.app.refresh_drives())

    def _toggle_show_all(self):
        """Обработчик переключения галочки"""
        self.app.toggle_show_all_devices()
        # Синхронизируем переменную с конфигом (на случай, если вызов пришёл откуда-то ещё)
        self.show_all_var.set(self.app.config['ui'].get('show_all_devices', False))

    def _create_main_layout(self):
        """Создание основной структуры окна"""
        # Главный контейнер с отступами от краев окна
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== ЛЕВАЯ ПАНЕЛЬ (СПИСОК ДИСКОВ) =====
        left_panel = ttk.Frame(main_container, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Заголовок панели дисков
        self.drives_label = ttk.Label(
            left_panel,
            text=self.app.i18n.get("available_drives", "Доступные диски"),
            style="Heading.TLabel"
        )
        self.drives_label.pack(anchor=tk.W, pady=(0, 5))

        # Виджет списка дисков
        self.drive_list = DriveListWidget(left_panel, self.app)
        self.drive_list.pack(fill=tk.BOTH, expand=True)

        # Кнопка обновления списка дисков
        self.refresh_btn = ttk.Button(
            left_panel,
            text=self.app.i18n.get("refresh", "🔄 Обновить"),
            command=self.app.refresh_drives
        )
        self.refresh_btn.pack(fill=tk.X, pady=(10, 0))

        # ===== ПРАВАЯ ПАНЕЛЬ (СИСТЕМА ВКЛАДОК) =====
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Создание виджета вкладок
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Инициализация всех вкладок
        self.test_tab = TestTab(self.notebook, self.app)
        self.notebook.add(self.test_tab, text=self.app.i18n.get("tab_test", "🔍 Тестирование"))

        self.capacity_tab = CapacityTab(self.notebook, self.app)
        self.notebook.add(self.capacity_tab, text=self.app.i18n.get("tab_capacity", "📏 Ёмкость"))

        self.format_tab = FormatTab(self.notebook, self.app)
        self.notebook.add(self.format_tab, text=self.app.i18n.get("tab_format", "💾 Форматирование"))

        self.wipe_tab = WipeTab(self.notebook, self.app)
        self.notebook.add(self.wipe_tab, text=self.app.i18n.get("tab_wipe", "🧹 Затирание"))

        self.results_tab = ResultsTab(self.notebook, self.app)
        self.notebook.add(self.results_tab, text=self.app.i18n.get("tab_results", "📊 Результаты"))

        self.info_tab = InfoTab(self.notebook, self.app)
        self.notebook.add(self.info_tab, text=self.app.i18n.get("tab_info", "ℹ️ Информация"))


    def _create_status_bar(self):
        """Создание строки состояния внизу окна"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Левая часть - текущий статус
        self.status_label = ttk.Label(
            self.status_bar,
            text=self.app.i18n.get("ready", "Готов"),
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Правая часть - информация о выбранном диске
        self.drive_info_label = ttk.Label(
            self.status_bar,
            text="",
            relief=tk.SUNKEN,
            anchor=tk.E,
            width=40
        )
        self.drive_info_label.pack(side=tk.RIGHT)

    def update_drive_list(self, drives):
        """Обновление списка дисков"""
        self.drive_list.update_drives(drives)
        self.update_status(f"Найдено дисков: {len(drives)}")

    def update_selected_drive(self, drive_info):
        """Обновление информации при выборе диска"""
        self.selected_drive = drive_info

        if drive_info:
            if drive_info.get('is_system', False):
                info_text = f"⚠️ СИСТЕМНЫЙ ДИСК: {drive_info['path']}"
                self.drive_info_label.config(foreground="red")
            else:
                info_text = f"{drive_info['path']} | {drive_info['total_size']} | {drive_info['fs']}"
                self.drive_info_label.config(foreground="")

            self.drive_info_label.config(text=info_text)

            # Уведомляем все вкладки о выборе диска
            self.test_tab.on_drive_selected(drive_info)
            self.capacity_tab.on_drive_selected(drive_info)
            self.format_tab.on_drive_selected(drive_info)
            self.wipe_tab.on_drive_selected(drive_info)
            self.results_tab.on_drive_selected(drive_info)
            self.info_tab.on_drive_selected(drive_info)

    def get_selected_drive(self):
        """Получение информации о текущем выбранном диске"""
        return self.selected_drive

    def update_status(self, message, message_type="info"):
        """Обновление текста в строке состояния"""
        self.status_label.config(text=message)

        colors = {
            "info": "",
            "warning": "orange",
            "error": "red",
            "success": "green"
        }
        self.status_label.config(foreground=colors.get(message_type, ""))

    def show_admin_warning(self):
        """Показывает предупреждение о необходимости прав администратора"""
        warning_text = self.app.i18n.get(
            "admin_warning",
            "⚠️ Для полного доступа к дискам рекомендуется запустить программу от имени администратора/root"
        )
        self.update_status(warning_text, "warning")

    def update_ui_language(self):
        """Обновление языка интерфейса при смене локализации"""
        # Обновление заголовков вкладок
        self.notebook.tab(0, text=self.app.i18n.get("tab_test", "🔍 Тестирование"))
        self.notebook.tab(1, text=self.app.i18n.get("tab_format", "💾 Форматирование"))
        self.notebook.tab(2, text=self.app.i18n.get("tab_wipe", "🧹 Затирание"))
        self.notebook.tab(3, text=self.app.i18n.get("tab_results", "📊 Результаты"))
        self.notebook.tab(4, text=self.app.i18n.get("tab_info", "ℹ️ Информация"))

        # Обновление содержимого вкладок
        self.test_tab.update_language()
        self.format_tab.update_language()
        self.wipe_tab.update_language()
        self.results_tab.update_language()
        self.info_tab.update_language()

        # Обновление заголовков списка дисков
        self.drive_list.update_language()

        # Обновление меню
        self._create_menu()

        # Обновление заголовка списка дисков
        if hasattr(self, 'drives_label'):
            self.drives_label.config(text=self.app.i18n.get("available_drives", "Доступные диски"))

        # Обновление кнопки обновления
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.config(text=self.app.i18n.get("refresh", "🔄 Обновить"))

    def update_theme(self):
        """Обновление темы оформления"""
        # Применение темы к корневому окну
        self.app.theme_manager.apply_to_root(self.root)

        # Обновление вкладок
        self.test_tab.update_theme()
        self.format_tab.update_theme()
        self.wipe_tab.update_theme()
        self.results_tab.update_theme()
        self.info_tab.update_theme()

        # Обновление списка дисков
        self.drive_list.update_theme()

    def _open_settings(self):
        """Открытие окна настроек"""
        messagebox.showinfo("Информация", "Окно настроек будет доступно в следующей версии")

    def _check_disk_health(self):
        """Проверка здоровья выбранного диска"""
        if not self.selected_drive:
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_drive_first", "Сначала выберите диск")
            )
            return

        messagebox.showinfo("Информация", "Проверка здоровья будет доступна в следующей версии")

    def _run_benchmark(self):
        """Запуск бенчмарка для выбранного диска"""
        if not self.selected_drive:
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_drive_first", "Сначала выберите диск")
            )
            return

        # Переключение на вкладку тестирования и запуск бенчмарка
        self.notebook.select(0)
        self.test_tab.run_benchmark()

    def _show_error_log(self):
        """Отображение журнала ошибок в отдельном окне"""
        from tkinter import scrolledtext

        error_window = tk.Toplevel(self.root)
        error_window.title(self.app.i18n.get("error_log", "Журнал ошибок"))
        error_window.geometry("700x500")
        error_window.minsize(600, 400)

        text_area = scrolledtext.ScrolledText(
            error_window,
            wrap=tk.WORD,
            font=self.app.theme_manager.fixed_font
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_path = os.path.join("logs", "error.log")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                text_area.insert(tk.END, f.read())

        text_area.config(state=tk.DISABLED)

    def _open_documentation(self):
        """Открытие документации в браузере"""
        import webbrowser
        webbrowser.open("https://github.com/yourusername/flashtestpro/wiki")

    def _show_about(self):
        """Показ информации о программе"""
        about_text = f"""
{self.app.i18n.get("app_title", "FlashTest Pro")} v1.0.0

{self.app.i18n.get("about_description", "Профессиональный инструмент для тестирования и обслуживания flash-накопителей")}

© 2024 FlashTest Pro Team
{self.app.i18n.get("license", "Лицензия")}: MIT

{self.app.i18n.get("system_info", "Информация о системе")}:
OS: {platform.system()} {platform.release()}
Python: {platform.python_version()}
"""
        messagebox.showinfo(
            self.app.i18n.get("about", "О программе"),
            about_text
        )