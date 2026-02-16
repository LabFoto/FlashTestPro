"""
Управление темами оформления
Модуль отвечает за переключение между светлой и темной темами интерфейса,
а также за применение цветовых схем к элементам tkinter/ttk
"""

import tkinter as tk
from tkinter import ttk

class ThemeManager:
    """
    Менеджер тем оформления - основной класс для управления цветовыми схемами.
    Позволяет переключаться между темами и применять их к элементам интерфейса.
    """

    # ==================== ТЕМНАЯ ТЕМА ====================
    # Цветовая схема для темного режима (рекомендуется для работы в условиях низкой освещенности)
    DARK_THEME = {
        # Основные цвета интерфейса
        "bg": "#1c1c1c",           # Фоновый цвет окон и панелей (темно-серый)
        "fg": "#ffffff",            # Цвет текста по умолчанию (белый)

        # Цвета выделения
        "select_bg": "#228b22",     # Фон выделенного текста (Лесной зелёный)
        "select_fg": "#ffffff",      # Цвет выделенного текста (белый)

        # Акцентные цвета
        "accent": "#007acc",         # Акцентный цвет для кнопок, вкладок (ярко-синий)

        # Элементы управления
        "button_bg": "#2d2d2d",      # Фон кнопок (темно-серый)
        "button_fg": "#ffffff",      # Текст на кнопках (белый)
        "entry_bg": "#3c3c3c",       # Фон полей ввода (серый)
        "entry_fg": "#ffffff",       # Текст в полях ввода (белый)
        "tree_bg": "#252526",        # Фон древовидных списков (темно-серый)
        "tree_fg": "#ffffff",        # Текст в древовидных списках (белый)

        # Служебные цвета
        "disabled_fg": "#6d6d6d",    # Цвет для неактивных элементов (серый)
        "highlight": "#007acc",      # Цвет подсветки при наведении (синий)

        # Цвета статусов
        "error": "#f48771",          # Цвет ошибок (светло-коралловый)
        "warning": "#cca700",         # Цвет предупреждений (желтый)
        "success": "#6a9955"          # Цвет успешных операций (зеленый)
    }

    # ==================== СВЕТЛАЯ ТЕМА ====================
    # Цветовая схема для светлого режима (классический вид)
    LIGHT_THEME = {
        # Основные цвета интерфейса
        "bg": "#f3f3f3",            # Фоновый цвет окон и панелей (светло-серый)
        "fg": "#000000",             # Цвет текста по умолчанию (черный)

        # Цвета выделения
        "select_bg": "#228b22",      # Фон выделенного текста (Лесной зелёный)
        "select_fg": "#ffffff",       # Цвет выделенного текста (белый)

        # Акцентные цвета
        "accent": "#005a9e",          # Акцентный цвет для кнопок, вкладок (темно-синий)

        # Элементы управления
        "button_bg": "#e1e1e1",       # Фон кнопок (светло-серый)
        "button_fg": "#000000",       # Текст на кнопках (черный)
        "entry_bg": "#ffffff",        # Фон полей ввода (белый)
        "entry_fg": "#000000",        # Текст в полях ввода (черный)
        "tree_bg": "#ffffff",         # Фон древовидных списков (белый)
        "tree_fg": "#000000",         # Текст в древовидных списках (черный)

        # Служебные цвета
        "disabled_fg": "#a2a2a2",     # Цвет для неактивных элементов (серый)
        "highlight": "#005a9e",       # Цвет подсветки при наведении (синий)

        # Цвета статусов
        "error": "#d13438",           # Цвет ошибок (красный)
        "warning": "#ff8c00",         # Цвет предупреждений (оранжевый)
        "success": "#107c10"          # Цвет успешных операций (зеленый)
    }

    def __init__(self, theme_name="dark"):
        """
        Инициализация менеджера тем
        :param theme_name: название темы ("dark" или "light")
        """
        self.current_theme = theme_name  # Текущая активная тема
        # Загружаем цвета соответствующей темы
        self.colors = self.DARK_THEME if theme_name == "dark" else self.LIGHT_THEME

    def set_theme(self, theme_name):
        """
        Переключение между темами
        :param theme_name: название темы для активации
        """
        self.current_theme = theme_name
        # Обновляем словарь цветов при смене темы
        self.colors = self.DARK_THEME if theme_name == "dark" else self.LIGHT_THEME

    def apply_to_root(self, root):
        """
        Применение цветовой темы ко всем элементам интерфейса
        :param root: корневое окно tkinter
        """
        # Устанавливаем фон для главного окна
        root.configure(bg=self.colors["bg"])

        # ========== НАСТРОЙКА СТИЛЕЙ TTK ==========
        # Создаем и настраиваем стили для современных виджетов ttk
        style = ttk.Style()
        style.theme_use("clam")  # Используем тему "clam" как базовую для кастомизации

        # ----- Общие настройки для всех виджетов -----
        style.configure(".",
                        background=self.colors["bg"],        # Фон по умолчанию
                        foreground=self.colors["fg"],        # Текст по умолчанию
                        fieldbackground=self.colors["entry_bg"])  # Фон полей ввода

        # ----- Настройка контейнеров -----
        # Фреймы - используются для группировки элементов
        style.configure("TFrame", background=self.colors["bg"])

        # Фреймы с рамкой и заголовком
        style.configure("TLabelframe",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"])
        style.configure("TLabelframe.Label",
                        background=self.colors["bg"],
                        foreground=self.colors["accent"])  # Заголовок акцентным цветом

        # ----- Настройка кнопок -----
        style.configure("TButton",
                        background=self.colors["button_bg"],   # Обычное состояние
                        foreground=self.colors["button_fg"],
                        borderwidth=1,                          # Толщина границы
                        focuscolor="none")                      # Убираем фокусную обводку
        # Состояния кнопки (при наведении, нажатии и т.д.)
        style.map("TButton",
                  background=[("active", self.colors["accent"])],  # При наведении
                  foreground=[("active", "#ffffff")])              # Текст при наведении

        # ----- Настройка полей ввода -----
        style.configure("TEntry",
                        fieldbackground=self.colors["entry_bg"],  # Фон поля
                        foreground=self.colors["entry_fg"])       # Текст в поле

        # ----- Настройка переключателей -----
        # Флажки (чекбоксы)
        style.configure("TCheckbutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"])
        # Радиокнопки
        style.configure("TRadiobutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"])

        # ----- Настройка выпадающих списков -----
        style.configure("TCombobox",
                        fieldbackground=self.colors["entry_bg"],  # Фон поля
                        foreground=self.colors["entry_fg"])       # Текст
        # Состояния комбобокса
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.colors["entry_bg"])])

        # ----- Настройка полос прокрутки -----
        style.configure("TScrollbar",
                        background=self.colors["button_bg"],      # Цвет бегунка
                        troughcolor=self.colors["bg"],            # Цвет дорожки
                        bordercolor=self.colors["bg"])            # Цвет границы

        # ----- Настройка вкладок (ноутбук) -----
        style.configure("TNotebook",
                        background=self.colors["bg"],
                        tabmargins=[2, 5, 2, 0])                  # Отступы для вкладок
        style.configure("TNotebook.Tab",
                        background=self.colors["button_bg"],       # Обычная вкладка
                        foreground=self.colors["fg"],
                        padding=[10, 2])                           # Внутренние отступы
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["accent"])],  # Активная вкладка
                  foreground=[("selected", "#ffffff")])

        # ----- Настройка индикатора прогресса -----
        style.configure("Horizontal.TProgressbar",
                        background=self.colors["accent"],          # Цвет заполнения
                        troughcolor=self.colors["button_bg"])      # Цвет фона

        # ----- Настройка разделителей -----
        style.configure("TSeparator",
                        background=self.colors["disabled_fg"])     # Цвет линии

    def get_color(self, color_name):
        """
        Получение значения цвета по его имени
        :param color_name: ключ цвета из словаря темы
        :return: HEX-код цвета или цвет текста по умолчанию
        """
        # Если запрошенный цвет не найден, возвращаем цвет текста
        return self.colors.get(color_name, self.colors["fg"])
