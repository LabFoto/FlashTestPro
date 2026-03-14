"""
Вкладка проверки реальной ёмкости диска
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class CapacityTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None
        self.create_widgets()
        self.after(100, self.process_messages)

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Кнопка запуска
        self.start_btn = ttk.Button(
            main_frame,
            text=self.app.i18n.get("start_capacity_test", "📏 Проверить ёмкость"),
            command=self.start_test,
            state=tk.DISABLED
        )
        self.start_btn.pack(pady=10)

        # Прогресс
        self.progress_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("progress", "Прогресс"))
        self.progress_frame.pack(fill=tk.X, pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(pady=(0, 10))

        # Лог
        self.log_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("log", "Лог"))
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_drive_selected(self, drive_info):
        self.current_drive = drive_info
        if drive_info and not drive_info.get('is_system', False):
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)

    def start_test(self):
        if not self.current_drive:
            return
        if messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            self.app.i18n.get("confirm_capacity_test",
                             "Все данные на диске будут уничтожены!\nПродолжить?")
        ):
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")
            self._clear_log()
            self.start_btn.config(state=tk.DISABLED)
            self.app.capacity_tester.start_test(self.current_drive['path'])
            self._log(self.app.i18n.get("capacity_test_started", "Запуск проверки ёмкости..."))

    def process_messages(self):
        if hasattr(self.app, 'capacity_tester'):
            msg = self.app.capacity_tester.get_message()
            while msg:
                msg_type = msg[0]
                if msg_type == "log":
                    self._log(msg[1], msg[2] if len(msg) > 2 else "info")
                elif msg_type == "progress":
                    self.progress_bar['value'] = msg[1]
                    self.progress_label.config(text=f"{msg[1]:.1f}%")
                elif msg_type == "result":
                    result = msg[1]
                    self._log(f"Заявлено: {result['claimed']:.2f} GB", "info")
                    self._log(f"Реально: {result['real']:.2f} GB", "info")
                    self._log(f"Статус: {result['status']}", "success" if "✅" in result['status'] else "error")
                elif msg_type == "complete":
                    self._log(msg[1], "success")
                    self.start_btn.config(state=tk.NORMAL)
                elif msg_type == "error":
                    self._log(f"Ошибка: {msg[1]}", "error")
                    self.start_btn.config(state=tk.NORMAL)
                elif msg_type == "unmount_notice":
                    self._log(self.app.i18n.get("unmount_notice_message", "Диск {} был размонтирован.").format(msg[1]), "warning")
                msg = self.app.capacity_tester.get_message()
        self.after(100, self.process_messages)

    def _log(self, message, level="info"):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        # Раскраска (можно доработать)
        if level == "error":
            self.log_text.tag_add("error", "end-2l", "end-1l")
            self.log_text.tag_config("error", foreground="red")
        elif level == "success":
            self.log_text.tag_add("success", "end-2l", "end-1l")
            self.log_text.tag_config("success", foreground="green")
        elif level == "warning":
            self.log_text.tag_add("warning", "end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground="orange")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_language(self):
        self.start_btn.config(text=self.app.i18n.get("start_capacity_test", "📏 Проверить ёмкость"))
        self.progress_frame.config(text=self.app.i18n.get("progress", "Прогресс"))
        self.log_frame.config(text=self.app.i18n.get("log", "Лог"))

    def update_theme(self):
        colors = self.app.theme_manager.colors
        self.log_text.config(
            bg=colors.get("entry_bg", "#ffffff"),
            fg=colors.get("entry_fg", "#000000")
        )