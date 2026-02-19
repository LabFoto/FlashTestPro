"""
Вкладка с информацией о системе и программе
"""
import tkinter as tk
from tkinter import ttk
import platform
import psutil

class InfoTab(ttk.Frame):
    """Вкладка информации"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Словари для хранения виджетов
        self.program_labels = {}          # значения (правая колонка)
        self.program_label_widgets = {}   # левые метки (названия)
        self.system_labels = {}
        self.system_label_widgets = {}

        self.create_widgets()
        self.update_info()

    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== Информация о программе =====
        self.program_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("program_info", "Информация о программе")
        )
        self.program_frame.pack(fill=tk.X, pady=(0, 10))

        prog_info = [
            ("name", "name_label"),
            ("version", "version_label"),
            ("author", "author_label"),
            ("license", "license_label"),
        ]

        for key, label_key in prog_info:
            row_frame = ttk.Frame(self.program_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)

            # Левая метка (локализуемая)
            left_label = ttk.Label(
                row_frame,
                text=self.app.i18n.get(label_key, label_key),
                font=("Segoe UI", 10, "bold"),
                width=15
            )
            left_label.pack(side=tk.LEFT)
            self.program_label_widgets[key] = left_label

            # Правое значение (будет обновляться в update_info)
            value_label = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            value_label.pack(side=tk.LEFT, padx=(10, 0))
            self.program_labels[key] = value_label

        # ===== Информация о системе =====
        self.system_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("system_info", "Информация о системе")
        )
        self.system_frame.pack(fill=tk.X, pady=(0, 10))

        sys_info = [
            ("os", "os_label"),
            ("python", "python_label"),
            ("processor", "processor_label"),
            ("memory", "memory_label"),
            ("disks", "disks_label"),
            ("admin", "admin_label"),
        ]

        for key, label_key in sys_info:
            row_frame = ttk.Frame(self.system_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)

            left_label = ttk.Label(
                row_frame,
                text=self.app.i18n.get(label_key, label_key),
                font=("Segoe UI", 10, "bold"),
                width=15
            )
            left_label.pack(side=tk.LEFT)
            self.system_label_widgets[key] = left_label

            value_label = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            value_label.pack(side=tk.LEFT, padx=(10, 0))
            self.system_labels[key] = value_label

        # ===== Кнопка обновления =====
        self.refresh_btn = ttk.Button(
            main_frame,
            text=self.app.i18n.get("refresh", "🔄 Обновить"),
            command=self.update_info
        )
        self.refresh_btn.pack(pady=10)

        # ===== Копирайт =====
        copyright_frame = ttk.Frame(main_frame)
        copyright_frame.pack(fill=tk.X, pady=(20, 0))

        copyright_text = self.app.i18n.get("copyright", "© 2024 FlashTest Pro Team. {}").format(
            self.app.i18n.get("all_rights_reserved", "Все права защищены.")
        )
        self.copyright_label = ttk.Label(
            copyright_frame,
            text=copyright_text,
            font=("Segoe UI", 8)
        )
        self.copyright_label.pack()

    def update_info(self):
        """Обновление информации (значений)"""
        i = self.app.i18n

        # Информация о программе
        self.program_labels["name"].config(text=self.app.config.get("app", {}).get("name", "FlashTest Pro"))
        self.program_labels["version"].config(text=self.app.config.get("app", {}).get("version", "1.0.0"))
        self.program_labels["author"].config(text=i.get("author_value", "DeepSeek"))
        self.program_labels["license"].config(text=i.get("license_value", "MIT"))

        # Информация о системе
        self.system_labels["os"].config(text=f"{platform.system()} {platform.release()}")
        self.system_labels["python"].config(text=platform.python_version())
        self.system_labels["processor"].config(
            text=platform.processor() or i.get("unknown", "Неизвестно")
        )

        # Память
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3)
        mem_used = mem.used / (1024**3)
        self.system_labels["memory"].config(text=f"{mem_used:.1f} GB / {mem_total:.1f} GB ({mem.percent}%)")

        # Количество дисков
        disks = len(psutil.disk_partitions())
        self.system_labels["disks"].config(text=str(disks))

        # Права администратора
        is_admin = self.app.drive_manager.is_admin()
        admin_text = i.get("yes", "Да") if is_admin else i.get("no", "Нет")
        self.system_labels["admin"].config(text=admin_text)

    def on_drive_selected(self, drive_info):
        """Обработка выбора диска (не используется)"""
        pass

    def update_language(self):
        """Обновление языка интерфейса (левых меток и заголовков)"""
        i = self.app.i18n

        # Заголовки фреймов
        self.program_frame.config(text=i.get("program_info", "Информация о программе"))
        self.system_frame.config(text=i.get("system_info", "Информация о системе"))

        # Левые метки программы
        for key, widget in self.program_label_widgets.items():
            loc_key = {
                "name": "name_label",
                "version": "version_label",
                "author": "author_label",
                "license": "license_label"
            }.get(key, key)
            widget.config(text=i.get(loc_key, loc_key))

        # Левые метки системы
        for key, widget in self.system_label_widgets.items():
            loc_key = {
                "os": "os_label",
                "python": "python_label",
                "processor": "processor_label",
                "memory": "memory_label",
                "disks": "disks_label",
                "admin": "admin_label"
            }.get(key, key)
            widget.config(text=i.get(loc_key, loc_key))

        # Кнопка обновления
        self.refresh_btn.config(text=i.get("refresh", "🔄 Обновить"))

        # Копирайт
        copyright_text = i.get("copyright", "© 2024 FlashTest Pro Team. {}").format(
            i.get("all_rights_reserved", "Все права защищены.")
        )
        self.copyright_label.config(text=copyright_text)

        # Обновляем значения (на случай, если формат чисел или текст зависят от языка)
        self.update_info()

    def update_theme(self):
        """Обновление темы оформления"""
        colors = self.app.theme_manager.colors
        # Обновляем цвет текста для copyright_label, управляется через стили
        self.copyright_label.config(foreground=colors.get("disabled_fg", "#888888"))

        # Остальные элементы (ttk) обновляются автоматически через стили, применённые к root
        # Если в будущем появятся другие элементы с явными цветами, их нужно обновлять здесь