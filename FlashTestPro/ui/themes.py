"""
Управление темами оформления
Модуль отвечает за переключение между светлой и темной темами интерфейса,
а также за применение цветовых схем к элементам tkinter/ttk
"""

import tkinter as tk
from tkinter import ttk
import platform

class ThemeManager:
    """
    Менеджер тем оформления - основной класс для управления цветовыми схемами.
    Позволяет переключаться между темами и применять их к элементам интерфейса.
    """

    # ==================== ТЕМНАЯ ТЕМА ====================
    DARK_THEME = {
        # Основные цвета интерфейса
        "bg": "#1e1e1e",              # Фоновый цвет окон и панелей (темно-серый)
        "fg": "#ffffff",               # Цвет текста по умолчанию (белый)
        "secondary_bg": "#2d2d2d",     # Фон для второстепенных элементов
        "tertiary_bg": "#3c3c3c",      # Фон для полей ввода и списков

        # Цвета выделения
        "select_bg": "#228b22",         # Фон выделенного текста (Лесной зелёный)
        "select_fg": "#ffffff",          # Цвет выделенного текста (белый)

        # Акцентные цвета
        "accent": "#007acc",             # Акцентный цвет для кнопок, вкладок (ярко-синий)

        # Элементы управления
        "button_bg": "#2d2d2d",           # Фон кнопок (темно-серый)
        "button_fg": "#ffffff",           # Текст на кнопках (белый)
        "entry_bg": "#3c3c3c",            # Фон полей ввода (серый)
        "entry_fg": "#ffffff",            # Текст в полях ввода (белый)

        # Специальные цвета для дисков
        "system_disk_fg": "#ff6b6b",      # Красный цвет для системных дисков
        "normal_disk_fg": "#ffffff",      # Белый цвет для обычных дисков
        "removable_disk_fg": "#87CEEB",   # Голубой для съемных дисков
        "tree_select_bg": "#228b22",      # Фон выделенного элемента в списке (зеленый)
        "tree_select_fg": "#ffffff",      # Текст выделенного элемента (белый)

        # Служебные цвета
        "disabled_fg": "#6d6d6d",          # Цвет для неактивных элементов (серый)
        "highlight": "#007acc",            # Цвет подсветки при наведении (синий)
        "border": "#3c3c3c",               # Цвет границ

        # Цвета статусов
        "error": "#f48771",                 # Цвет ошибок (светло-коралловый)
        "warning": "#cca700",                # Цвет предупреждений (желтый)
        "success": "#6a9955",                # Цвет успешных операций (зеленый)
        
        # Цвета для лога
        "log_bg": "#1e1e1e",                 # Фон журнала событий
        "log_fg": "#d4d4d4",                 # Текст журнала
        "log_error": "#f48771",              # Ошибки в логе
        "log_warning": "#cca700",             # Предупреждения в логе
        "log_success": "#6a9955",             # Успех в логе
        "log_info": "#9cdcfe",                # Информация в логе
        "log_system": "#c586c0"               # Системные сообщения в логе
    }

    # ==================== СВЕТЛАЯ ТЕМА ====================
    LIGHT_THEME = {
        # Основные цвета интерфейса
        "bg": "#f3f3f3",                     # Фоновый цвет окон и панелей (светло-серый)
        "fg": "#000000",                      # Цвет текста по умолчанию (черный)
        "secondary_bg": "#e1e1e1",            # Фон для второстепенных элементов
        "tertiary_bg": "#ffffff",             # Фон для полей ввода и списков

        # Цвета выделения
        "select_bg": "#228b22",                # Фон выделенного текста (Лесной зелёный)
        "select_fg": "#ffffff",                 # Цвет выделенного текста (белый)

        # Акцентные цвета
        "accent": "#005a9e",                    # Акцентный цвет для кнопок, вкладок (темно-синий)

        # Элементы управления
        "button_bg": "#e1e1e1",                  # Фон кнопок (светло-серый)
        "button_fg": "#000000",                   # Текст на кнопках (черный)
        "entry_bg": "#ffffff",                     # Фон полей ввода (белый)
        "entry_fg": "#000000",                     # Текст в полях ввода (черный)

        # Специальные цвета для дисков
        "system_disk_fg": "#d13438",               # Красный цвет для системных дисков
        "normal_disk_fg": "#000000",               # Черный цвет для обычных дисков
        "removable_disk_fg": "#005a9e",            # Синий для съемных дисков
        "tree_select_bg": "#228b22",               # Фон выделенного элемента в списке (зеленый)
        "tree_select_fg": "#ffffff",               # Текст выделенного элемента (белый)

        # Служебные цвета
        "disabled_fg": "#a2a2a2",                   # Цвет для неактивных элементов (серый)
        "highlight": "#005a9e",                     # Цвет подсветки при наведении (синий)
        "border": "#a2a2a2",                        # Цвет границ

        # Цвета статусов
        "error": "#d13438",                          # Цвет ошибок (красный)
        "warning": "#ff8c00",                        # Цвет предупреждений (оранжевый)
        "success": "#107c10",                        # Цвет успешных операций (зеленый)
        
        # Цвета для лога
        "log_bg": "#ffffff",                         # Фон журнала событий
        "log_fg": "#000000",                          # Текст журнала
        "log_error": "#d13438",                       # Ошибки в логе
        "log_warning": "#ff8c00",                     # Предупреждения в логе
        "log_success": "#107c10",                     # Успех в логе
        "log_info": "#005a9e",                        # Информация в логе
        "log_system": "#800080"                        # Системные сообщения в логе
    }

    def __init__(self, theme_name="dark"):
        """
        Инициализация менеджера тем
        :param theme_name: название темы ("dark" или "light")
        """
        self.current_theme = theme_name
        self.colors = self.DARK_THEME if theme_name == "dark" else self.LIGHT_THEME
        
        # Определяем системные шрифты для поддержки разных языков
        self._setup_system_fonts()

    def _setup_system_fonts(self):
        """Настройка системных шрифтов для поддержки разных языков"""
        system = platform.system()
        
        # Базовые шрифты для разных ОС
        if system == "Windows":
            # Windows шрифты с поддержкой китайского
            self.default_font_family = "Microsoft YaHei"
            self.fixed_font_family = "Consolas"
        elif system == "Linux":
            # Linux шрифты
            self.default_font_family = "WenQuanYi Zen Hei"
            self.fixed_font_family = "Monospace"
        elif system == "Darwin":  # macOS
            self.default_font_family = "PingFang SC"
            self.fixed_font_family = "Menlo"
        else:
            self.default_font_family = "TkDefaultFont"
            self.fixed_font_family = "TkFixedFont"
        
        # Создаем кортежи шрифтов для разных целей
        self.default_font = (self.default_font_family, 9)
        self.default_font_bold = (self.default_font_family, 9, "bold")
        self.fixed_font = (self.fixed_font_family, 9)
        self.fixed_font_bold = (self.fixed_font_family, 9, "bold")
        self.heading_font = (self.default_font_family, 11, "bold")
        self.menu_font = (self.default_font_family, 9)
        self.small_font = (self.default_font_family, 8)

    def set_theme(self, theme_name):
        """
        Переключение между темами
        :param theme_name: название темы для активации
        """
        self.current_theme = theme_name
        self.colors = self.DARK_THEME if theme_name == "dark" else self.LIGHT_THEME

    def apply_to_root(self, root):
        """
        Применение цветовой темы ко всем элементам интерфейса
        :param root: корневое окно tkinter
        """
        # Устанавливаем фон для главного окна
        root.configure(bg=self.colors["bg"])

        # Настраиваем шрифт по умолчанию для всех виджетов
        root.option_add("*Font", self.default_font)
        root.option_add("*Menu.font", self.menu_font)
        root.option_add("*TButton.font", self.default_font)
        root.option_add("*TLabel.font", self.default_font)
        root.option_add("*TEntry.font", self.default_font)
        root.option_add("*TCombobox.font", self.default_font)
        root.option_add("*TCheckbutton.font", self.default_font)
        root.option_add("*TRadiobutton.font", self.default_font)
        root.option_add("*TNotebook.Tab.font", self.default_font)
        root.option_add("*Treeview.font", self.default_font)
        root.option_add("*Listbox.font", self.default_font)
        root.option_add("*Text.font", self.fixed_font)

        # ========== НАСТРОЙКА СТИЛЕЙ TTK ==========
        style = ttk.Style()
        style.theme_use("clam")

        # ----- Общие настройки для всех виджетов -----
        style.configure(".",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["entry_bg"],
                        font=self.default_font)

        style.map(".",
                  background=[],
                  foreground=[])

        # ----- Настройка контейнеров -----
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", 
                       background=self.colors["bg"], 
                       foreground=self.colors["fg"],
                       font=self.default_font)
        
        # Фреймы с рамкой и заголовком
        style.configure("TLabelframe",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        bordercolor=self.colors["border"],
                        lightcolor=self.colors["border"],
                        darkcolor=self.colors["border"])
        style.configure("TLabelframe.Label",
                        background=self.colors["bg"],
                        foreground=self.colors["accent"],
                        font=self.default_font_bold)

        # ----- Настройка кнопок -----
        style.configure("TButton",
                        background=self.colors["button_bg"],
                        foreground=self.colors["button_fg"],
                        borderwidth=1,
                        focuscolor="none",
                        relief="raised",
                        font=self.default_font)
        style.map("TButton",
                  background=[("active", self.colors["accent"]),
                             ("pressed", self.colors["accent"])],
                  foreground=[("active", "#ffffff"),
                             ("pressed", "#ffffff")],
                  relief=[("pressed", "sunken")])

        # ----- Настройка полей ввода -----
        style.configure("TEntry",
                        fieldbackground=self.colors["entry_bg"],
                        foreground=self.colors["entry_fg"],
                        insertcolor=self.colors["fg"],
                        bordercolor=self.colors["border"],
                        font=self.default_font)
        
        style.configure("TCombobox",
                        fieldbackground=self.colors["entry_bg"],
                        foreground=self.colors["entry_fg"],
                        selectbackground=self.colors["select_bg"],
                        selectforeground=self.colors["select_fg"],
                        arrowcolor=self.colors["fg"],
                        font=self.default_font)
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.colors["entry_bg"])])

        # ----- Настройка переключателей -----
        style.configure("TCheckbutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        indicatorcolor=self.colors["button_bg"],
                        indicatormargin=5,
                        font=self.default_font)
        style.map("TCheckbutton",
                  indicatorcolor=[("selected", self.colors["accent"]),
                                 ("active", self.colors["highlight"])])

        style.configure("TRadiobutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        indicatorcolor=self.colors["button_bg"],
                        font=self.default_font)
        style.map("TRadiobutton",
                  indicatorcolor=[("selected", self.colors["accent"])])

        # ----- Настройка полос прокрутки -----
        style.configure("TScrollbar",
                        background=self.colors["button_bg"],
                        troughcolor=self.colors["bg"],
                        bordercolor=self.colors["bg"],
                        arrowcolor=self.colors["fg"],
                        gripcount=0)
        style.map("TScrollbar",
                  background=[("active", self.colors["highlight"])])

        # ----- Настройка вкладок -----
        style.configure("TNotebook",
                        background=self.colors["bg"],
                        tabmargins=[2, 5, 2, 0],
                        borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.colors["button_bg"],
                        foreground=self.colors["fg"],
                        padding=[10, 2],
                        borderwidth=1,
                        font=self.default_font)
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["accent"])],
                  foreground=[("selected", "#ffffff")])

        # ----- Настройка индикатора прогресса -----
        style.configure("Horizontal.TProgressbar",
                        background=self.colors["accent"],
                        troughcolor=self.colors["button_bg"],
                        bordercolor=self.colors["border"],
                        lightcolor=self.colors["accent"],
                        darkcolor=self.colors["accent"])

        # ----- Настройка разделителей -----
        style.configure("TSeparator",
                        background=self.colors["disabled_fg"])

        # ----- Дополнительные стили -----
        # Стиль для лога
        style.configure("Log.TFrame", background=self.colors["log_bg"])
        style.configure("Log.TLabel", 
                       background=self.colors["log_bg"], 
                       foreground=self.colors["log_fg"],
                       font=self.fixed_font)
        
        # Стиль для панели прогресса
        style.configure("Progress.TFrame", background=self.colors["secondary_bg"])
        style.configure("Progress.TLabel", 
                       background=self.colors["secondary_bg"], 
                       foreground=self.colors["fg"],
                       font=self.default_font)
        
        # Стиль для информационных панелей
        style.configure("Info.TFrame", background=self.colors["tertiary_bg"])
        style.configure("Info.TLabel", 
                       background=self.colors["tertiary_bg"], 
                       foreground=self.colors["fg"],
                       font=self.default_font)
        
        # Стиль для заголовков
        style.configure("Heading.TLabel", 
                       background=self.colors["bg"], 
                       foreground=self.colors["accent"],
                       font=self.heading_font)
        
        # Стиль для маленького текста
        style.configure("Small.TLabel",
                       background=self.colors["bg"],
                       foreground=self.colors["disabled_fg"],
                       font=self.small_font)

    def get_color(self, color_name):
        """
        Получение значения цвета по его имени
        :param color_name: ключ цвета из словаря темы
        :return: HEX-код цвета или цвет текста по умолчанию
        """
        return self.colors.get(color_name, self.colors["fg"])
    
    def get_treeview_style(self):
        """
        Создание и возврат стиля для Treeview
        Используется в виджете списка дисков
        """
        style = ttk.Style()
        
        # Настраиваем стиль для Treeview
        style.configure(
            "Custom.Treeview",
            background=self.colors["tertiary_bg"],
            foreground=self.colors["fg"],
            fieldbackground=self.colors["tertiary_bg"],
            borderwidth=0,
            relief="flat",
            rowheight=25,
            font=self.default_font
        )
        
        # Настраиваем стиль для выделенных элементов
        style.map(
            "Custom.Treeview",
            background=[("selected", self.colors["tree_select_bg"])],
            foreground=[("selected", self.colors["tree_select_fg"])]
        )
        
        # Настраиваем стиль для заголовков
        style.configure(
            "Custom.Treeview.Heading",
            background=self.colors["button_bg"],
            foreground=self.colors["button_fg"],
            relief="flat",
            borderwidth=1,
            font=self.default_font_bold
        )
        
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", self.colors["accent"])],
            foreground=[("active", "#ffffff")]
        )
        
        return "Custom.Treeview"
    
    def get_font_for_language(self, language):
        """
        Получение подходящего шрифта для конкретного языка
        :param language: код языка ('ru', 'en', 'zh')
        :return: кортеж шрифта (family, size, [style])
        """
        system = platform.system()
        
        if system == "Windows":
            if language == "zh":
                return ("Microsoft YaHei", 9)
            elif language == "ru":
                return ("Segoe UI", 9)
            else:
                return ("Segoe UI", 9)
        elif system == "Linux":
            if language == "zh":
                return ("WenQuanYi Zen Hei", 9)
            else:
                return ("Noto Sans", 9)
        elif system == "Darwin":  # macOS
            if language == "zh":
                return ("PingFang SC", 9)
            else:
                return ("Helvetica", 9)
        else:
            return ("TkDefaultFont", 9)