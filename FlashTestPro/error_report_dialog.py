"""
Модуль диалога отчетов об ошибках
"""
import tkinter as tk
from tkinter import ttk, messagebox
import platform

class ErrorReportDialog:
    """Диалог просмотра ошибок"""

    def __init__(self, parent, logger):
        self.parent = parent
        self.logger = logger
        self.dialog = None
        self.create_dialog()
        self.load_errors()

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

        # Кнопки управления
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(side="right")

        ttk.Button(
            button_frame,
            text="🔄 Обновить",
            command=self.load_errors
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="🗑 Очистить старые",
            command=self.clear_old_logs
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="📁 Открыть папку",
            command=self.open_logs_folder
        ).pack(side="left", padx=5)

        # Статистика
        self.stats_frame = ttk.LabelFrame(self.dialog, text=" Статистика ", padding=10)
        self.stats_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.stats_text = tk.Text(
            self.stats_frame,
            height=8,
            bg="#2d2d2d",
            fg="white",
            font=("Consolas", 9),
            wrap="word"
        )
        self.stats_text.pack(fill="both", expand=True)

        # Текстовое поле для лога ошибок
        log_frame = ttk.LabelFrame(self.dialog, text=" Лог ошибок ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_text = tk.Text(
            log_frame,
            bg="#2d2d2d",
            fg="white",
            font=("Consolas", 9),
            wrap="word",
            height=20
        )

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Настройка тегов для раскраски
        self.log_text.tag_configure("error", foreground="#f44336")
        self.log_text.tag_configure("warning", foreground="#ff9800")
        self.log_text.tag_configure("critical", foreground="#ff0000", font=("Consolas", 10, "bold"))

    def load_errors(self):
        """Загрузка ошибок"""
        self.log_text.delete("1.0", "end")
        self.stats_text.delete("1.0", "end")

        # Загрузка статистики
        stats = self.logger.get_error_statistics()
        stats_str = f"""
Всего ошибок: {stats['total_errors']}
Всего предупреждений: {stats['total_warnings']}

Частые ошибки:
"""
        for error, count in list(stats['errors_by_type'].items())[:10]:
            stats_str += f"  • {error}: {count}\n"

        stats_str += "\nМодули с ошибками:\n"
        for module, count in list(stats['errors_by_module'].items())[:10]:
            stats_str += f"  • {module}: {count}\n"

        self.stats_text.insert("1.0", stats_str)

        # Загрузка лога
        errors = self.logger.get_recent_errors(200)
        if errors:
            for error in errors:
                if "ERROR" in error or "CRITICAL" in error:
                    tag = "critical" if "CRITICAL" in error else "error"
                    self.log_text.insert("end", error, tag)
                elif "WARNING" in error:
                    self.log_text.insert("end", error, "warning")
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