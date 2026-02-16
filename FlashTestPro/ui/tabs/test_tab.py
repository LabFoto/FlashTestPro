"""
Вкладка тестирования дисков
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.widgets.progress_panel import ProgressPanel
from ui.widgets.log_viewer import LogViewer
from ui.widgets.chart_widget import SpeedChart
from utils.logger import get_logger

class TestTab(ttk.Frame):
    """Вкладка тестирования"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.logger = get_logger(__name__)
        
        self.current_drive = None
        self.create_widgets()
        
        # Запуск обработки сообщений
        self.after(100, self.process_messages)
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной контейнер
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель - настройки теста
        settings_frame = ttk.LabelFrame(
            main_frame, 
            text=self.app.i18n.get("test_settings", "Настройки тестирования")
        )
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Количество проходов
        passes_frame = ttk.Frame(settings_frame)
        passes_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(passes_frame, text=self.app.i18n.get("passes", "Проходы:")).pack(side=tk.LEFT)
        
        self.passes_var = tk.IntVar(value=1)
        passes_spinbox = ttk.Spinbox(
            passes_frame, 
            from_=1, to=100, 
            textvariable=self.passes_var,
            width=10
        )
        passes_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        # Паттерны тестирования
        patterns_frame = ttk.Frame(settings_frame)
        patterns_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(patterns_frame, text=self.app.i18n.get("patterns", "Паттерны:")).pack(side=tk.LEFT)
        
        self.test_ones = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            patterns_frame, 
            text=self.app.i18n.get("pattern_ones", "Единицы (0xFF)"),
            variable=self.test_ones
        ).pack(side=tk.LEFT, padx=(10, 5))
        
        self.test_zeros = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            patterns_frame, 
            text=self.app.i18n.get("pattern_zeros", "Нули (0x00)"),
            variable=self.test_zeros
        ).pack(side=tk.LEFT, padx=5)
        
        self.test_random = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            patterns_frame, 
            text=self.app.i18n.get("pattern_random", "Случайные"),
            variable=self.test_random
        ).pack(side=tk.LEFT, padx=5)
        
        # Опции
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.verify_read = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, 
            text=self.app.i18n.get("verify_read", "Проверка чтения"),
            variable=self.verify_read
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        self.auto_format = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, 
            text=self.app.i18n.get("auto_format", "Форматировать после теста"),
            variable=self.auto_format
        ).pack(side=tk.LEFT)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("start_test", "🚀 Начать тест"),
            command=self.start_test,
            width=20
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("pause", "⏸ Пауза"),
            command=self.pause_test,
            state=tk.DISABLED,
            width=15
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("stop", "⏹ Стоп"),
            command=self.stop_test,
            state=tk.DISABLED,
            width=15
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Панель с графиком и логом
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая часть - график и прогресс
        left_content = ttk.Frame(content_frame)
        left_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # График скорости
        self.chart_widget = SpeedChart(left_content, self.app)
        self.chart_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Панель прогресса
        self.progress_panel = ProgressPanel(left_content, self.app)
        self.progress_panel.pack(fill=tk.X)
        
        # Правая часть - лог
        right_content = ttk.Frame(content_frame)
        right_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(
            right_content, 
            text=self.app.i18n.get("event_log", "Журнал событий"),
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)
        
        self.log_viewer = LogViewer(right_content, self.app)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)
    
    def on_drive_selected(self, drive_info):
        """Обработка выбора диска"""
        self.current_drive = drive_info
        
        if drive_info and drive_info.get('is_system', False):
            self.start_btn.config(state=tk.DISABLED)
            self.log_viewer.log(self.app.i18n.get("system_drive_warning", "⚠️ Системные диски нельзя тестировать!"), "warning")
        elif drive_info:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)
    
    def start_test(self):
        """Запуск тестирования"""
        if not self.current_drive:
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_drive_first", "Сначала выберите диск")
            )
            return
        
        if self.current_drive.get('is_system', False):
            messagebox.showerror(
                self.app.i18n.get("error", "Ошибка"),
                self.app.i18n.get("cannot_test_system", "Нельзя тестировать системный диск!")
            )
            return
        
        # Проверка выбора паттернов
        if not (self.test_ones.get() or self.test_zeros.get() or self.test_random.get()):
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_pattern", "Выберите хотя бы один паттерн тестирования")
            )
            return
        
        # Подтверждение
        if not self._confirm_test_start():
            return
        
        # Параметры теста
        params = {
            'passes': self.passes_var.get(),
            'test_ones': self.test_ones.get(),
            'test_zeros': self.test_zeros.get(),
            'test_random': self.test_random.get(),
            'test_verify': self.verify_read.get(),
            'auto_format': self.auto_format.get(),
            'filesystem': 'FAT32'  # По умолчанию
        }
        
        # Очистка предыдущих результатов
        self.chart_widget.clear()
        self.progress_panel.reset()
        self.log_viewer.clear()
        
        # Запуск теста
        self.app.disk_tester.start_test(self.current_drive['path'], params)
        
        # Обновление состояния кнопок
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text=self.app.i18n.get("pause", "⏸ Пауза"))
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log_viewer.log(self.app.i18n.get("test_started", f"Тестирование запущено для диска {self.current_drive['path']}"), "info")
        self.app.main_window.update_status(self.app.i18n.get("testing", "Тестирование..."))
    
    def _confirm_test_start(self):
        """Подтверждение начала теста"""
        warning_text = self.app.i18n.get(
            "confirm_test",
            f"⚠️ ВНИМАНИЕ! Все данные на диске {self.current_drive['path']} будут уничтожены!\n\n"
            f"Параметры теста:\n"
            f"• Проходов: {self.passes_var.get()}\n"
            f"• Единицы: {'Да' if self.test_ones.get() else 'Нет'}\n"
            f"• Нули: {'Да' if self.test_zeros.get() else 'Нет'}\n"
            f"• Случайные: {'Да' if self.test_random.get() else 'Нет'}\n"
            f"• Проверка чтения: {'Да' if self.verify_read.get() else 'Нет'}\n"
            f"• Форматирование после теста: {'Да' if self.auto_format.get() else 'Нет'}\n\n"
            f"Вы уверены, что хотите продолжить?"
        )
        
        return messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            warning_text,
            icon='warning'
        )
    
    def pause_test(self):
        """Пауза/продолжение теста"""
        paused = self.app.disk_tester.pause()
        
        if paused is not None:
            if paused:
                self.pause_btn.config(text=self.app.i18n.get("resume", "▶ Продолжить"))
                self.log_viewer.log(self.app.i18n.get("test_paused", "Тест приостановлен"), "warning")
            else:
                self.pause_btn.config(text=self.app.i18n.get("pause", "⏸ Пауза"))
                self.log_viewer.log(self.app.i18n.get("test_resumed", "Тест продолжен"), "info")
    
    def stop_test(self):
        """Остановка теста"""
        if messagebox.askyesno(
            self.app.i18n.get("confirm", "Подтверждение"),
            self.app.i18n.get("confirm_stop", "Остановить тестирование?")
        ):
            self.app.disk_tester.stop()
            self.log_viewer.log(self.app.i18n.get("stopping_test", "Остановка теста..."), "warning")
            
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
    
    def process_messages(self):
        """Обработка сообщений от потока тестирования"""
        try:
            if hasattr(self.app, 'disk_tester'):
                msg = self.app.disk_tester.get_message()
                
                while msg:
                    msg_type = msg[0]
                    
                    if msg_type == "log" and len(msg) >= 3:
                        self.log_viewer.log(msg[1], msg[2])
                    
                    elif msg_type == "progress" and len(msg) >= 2:
                        self.progress_panel.update_progress(msg[1])
                    
                    elif msg_type == "speed" and len(msg) >= 3:
                        self.chart_widget.add_data_point(msg[2], msg[1])
                        self.progress_panel.update_speed(msg[1])
                        
                        # Обновляем время
                        stats = self.app.disk_tester.get_statistics()
                        self.progress_panel.update_time(stats.get('elapsed_time', '00:00:00'))
                    
                    elif msg_type == "bad_sector" and len(msg) >= 4:
                        self.log_viewer.log(f"{self.app.i18n.get('bad_sector', 'Битый сектор')}: {msg[1]}", "error")
                        self.progress_panel.add_bad_sector()
                    
                    elif msg_type == "complete" and len(msg) >= 2:
                        self._on_test_complete(msg[1])
                    
                    elif msg_type == "error" and len(msg) >= 2:
                        self._on_test_error(msg[1])
                    
                    msg = self.app.disk_tester.get_message()
                
                # Обновляем состояние кнопок в зависимости от статуса теста
                if self.app.disk_tester.is_running():
                    if hasattr(self.app.disk_tester, 'paused') and self.app.disk_tester.paused:
                        self.pause_btn.config(text=self.app.i18n.get("resume", "▶ Продолжить"))
                    else:
                        self.pause_btn.config(text=self.app.i18n.get("pause", "⏸ Пауза"))
        except Exception as e:
            self.logger.error(f"Ошибка в process_messages: {e}")
        
        self.after(100, self.process_messages)
    
    def _on_test_complete(self, message):
        """Обработка завершения теста"""
        self.log_viewer.log(message, "success")
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.progress_panel.update_progress(100)
        self.app.main_window.update_status(self.app.i18n.get("ready", "Готов"))
        
        # Обновление вкладки результатов
        stats = self.app.disk_tester.get_statistics()
        self.app.main_window.results_tab.update_results(stats)
        
        # Переключение на вкладку результатов
        self.app.main_window.notebook.select(3)
    
    def _on_test_error(self, error_msg):
        """Обработка ошибки теста"""
        self.log_viewer.log(f"{self.app.i18n.get('error', 'Ошибка')}: {error_msg}", "error")
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.app.main_window.update_status(self.app.i18n.get("error", "Ошибка"), "error")
    
    def run_benchmark(self):
        """Запуск бенчмарка (быстрый тест)"""
        if not self.current_drive:
            return
        
        # Установка параметров для бенчмарка
        self.passes_var.set(1)
        self.test_ones.set(True)
        self.test_zeros.set(True)
        self.test_random.set(True)
        self.verify_read.set(True)
        self.auto_format.set(False)
        
        # Запуск теста
        self.start_test()
    
    def update_language(self):
        """Обновление языка"""
        pass
    
    def update_theme(self):
        """Обновление темы"""
        self.chart_widget.update_theme()
        self.progress_panel.update_theme()
        self.log_viewer.update_theme()