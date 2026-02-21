"""
Вкладка форматирования дисков
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class FormatTab(ttk.Frame):
    """Вкладка форматирования"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None

        self.create_widgets()

        # Запуск обработки сообщений
        self.after(100, self.process_messages)

    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Настройки форматирования
        self.settings_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("format_settings", "Настройки форматирования")
        )
        self.settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Файловая система
        fs_frame = ttk.Frame(self.settings_frame)
        fs_frame.pack(fill=tk.X, padx=10, pady=10)

        self.fs_label = ttk.Label(fs_frame, text=self.app.i18n.get("filesystem_label", "Файловая система:"))
        self.fs_label.pack(side=tk.LEFT)

        self.fs_var = tk.StringVar(value="FAT32")
        self.fs_combo = ttk.Combobox(
            fs_frame,
            textvariable=self.fs_var,
            values=["FAT32", "exFAT", "NTFS", "EXT4"],
            state="readonly",
            width=15
        )
        self.fs_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Метка тома
        label_frame = ttk.Frame(self.settings_frame)
        label_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.volume_label = ttk.Label(label_frame, text=self.app.i18n.get("volume_label", "Метка тома:"))
        self.volume_label.pack(side=tk.LEFT)

        self.label_var = tk.StringVar()
        label_entry = ttk.Entry(label_frame, textvariable=self.label_var, width=20)
        label_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Быстрое форматирование
        self.quick_var = tk.BooleanVar(value=True)
        self.quick_cb = ttk.Checkbutton(
            self.settings_frame,
            text=self.app.i18n.get("quick_format", "Быстрое форматирование"),
            variable=self.quick_var
        )
        self.quick_cb.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Кнопка форматирования
        button_frame = ttk.Frame(self.settings_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.format_btn = ttk.Button(
            button_frame,
            text=self.app.i18n.get("format_drive", "💾 Форматировать диск"),
            command=self.format_disk,
            width=25
        )
        self.format_btn.pack()

        # Прогресс форматирования
        self.progress_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("progress", "Прогресс"))
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(pady=(0, 10))

        # Информация
        self.info_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("info", "Информация"))
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.info_text = tk.Text(self.info_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._update_info()

    def on_drive_selected(self, drive_info):
        """Обработка выбора диска"""
        self.current_drive = drive_info

        if drive_info and drive_info.get('is_system', False):
            self.format_btn.config(state=tk.DISABLED)
        elif drive_info:
            self.format_btn.config(state=tk.NORMAL)
        else:
            self.format_btn.config(state=tk.DISABLED)

        self._update_info()

    def _update_info(self):
        """Обновление информационного текста"""
        colors = self.app.theme_manager.colors

        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)

        # Применение цветов темы
        self.info_text.config(
            bg=colors["entry_bg"],
            fg=colors["entry_fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"]
        )

        if self.current_drive:
            info = f"""
    {self.app.i18n.get('drive', 'Диск')}: {self.current_drive['path']}
    {self.app.i18n.get('type', 'Тип')}: {self.current_drive['type']}
    {self.app.i18n.get('filesystem', 'ФС')}: {self.current_drive['fs']}
    {self.app.i18n.get('size', 'Размер')}: {self.current_drive['total_size']}
    {self.app.i18n.get('used', 'Использовано')}: {self.current_drive['used']} ({self.current_drive['percent_used']}%)
    {self.app.i18n.get('free', 'Свободно')}: {self.current_drive['free']}
    {self.app.i18n.get('label', 'Метка')}: {self.current_drive['label'] or self.app.i18n.get('no_label', 'Нет')}
            """
            self.info_text.insert(tk.END, info)

        self.info_text.config(state=tk.DISABLED)

    def format_disk(self):
        """Форматирование диска"""
        if not self.current_drive:
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_drive_first", "Сначала выберите диск")
            )
            return

        if self.current_drive.get('is_system', False):
            messagebox.showerror(
                self.app.i18n.get("error", "Ошибка"),
                self.app.i18n.get("cannot_format_system", "Нельзя форматировать системный диск!")
            )
            return

        # Подтверждение
        if not messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            self.app.i18n.get("confirm_format",
                             f"Все данные на диске {self.current_drive['path']} будут удалены!\n\nПродолжить?")
        ):
            return

        # Сброс прогресса
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")

        # Очистка лога
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)

        # Запуск форматирования
        self.format_btn.config(state=tk.DISABLED)

        success, message = self.app.disk_formatter.format_disk(
            self.current_drive['path'],
            self.fs_var.get(),
            self.quick_var.get(),
            self.label_var.get()
        )

        if not success:
            error_msg = self.app.i18n.get("log_error_prefix", "Ошибка запуска: {}").format(message)
            self._log(error_msg, "error")
            self.format_btn.config(state=tk.NORMAL)

    def process_messages(self):
        """Обработка сообщений от потока форматирования"""
        if hasattr(self.app, 'disk_formatter'):
            msg = self.app.disk_formatter.get_message()

            while msg:
                msg_type = msg[0]

                if msg_type == "log" and len(msg) >= 3:
                    self._log(msg[1], msg[2])

                elif msg_type == "progress" and len(msg) >= 2:
                    self.progress_bar['value'] = msg[1]
                    self.progress_label.config(text=f"{msg[1]:.1f}%")

                elif msg_type == "complete" and len(msg) >= 2:
                    self._log(msg[1], "success")
                    self.format_btn.config(state=tk.NORMAL)
                    messagebox.showinfo(
                        self.app.i18n.get("success", "Успех"),
                        msg[1]
                    )
                    self.app.refresh_drives()

                elif msg_type == "error" and len(msg) >= 2:
                    error_msg = self.app.i18n.get("log_error", "Ошибка: {}").format(msg[1])
                    self._log(error_msg, "error")
                    self.format_btn.config(state=tk.NORMAL)
                    messagebox.showerror(
                        self.app.i18n.get("error", "Ошибка"),
                        msg[1]
                    )

                msg = self.app.disk_formatter.get_message()

        self.after(100, self.process_messages)

    def _log(self, message, level="info"):
        """Добавление сообщения в лог"""
        self.info_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")

        # Цвет в зависимости от уровня
        colors = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        self.info_text.tag_add(level, "end-2l", "end-1l")
        self.info_text.tag_config(level, foreground=colors.get(level, "black"))

        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

    def update_language(self):
        """Обновление языка интерфейса"""
        self.settings_frame.config(text=self.app.i18n.get("format_settings", "Настройки форматирования"))
        self.progress_frame.config(text=self.app.i18n.get("progress", "Прогресс"))
        self.info_frame.config(text=self.app.i18n.get("info", "Информация"))

        self.fs_label.config(text=self.app.i18n.get("filesystem_label", "Файловая система:"))
        self.volume_label.config(text=self.app.i18n.get("volume_label", "Метка тома:"))
        self.quick_cb.config(text=self.app.i18n.get("quick_format", "Быстрое форматирование"))
        self.format_btn.config(text=self.app.i18n.get("format_drive", "💾 Форматировать диск"))

        self._update_info()  # обновить текст с информацией о диске

        def update_theme(self):
            """Обновление темы оформления"""
            self.chart_widget.update_theme()
            self.progress_panel.update_theme()
            self.log_viewer.update_theme()