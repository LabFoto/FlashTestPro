# ui/tabs/info_tab.py

import tkinter as tk
from tkinter import ttk
import platform
import psutil
import socket
import subprocess
import re

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
        self.drive_info_labels = {}       # значения для выбранного диска
        self.drive_left_labels = {}       # левые метки для диска

        self.create_widgets()
        self.update_info()

    def _get_cpu_info(self):
        """
        Возвращает строку с информацией о процессоре в формате:
        "12th Gen Intel(R) Core(TM) i5-12400 (2.50 GHz)"
        """
        system = platform.system()
        cpu_model = "Неизвестно"
        cpu_freq_ghz = None

        # Получаем частоту (в MHz) через psutil (работает везде)
        try:
            freq = psutil.cpu_freq()
            if freq and freq.max:
                cpu_freq_ghz = freq.max / 1000.0  # переводим в GHz
        except:
            pass

        if system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                # Берём первый процессор (обычно достаточно)
                for processor in c.Win32_Processor():
                    cpu_model = processor.Name.strip()
                    # Частота из WMI (MaxClockSpeed) может быть точнее
                    if hasattr(processor, 'MaxClockSpeed') and processor.MaxClockSpeed:
                        cpu_freq_ghz = processor.MaxClockSpeed / 1000.0
                    break
            except Exception as e:
                self.app.logger.debug(f"Ошибка получения CPU через WMI: {e}")
                # Fallback на старый метод
                cpu_model = platform.processor()

        elif system == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_model = line.split(':', 1)[1].strip()
                            break
                # Частота из /proc/cpuinfo (cpu MHz) — если psutil не сработал
                if not cpu_freq_ghz:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'cpu MHz' in line:
                                mhz = float(line.split(':', 1)[1].strip())
                                cpu_freq_ghz = mhz / 1000.0
                                break
            except Exception as e:
                self.app.logger.debug(f"Ошибка чтения /proc/cpuinfo: {e}")
                cpu_model = platform.processor()

        elif system == "Darwin":  # macOS
            try:
                # Получаем модель через sysctl
                result = subprocess.run(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cpu_model = result.stdout.strip()
                else:
                    cpu_model = platform.processor()
            except:
                cpu_model = platform.processor()

        else:
            cpu_model = platform.processor()

        # Формируем итоговую строку
        if cpu_freq_ghz and cpu_freq_ghz > 0:
            # Округляем до 2 знаков, заменяем точку на запятую? Нет, оставляем точку.
            freq_str = f"({cpu_freq_ghz:.2f} GHz)"
        else:
            freq_str = ""

        # Убираем лишние пробелы
        cpu_model = ' '.join(cpu_model.split())
        return f"{cpu_model} {freq_str}".strip()

    def create_widgets(self):
        """Создание виджетов (без изменений, как в предыдущем ответе)"""
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

            left_label = ttk.Label(
                row_frame,
                text=self.app.i18n.get(label_key, label_key),
                font=("Segoe UI", 10, "bold"),
                width=15
            )
            left_label.pack(side=tk.LEFT)
            self.program_label_widgets[key] = left_label

            value_label = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            value_label.pack(side=tk.LEFT, padx=(10, 0))
            self.program_labels[key] = value_label

        # ===== Информация о выбранном диске =====
        self.drive_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("selected_drive_info", "Информация о выбранном диске")
        )
        self.drive_frame.pack(fill=tk.X, pady=(0, 10))

        drive_info_fields = [
            ("path", "drive"),
            ("type", "type"),
            ("fs", "filesystem"),
            ("total_size", "size"),
            ("used", "used"),
            ("free", "free"),
            ("label", "label"),
        ]

        for key, label_key in drive_info_fields:
            row = ttk.Frame(self.drive_frame)
            row.pack(fill=tk.X, padx=10, pady=2)

            left = ttk.Label(
                row,
                text=self.app.i18n.get(label_key, label_key) + ":",
                font=("Segoe UI", 9, "bold")
            )
            left.pack(side=tk.LEFT)
            self.drive_left_labels[key] = left

            value = ttk.Label(row, text="---", font=("Segoe UI", 9))
            value.pack(side=tk.LEFT, padx=(5, 0))
            self.drive_info_labels[key] = value

        # ===== Информация о системе =====
        self.system_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("system_info", "Информация о системе")
        )
        self.system_frame.pack(fill=tk.X, pady=(0, 10))

        sys_info = [
            ("hostname", "hostname_label"),
            ("admin", "admin_label"),
            ("processor", "processor_label"),
            ("os", "os_label"),
            ("arch", "arch_label"),
            ("memory", "memory_label"),
            ("disks", "disks_label"),
        ]

        for key, label_key in sys_info:
            row_frame = ttk.Frame(self.system_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)

            left_label = ttk.Label(
                row_frame,
                text=self.app.i18n.get(label_key, label_key),
                font=("Segoe UI", 10, "bold"),
                width=20
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
        """Обновление системной информации"""
        i = self.app.i18n

        # Информация о программе 
        self.program_labels["name"].config(text=self.app.config.get("app", {}).get("name", "FlashTest Pro"))
        self.program_labels["version"].config(text=self.app.config.get("app", {}).get("version", "1.0.0"))
        self.program_labels["author"].config(text=i.get("author_value", "DeepSeek"))
        self.program_labels["license"].config(text=i.get("license_value", "MIT"))

        # Информация о системе
        # 1. Имя устройства
        hostname = platform.node() or socket.gethostname()
        self.system_labels["hostname"].config(text=hostname)

        # 2. Администратор
        is_admin = self.app.drive_manager.is_admin()
        admin_text = i.get("yes", "Да") if is_admin else i.get("no", "Нет")
        self.system_labels["admin"].config(text=admin_text)

        # 3. Процессор (используем новый метод)
        cpu_info = self._get_cpu_info()
        self.system_labels["processor"].config(text=cpu_info)

        # 4. Операционная система
        os_str = f"{platform.system()} {platform.release()}"
        self.system_labels["os"].config(text=os_str)

        # 5. Архитектура
        arch = platform.architecture()[0]
        self.system_labels["arch"].config(text=arch)

        # 6. Память (использовано/свободно в GB)
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024**3)
        free_gb = mem.free / (1024**3)
        mem_text = f"{used_gb:.1f} GB / {free_gb:.1f} GB"
        self.system_labels["memory"].config(text=mem_text)

        # 7. Количество дисков
        disks_count = len(psutil.disk_partitions())
        self.system_labels["disks"].config(text=str(disks_count))

    def on_drive_selected(self, drive_info):
        """Обновление информации о выбранном диске"""
        if drive_info:
            self.drive_info_labels["path"].config(text=drive_info.get("path", "---"))

            # Перевод типа диска
            type_key = drive_info.get("type", "")
            if type_key:
                type_text = self.app.i18n.get(f"drive_type_{type_key}", type_key)
            else:
                type_text = "---"
            self.drive_info_labels["type"].config(text=type_text)

            self.drive_info_labels["fs"].config(text=drive_info.get("fs", "---"))
            self.drive_info_labels["total_size"].config(text=drive_info.get("total_size", "---"))
            self.drive_info_labels["used"].config(text=drive_info.get("used", "---"))
            self.drive_info_labels["free"].config(text=drive_info.get("free", "---"))
            label = drive_info.get("label", "")
            self.drive_info_labels["label"].config(text=label if label else self.app.i18n.get("no_label", "Нет"))
        else:
            for lbl in self.drive_info_labels.values():
                lbl.config(text="---")

    def update_language(self):
        """Обновление языка интерфейса (без изменений)"""
        i = self.app.i18n

        # Заголовки фреймов
        self.program_frame.config(text=i.get("program_info", "Информация о программе"))
        self.drive_frame.config(text=i.get("selected_drive_info", "Информация о выбранном диске"))
        self.system_frame.config(text=i.get("system_info", "Информация о системе"))

        # Левая метка программы
        for key, widget in self.program_label_widgets.items():
            loc_key = {
                "name": "name_label",
                "version": "version_label",
                "author": "author_label",
                "license": "license_label"
            }.get(key, key)
            widget.config(text=i.get(loc_key, loc_key))

        # Левая метка диска
        drive_fields = [
            ("path", "drive"),
            ("type", "type"),
            ("fs", "filesystem"),
            ("total_size", "size"),
            ("used", "used"),
            ("free", "free"),
            ("label", "label"),
        ]
        for key, loc_key in drive_fields:
            if key in self.drive_left_labels:
                self.drive_left_labels[key].config(text=i.get(loc_key, loc_key) + ":")

        # Левая метка системы
        sys_fields = [
            ("hostname", "hostname_label"),
            ("admin", "admin_label"),
            ("processor", "processor_label"),
            ("os", "os_label"),
            ("arch", "arch_label"),
            ("memory", "memory_label"),
            ("disks", "disks_label"),
        ]
        for key, loc_key in sys_fields:
            if key in self.system_label_widgets:
                self.system_label_widgets[key].config(text=i.get(loc_key, loc_key))

        # Кнопка обновления
        self.refresh_btn.config(text=i.get("refresh", "🔄 Обновить"))

        # Копирайт
        copyright_text = i.get("copyright", "© 2024 FlashTest Pro Team. {}").format(
            i.get("all_rights_reserved", "Все права защищены.")
        )
        self.copyright_label.config(text=copyright_text)

        # Обновить значения (чтобы применить возможные изменения формата)
        self.update_info()

    def update_theme(self):
        """Обновление темы оформления (без изменений)"""
        colors = self.app.theme_manager.colors
        self.copyright_label.config(foreground=colors.get("disabled_fg", "#888888"))
        # Остальные элементы обновляются автоматически через стили