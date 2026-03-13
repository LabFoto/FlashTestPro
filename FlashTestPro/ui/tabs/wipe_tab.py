"""
Вкладка безопасного затирания данных
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class WipeTab(ttk.Frame):
    """Вкладка затирания данных"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None

        # Соответствие идентификатор -> ключ локализации
        self.method_map = {
            "simple": "method_simple",
            "dod": "method_dod",
            "gutmann": "method_gutmann"
        }
        self.method_ids = list(self.method_map.keys())

        self.create_widgets()

        # Запуск обработки сообщений
        self.after(100, self.process_messages)

    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Настройки затирания
        self.settings_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("wipe_settings", "Настройки затирания")
        )
        self.settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Метод затирания
        method_frame = ttk.Frame(self.settings_frame)
        method_frame.pack(fill=tk.X, padx=10, pady=10)

        self.method_label = ttk.Label(method_frame, text=self.app.i18n.get("wipe_method", "Метод затирания:"))
        self.method_label.pack(side=tk.LEFT)

        self.method_id = tk.StringVar(value="dod")          # храним идентификатор
        self.method_combo = ttk.Combobox(
            method_frame,
            values=self._get_localized_methods(),
            state="readonly",
            width=30
        )
        self.method_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.method_combo.bind("<<ComboboxSelected>>", self._on_method_selected)

        # Установка начального значения
        self._set_method_combo(self.method_id.get())

        # Количество проходов
        passes_frame = ttk.Frame(self.settings_frame)
        passes_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.passes_label = ttk.Label(passes_frame, text=self.app.i18n.get("wipe_passes", "Количество проходов:"))
        self.passes_label.pack(side=tk.LEFT)

        self.passes_var = tk.IntVar(value=3)
        passes_spin = ttk.Spinbox(
            passes_frame,
            from_=1, to=100,
            textvariable=self.passes_var,
            width=10
        )
        passes_spin.pack(side=tk.LEFT, padx=(10, 0))

        # Проверка после затирания
        self.verify_var = tk.BooleanVar(value=True)
        self.verify_cb = ttk.Checkbutton(
            self.settings_frame,
            text=self.app.i18n.get("verify_wipe", "Проверить после затирания"),
            variable=self.verify_var
        )
        self.verify_cb.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Кнопки управления
        buttons_frame = ttk.Frame(self.settings_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("start_wipe", "🧹 Начать затирание"),
            command=self.start_wipe,
            width=25
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("stop", "⏹ Стоп"),
            command=self.stop_wipe,
            state=tk.DISABLED,
            width=15
        )
        self.stop_btn.pack(side=tk.LEFT)

        # Прогресс
        self.progress_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("progress", "Прогресс"))
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(pady=(0, 10))

        # Лог
        self.log_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("log", "Лог"))
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _get_localized_methods(self):
        """Возвращает список локализованных названий методов в порядке self.method_ids"""
        return [self.app.i18n.get(self.method_map[mid], mid) for mid in self.method_ids]

    def _set_method_combo(self, method_id):
        """Устанавливает выбранный элемент комбобокса по идентификатору"""
        if method_id in self.method_ids:
            index = self.method_ids.index(method_id)
            localized = self._get_localized_methods()[index]
            self.method_combo.set(localized)

    def _on_method_selected(self, event):
        """Обработчик выбора метода: обновляет self.method_id"""
        selected = self.method_combo.get()
        # Находим идентификатор по локализованному названию
        for mid, loc_key in self.method_map.items():
            if self.app.i18n.get(loc_key) == selected:
                self.method_id.set(mid)
                break

    def on_drive_selected(self, drive_info):
        """Обработка выбора диска"""
        self.current_drive = drive_info

        if drive_info and drive_info.get('is_system', False):
            self.start_btn.config(state=tk.DISABLED)
        elif drive_info:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)

    def start_wipe(self):
        """Запуск затирания"""
        if not self.current_drive:
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_drive_first", "Сначала выберите диск")
            )
            return

        if self.current_drive.get('is_system', False):
            messagebox.showerror(
                self.app.i18n.get("error", "Ошибка"),
                self.app.i18n.get("cannot_wipe_system", "Нельзя затирать системный диск!")
            )
            return

        # Подтверждение
        if not messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            self.app.i18n.get("confirm_wipe",
                             f"Все данные на диске {self.current_drive['path']} будут безвозвратно уничтожены!\n\nПродолжить?")
        ):
            return

        # Сброс прогресса
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")

        # Очистка лога
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Запуск затирания
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.app.data_wiper.wipe_disk(
            self.current_drive['path'],
            self.method_id.get(),               # используем идентификатор
            self.passes_var.get(),
            self.verify_var.get()
        )

        self._log(self.app.i18n.get("wipe_started", f"Затирание запущено для диска {self.current_drive['path']}"))

    def stop_wipe(self):
        """Остановка затирания"""
        if messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            self.app.i18n.get("confirm_stop_wipe", "Остановить затирание?")
        ):
            self.app.data_wiper.stop()
            self._log(self.app.i18n.get("wipe_stopping", "Остановка затирания..."))

    def process_messages(self):
        """Обработка сообщений от потока затирания"""
        if hasattr(self.app, 'data_wiper'):
            msg = self.app.data_wiper.get_message()

            while msg:
                msg_type = msg[0]

                if msg_type == "log" and len(msg) >= 2:
                    self._log(msg[1])

                elif msg_type == "progress" and len(msg) >= 2:
                    self.progress_bar['value'] = msg[1]
                    self.progress_label.config(text=f"{msg[1]:.1f}%")

                elif msg_type == "complete" and len(msg) >= 2:
                    self._log(msg[1])
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    messagebox.showinfo(
                        self.app.i18n.get("success", "Успех"),
                        msg[1]
                    )

                elif msg_type == "error" and len(msg) >= 2:
                    # Локализованное сообщение об ошибке
                    error_msg = self.app.i18n.get("log_error", "Ошибка: {}").format(msg[1])
                    self._log(error_msg, is_error=True)
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    messagebox.showerror(
                        self.app.i18n.get("error", "Ошибка"),
                        msg[1]
                    )

                msg = self.app.data_wiper.get_message()

        self.after(100, self.process_messages)

    def _log(self, message, is_error=False):
        """Добавление сообщения в лог"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")

        if is_error:
            # Выделение ошибки красным
            end_pos = self.log_text.index(tk.END)
            start_pos = f"{end_pos.split('.')[0]}.0"
            self.log_text.tag_add("error", f"{start_pos}-2l", f"{start_pos}-1l")
            self.log_text.tag_config("error", foreground="red")

        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_language(self):
        """Обновление языка интерфейса"""
        self.settings_frame.config(text=self.app.i18n.get("wipe_settings", "Настройки затирания"))
        self.progress_frame.config(text=self.app.i18n.get("progress", "Прогресс"))
        self.log_frame.config(text=self.app.i18n.get("log", "Лог"))

        self.method_label.config(text=self.app.i18n.get("wipe_method", "Метод затирания:"))
        self.passes_label.config(text=self.app.i18n.get("wipe_passes", "Количество проходов:"))
        self.verify_cb.config(text=self.app.i18n.get("verify_wipe", "Проверить после затирания"))
        self.start_btn.config(text=self.app.i18n.get("start_wipe", "🧹 Начать затирание"))
        self.stop_btn.config(text=self.app.i18n.get("stop", "⏹ Стоп"))

        # Обновляем список методов в комбобоксе
        self.method_combo['values'] = self._get_localized_methods()
        self._set_method_combo(self.method_id.get())

    def update_theme(self):
        """Обновление темы оформления"""
        colors = self.app.theme_manager.colors
        # Обновляем цвета текстового поля лога
        self.log_text.config(
            bg=colors.get("entry_bg", "#ffffff"),
            fg=colors.get("entry_fg", "#000000")
        )