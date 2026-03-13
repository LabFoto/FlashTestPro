"""
Вкладка тестирования дисков с расширенными настройками производительности
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import os

from ui.widgets.progress_panel import ProgressPanel
from ui.widgets.log_viewer import LogViewer
from ui.widgets.chart_widget import SpeedChart
from utils.logger import get_logger

class TestTab(ttk.Frame):
    """Вкладка тестирования с расширенными настройками"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.logger = get_logger(__name__)

        self.current_drive = None
        self.create_widgets()

        # Запуск обработки сообщений
        self.after(100, self.process_messages)

    def create_widgets(self):
        """Создание виджетов вкладки с расширенными настройками"""
        # Основной контейнер с двумя колонками
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая колонка - настройки теста (увеличена ширина)
        left_column = ttk.Frame(main_container, width=380)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_column.pack_propagate(False)

        # Правая колонка - график и лог
        right_column = ttk.Frame(main_container)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Создаем панель настроек в левой колонке
        self._create_settings_panel(left_column)

        # Создаем график и лог в правой колонке
        self._create_chart_and_log_panel(right_column)

    def _create_settings_panel(self, parent):
        """Создание панели настроек"""
        colors = self.app.theme_manager.colors

        # Контейнер для настроек с прокруткой
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем Canvas с правильным фоном
        canvas = tk.Canvas(
            canvas_frame,
            highlightthickness=0,
            bg=colors["bg"],
            borderwidth=0
        )

        # Создаем Scrollbar
        scrollbar = tk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=canvas.yview,
            width=20)

        # Создаем фрейм для содержимого
        scrollable_frame = ttk.Frame(canvas)

        # Настраиваем прокрутку
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Создаем окно в canvas
        canvas_window = canvas.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw",
            width=canvas.winfo_width()
        )

        # Настраиваем canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Размещаем элементы
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Обновление ширины окна при изменении размера
        def _configure_canvas(event):
            # Обновляем ширину окна в canvas
            canvas.itemconfig(canvas_window, width=event.width)
            # Обновляем ширину scrollable_frame
            scrollable_frame.config(width=event.width)

        canvas.bind("<Configure>", _configure_canvas)

        # Настройки тестирования
        self.settings_frame = ttk.LabelFrame(
            scrollable_frame,
            text=self.app.i18n.get("test_settings", "Настройки тестирования")
        )
        self.settings_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Базовые настройки
        self._create_basic_settings()

        # Разделитель
        ttk.Separator(self.settings_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

        # Расширенные настройки производительности
        self._create_performance_settings()

        # Добавляем пустое пространство внизу для удобства прокрутки
        ttk.Frame(scrollable_frame, height=20).pack()

    def _create_basic_settings(self):
        """Базовые настройки теста"""
        # Количество проходов
        passes_frame = ttk.Frame(self.settings_frame)
        passes_frame.pack(fill=tk.X, padx=10, pady=10)

        self.passes_label = ttk.Label(passes_frame, text=self.app.i18n.get("passes", "Проходы:"))
        self.passes_label.pack(side=tk.LEFT)

        self.passes_var = tk.IntVar(value=1)
        self.passes_combo = ttk.Combobox(
            passes_frame,
            textvariable=self.passes_var,
            values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            width=5,
            state='readonly'
        )
        self.passes_combo.pack(side=tk.LEFT, padx=(5, 20))

        # Режим тестирования
        mode_frame = ttk.Frame(self.settings_frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.mode_label = ttk.Label(mode_frame, text=self.app.i18n.get("test_mode", "Режим:"))
        self.mode_label.pack(anchor=tk.W)

        self.test_mode = tk.StringVar(value="free")
        self.mode_free_rb = ttk.Radiobutton(
            mode_frame,
            text=self.app.i18n.get("mode_free", "Только свободное место"),
            variable=self.test_mode,
            value="free"
        )
        self.mode_free_rb.pack(anchor=tk.W, padx=(10, 0), pady=2)

        self.mode_full_rb = ttk.Radiobutton(
            mode_frame,
            text=self.app.i18n.get("mode_full", "Полное тестирование (все сектора)"),
            variable=self.test_mode,
            value="full"
        )
        self.mode_full_rb.pack(anchor=tk.W, padx=(10, 0), pady=2)

        # Паттерны тестирования
        patterns_frame = ttk.Frame(self.settings_frame)
        patterns_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.patterns_label = ttk.Label(patterns_frame, text=self.app.i18n.get("patterns", "Паттерны:"))
        self.patterns_label.pack(anchor=tk.W)

        self.test_ones = tk.BooleanVar(value=False)
        self.ones_cb = ttk.Checkbutton(
            patterns_frame,
            text=self.app.i18n.get("pattern_ones", "Единицы (0xFF)"),
            variable=self.test_ones
        )
        self.ones_cb.pack(anchor=tk.W, padx=(10, 0), pady=2)

        self.test_zeros = tk.BooleanVar(value=False)
        self.zeros_cb = ttk.Checkbutton(
            patterns_frame,
            text=self.app.i18n.get("pattern_zeros", "Нули (0x00)"),
            variable=self.test_zeros
        )
        self.zeros_cb.pack(anchor=tk.W, padx=(10, 0), pady=2)

        self.test_random = tk.BooleanVar(value=False)
        self.random_cb = ttk.Checkbutton(
            patterns_frame,
            text=self.app.i18n.get("pattern_random", "Случайные"),
            variable=self.test_random
        )
        self.random_cb.pack(anchor=tk.W, padx=(10, 0), pady=2)

        self.select_all_btn = ttk.Button(
            patterns_frame,
            text=self.app.i18n.get("select_all", "Все"),
            command=self._select_all_patterns
        )
        self.select_all_btn.pack(anchor=tk.W, padx=(10, 0), pady=5)

        # Опции
        options_frame = ttk.Frame(self.settings_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.verify_read = tk.BooleanVar(value=True)
        self.verify_cb = ttk.Checkbutton(
            options_frame,
            text=self.app.i18n.get("verify_read", "Проверка чтения"),
            variable=self.verify_read
        )
        self.verify_cb.pack(anchor=tk.W, pady=2)

        self.auto_format = tk.BooleanVar(value=False)
        self.auto_format_cb = ttk.Checkbutton(
            options_frame,
            text=self.app.i18n.get("auto_format", "Форматировать после теста"),
            variable=self.auto_format
        )
        self.auto_format_cb.pack(anchor=tk.W, pady=2)

    def _create_performance_settings(self):
        """Создание расширенных настроек производительности"""
        self.perf_frame = ttk.LabelFrame(
            self.settings_frame,
            text=self.app.i18n.get("performance_settings", "⚡ Настройки производительности")
        )
        self.perf_frame.pack(fill=tk.X, padx=10, pady=5)

        # Размер чанка с подсказкой
        chunk_frame = ttk.Frame(self.perf_frame)
        chunk_frame.pack(fill=tk.X, padx=10, pady=5)

        chunk_label_frame = ttk.Frame(chunk_frame)
        chunk_label_frame.pack(anchor=tk.W)

        self.chunk_label = ttk.Label(
            chunk_label_frame,
            text=self.app.i18n.get("chunk_size", "Размер блока (MB):")
        )
        self.chunk_label.pack(side=tk.LEFT)

        # Кнопка с подсказкой
        self.chunk_info_btn = ttk.Label(
            chunk_label_frame,
            text=" ⓘ",
            cursor="question_arrow",
            font=("Segoe UI", 10, "bold")
        )
        self.chunk_info_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.chunk_info_btn.bind("<Enter>", self._show_chunk_tooltip)
        self.chunk_info_btn.bind("<Leave>", self._hide_tooltip)

        # Переменная для размера чанка
        self.chunk_size_var = tk.IntVar(
            value=self.app.config.get("testing", {}).get("chunk_size_mb", 32)
        )

        # Выпадающий список для выбора размера чанка
        chunk_control_frame = ttk.Frame(chunk_frame)
        chunk_control_frame.pack(anchor=tk.W, pady=(5, 0))

        self.chunk_combo = ttk.Combobox(
            chunk_control_frame,
            textvariable=self.chunk_size_var,
            values=[1, 2, 4, 8, 16, 32, 64, 128, 256],
            width=8,
            state='readonly'
        )
        self.chunk_combo.pack(side=tk.LEFT)
        self.chunk_combo.bind("<<ComboboxSelected>>", self._on_chunk_change)

        # Подпись с рекомендацией
        self.chunk_recommendation = ttk.Label(
            chunk_frame,
            text="",
            font=("Segoe UI", 8),
            foreground="#888888",
            wraplength=250
        )
        self.chunk_recommendation.pack(anchor=tk.W, pady=(5, 0))

        # Адаптивный размер чанка
        adaptive_frame = ttk.Frame(self.perf_frame)
        adaptive_frame.pack(fill=tk.X, padx=10, pady=5)

        adaptive_check_frame = ttk.Frame(adaptive_frame)
        adaptive_check_frame.pack(anchor=tk.W)

        self.adaptive_chunk_var = tk.BooleanVar(
            value=self.app.config.get("testing", {}).get("adaptive_chunk", True)
        )
        self.adaptive_chunk_cb = ttk.Checkbutton(
            adaptive_check_frame,
            text=self.app.i18n.get("adaptive_chunk", "🔄 Адаптивный размер блока"),
            variable=self.adaptive_chunk_var,
            command=self._on_adaptive_chunk_toggle
        )
        self.adaptive_chunk_cb.pack(side=tk.LEFT)

        # Кнопка с подсказкой для адаптивного режима
        self.adaptive_info_btn = ttk.Label(
            adaptive_check_frame,
            text=" ⓘ",
            cursor="question_arrow",
            font=("Segoe UI", 10, "bold")
        )
        self.adaptive_info_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.adaptive_info_btn.bind("<Enter>", self._show_adaptive_tooltip)
        self.adaptive_info_btn.bind("<Leave>", self._hide_tooltip)

        # Параллельное тестирование
        parallel_frame = ttk.Frame(self.perf_frame)
        parallel_frame.pack(fill=tk.X, padx=10, pady=5)

        parallel_check_frame = ttk.Frame(parallel_frame)
        parallel_check_frame.pack(anchor=tk.W)

        self.parallel_test_var = tk.BooleanVar(
            value=self.app.config.get("testing", {}).get("parallel_testing", False)
        )
        self.parallel_test_cb = ttk.Checkbutton(
            parallel_check_frame,
            text=self.app.i18n.get("parallel_test", "⚡ Параллельное тестирование"),
            variable=self.parallel_test_var,
            command=self._on_parallel_test_toggle
        )
        self.parallel_test_cb.pack(side=tk.LEFT)

        # Кнопка с подсказкой для параллельного режима
        self.parallel_info_btn = ttk.Label(
            parallel_check_frame,
            text=" ⓘ",
            cursor="question_arrow",
            font=("Segoe UI", 10, "bold")
        )
        self.parallel_info_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.parallel_info_btn.bind("<Enter>", self._show_parallel_tooltip)
        self.parallel_info_btn.bind("<Leave>", self._hide_tooltip)

        # Количество потоков
        threads_frame = ttk.Frame(parallel_frame)
        threads_frame.pack(fill=tk.X, padx=(20, 0), pady=(5, 0))

        self.threads_label = ttk.Label(
            threads_frame,
            text=self.app.i18n.get("threads", "Потоки:")
        )
        self.threads_label.pack(side=tk.LEFT)

        self.threads_var = tk.IntVar(
            value=self.app.config.get("testing", {}).get("max_threads", 4)
        )
        self.threads_combo = ttk.Combobox(
            threads_frame,
            textvariable=self.threads_var,
            values=[1, 2, 4, 8, 16],
            width=5,
            state='readonly'
        )
        self.threads_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Изначально отключаем выбор потоков, если параллельный режим выключен
        if not self.parallel_test_var.get():
            self.threads_combo.config(state='disabled')
            self.threads_label.config(foreground='gray')

        # Быстрый тест
        quick_frame = ttk.Frame(self.perf_frame)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        quick_check_frame = ttk.Frame(quick_frame)
        quick_check_frame.pack(anchor=tk.W)

        self.quick_test_var = tk.BooleanVar(value=False)
        self.quick_test_cb = ttk.Checkbutton(
            quick_check_frame,
            text=self.app.i18n.get("quick_test", "⚡ Быстрый тест"),
            variable=self.quick_test_var
        )
        self.quick_test_cb.pack(side=tk.LEFT)

        # Кнопка с подсказкой для быстрого теста
        self.quick_info_btn = ttk.Label(
            quick_check_frame,
            text=" ⓘ",
            cursor="question_arrow",
            font=("Segoe UI", 10, "bold")
        )
        self.quick_info_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.quick_info_btn.bind("<Enter>", self._show_quick_tooltip)
        self.quick_info_btn.bind("<Leave>", self._hide_tooltip)

        # Кнопки управления
        self._create_control_buttons()

        # Обновляем рекомендацию по размеру чанка
        self._update_chunk_recommendation()

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        buttons_frame = ttk.Frame(self.settings_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("start_test", "🚀 Начать тест"),
            command=self.start_test,
            width=20
        )
        self.start_btn.pack(fill=tk.X, pady=2)

        self.pause_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("pause", "⏸ Пауза"),
            command=self.pause_test,
            state=tk.DISABLED,
            width=20
        )
        self.pause_btn.pack(fill=tk.X, pady=2)

        self.stop_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("stop", "⏹ Стоп"),
            command=self.stop_test,
            state=tk.DISABLED,
            width=20
        )
        self.stop_btn.pack(fill=tk.X, pady=2)

    def _create_chart_and_log_panel(self, parent):
        """Создание панели с графиком и журналом событий с новым распределением высоты"""
        # Используем PanedWindow для регулировки пропорций
        paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # График скорости (35% высоты)
        chart_container = ttk.Frame(paned)
        paned.add(chart_container, weight=35)

        self.chart_frame = ttk.LabelFrame(
            chart_container,
            text=self.app.i18n.get("speed_chart", "График скорости")
        )
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chart_widget = SpeedChart(self.chart_frame, self.app)
        self.chart_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Панель прогресса (15% высоты)
        self.progress_panel = ProgressPanel(paned, self.app)
        paned.add(self.progress_panel, weight=15)

        # Журнал событий (50% высоты)
        log_container = ttk.Frame(paned)
        paned.add(log_container, weight=50)

        self.log_frame = ttk.LabelFrame(
            log_container,
            text=self.app.i18n.get("event_log", "Журнал событий")
        )
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_viewer = LogViewer(self.log_frame, self.app)
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

    def _on_chunk_change(self, event):
        """Обработка изменения размера чанка"""
        self._update_chunk_recommendation()

    def _on_adaptive_chunk_toggle(self):
        """Обработка переключения адаптивного режима"""
        if self.adaptive_chunk_var.get():
            self.chunk_combo.config(state='disabled')
        else:
            self.chunk_combo.config(state='readonly')

    def _on_parallel_test_toggle(self):
        """Обработка переключения параллельного тестирования"""
        if self.parallel_test_var.get():
            self.threads_combo.config(state='readonly')
            self.threads_label.config(foreground='')
        else:
            self.threads_combo.config(state='disabled')
            self.threads_label.config(foreground='gray')

    def _update_chunk_recommendation(self):
        """Обновление рекомендации по размеру чанка"""
        chunk_size = self.chunk_size_var.get()

        if self.current_drive:
            drive_size = self.current_drive.get('total_bytes', 0) / (1024**3)  # в GB

            if drive_size < 16:
                recommended = 16
            elif drive_size < 64:
                recommended = 32
            elif drive_size < 256:
                recommended = 64
            else:
                recommended = 128

            if chunk_size < recommended:
                text = f"💡 Рекомендуется {recommended} MB для диска {drive_size:.1f} GB"
            else:
                text = f"✓ Оптимально для диска {drive_size:.1f} GB"

            self.chunk_recommendation.config(text=text)
        else:
            self.chunk_recommendation.config(text="")

    # ==================== ВСПЛЫВАЮЩИЕ ПОДСКАЗКИ ====================

    def _show_chunk_tooltip(self, event):
        tooltip_text = self.app.i18n.get(
            "chunk_tooltip",
            "Размер блока данных за одну операцию:\n\n"
            "• Меньше (1-16 MB) - выше точность, медленнее\n"
            "• Больше (64-256 MB) - выше скорость, меньше точность локализации ошибок\n\n"
            "Рекомендации:\n"
            "• Для HDD: 32-64 MB\n"
            "• Для SSD: 64-128 MB\n"
            "• Для Flash: 16-32 MB\n\n"
            "Выбор размера влияет на:\n"
            "- Скорость тестирования\n"
            "- Точность определения битых секторов\n"
            "- Нагрузку на систему"
        )
        self._show_tooltip(event, tooltip_text)

    def _show_adaptive_tooltip(self, event):
        tooltip_text = self.app.i18n.get(
            "adaptive_tooltip",
            "Адаптивный размер блока автоматически оптимизирует процесс тестирования:\n\n"
            "• При высокой скорости - увеличивает блок для ускорения\n"
            "• При появлении ошибок - уменьшает блок для точной локализации\n"
            "• Анализирует производительность диска в реальном времени\n"
            "• Оптимизирует соотношение скорость/точность\n\n"
            "Рекомендуется включать для неизвестных дисков"
        )
        self._show_tooltip(event, tooltip_text)

    def _show_parallel_tooltip(self, event):
        tooltip_text = self.app.i18n.get(
            "parallel_tooltip",
            "Параллельное тестирование использует несколько потоков:\n\n"
            "• Разбивает диск на независимые зоны\n"
            "• Тестирует зоны одновременно в разных потоках\n"
            "• Ускорение в 2-8 раз на многоядерных процессорах\n"
            "• Автоматическое распределение нагрузки\n\n"
            "⚠️ Может увеличить нагрузку на систему\n"
            "✓ Рекомендуется для SSD и быстрых накопителей"
        )
        self._show_tooltip(event, tooltip_text)

    def _show_quick_tooltip(self, event):
        tooltip_text = self.app.i18n.get(
            "quick_tooltip",
            "Быстрый тест проверяет только ключевые области диска:\n\n"
            "• Начало диска (загрузочный сектор)\n"
            "• Середина диска\n"
            "• Конец диска\n"
            "• Несколько случайных позиций\n\n"
            "Преимущества:\n"
            "• Занимает 1-2 минуты\n"
            "• Выявляет очевидные проблемы\n"
            "• Безопасен для данных\n\n"
            "Ограничения:\n"
            "• Не заменяет полное тестирование\n"
            "• Может пропустить скрытые дефекты"
        )
        self._show_tooltip(event, tooltip_text)

    def _show_tooltip(self, event, text):
        x = event.widget.winfo_rootx() + 25
        y = event.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.attributes('-topmost', True)

        label = tk.Label(
            self.tooltip,
            text=text,
            justify=tk.LEFT,
            bg="#ffffe0",
            fg="black",
            relief=tk.SOLID,
            borderwidth=1,
            padx=5, pady=5
        )
        label.pack()

    def _hide_tooltip(self, event):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

    # ==================== ОСНОВНАЯ ЛОГИКА ====================

    def _select_all_patterns(self):
        self.test_ones.set(True)
        self.test_zeros.set(True)
        self.test_random.set(True)

    def on_drive_selected(self, drive_info):
        self.current_drive = drive_info
        self._update_chunk_recommendation()

        if drive_info and drive_info.get('is_system', False):
            self.start_btn.config(state=tk.DISABLED)
            self.log_viewer.log(
                self.app.i18n.get("system_drive_warning", "⚠️ Системные диски нельзя тестировать!"),
                "warning"
            )
        elif drive_info:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)

    def start_test(self):
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

        if not (self.test_ones.get() or self.test_zeros.get() or self.test_random.get()):
            messagebox.showwarning(
                self.app.i18n.get("warning", "Предупреждение"),
                self.app.i18n.get("select_pattern", "Выберите хотя бы один паттерн тестирования")
            )
            return

        if self.test_mode.get() == 'full':
            if not messagebox.askyesno(
                    self.app.i18n.get("confirm", "Подтверждение"),
                    "⚠️ ПОЛНЫЙ РЕЖИМ: будут проверены ВСЕ сектора диска, включая системные области. "
                    "Это может привести к потере данных и повреждению файловой системы!\n\nПродолжить?",
                    icon='warning'
            ):
                return

        if not self._confirm_test_start():
            return

        params = {
            'passes': self.passes_var.get(),
            'test_ones': self.test_ones.get(),
            'test_zeros': self.test_zeros.get(),
            'test_random': self.test_random.get(),
            'test_verify': self.verify_read.get(),
            'auto_format': self.auto_format.get(),
            'mode': self.test_mode.get(),
            'filesystem': 'FAT32',
            'chunk_size_mb': self.chunk_size_var.get(),
            'adaptive_chunk': self.adaptive_chunk_var.get(),
            'parallel_testing': self.parallel_test_var.get(),
            'num_threads': self.threads_var.get() if self.parallel_test_var.get() else 1,
            'quick_test': self.quick_test_var.get()
        }

        i = self.app.i18n
        self.log_viewer.log("=" * 50, "info")
        self.log_viewer.log(i.get("log_test_start", "🚀 ЗАПУСК ТЕСТА С ПАРАМЕТРАМИ:"), "system")
        mode_text = i.get("mode_full" if params['mode'] == 'full' else "mode_free")
        self.log_viewer.log(i.get("log_mode", "📊 Режим: {}").format(mode_text), "info")
        self.log_viewer.log(i.get("log_passes", "🔄 Проходов: {}").format(params['passes']), "info")
        self.log_viewer.log(i.get("log_chunk_size", "📦 Размер блока: {} MB").format(params['chunk_size_mb']), "info")
        yes_no = i.get("yes") if params['adaptive_chunk'] else i.get("no")
        self.log_viewer.log(i.get("log_adaptive", "🔄 Адаптивный блок: {}").format(yes_no), "info")
        yes_no = i.get("yes") if params['parallel_testing'] else i.get("no")
        self.log_viewer.log(i.get("log_parallel", "⚡ Параллельное тестирование: {}").format(yes_no), "info")
        if params['parallel_testing']:
            self.log_viewer.log(i.get("log_threads", "🧵 Потоков: {}").format(params['num_threads']), "info")
        yes_no = i.get("yes") if params['quick_test'] else i.get("no")
        self.log_viewer.log(i.get("log_quick", "⚡ Быстрый тест: {}").format(yes_no), "info")
        self.log_viewer.log("=" * 50, "info")

        self.chart_widget.clear()
        self.progress_panel.reset()
        self.log_viewer.clear()

        self.app.disk_tester.start_test(self.current_drive['path'], params)

        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text=i.get("pause", "⏸ Пауза"))
        self.stop_btn.config(state=tk.NORMAL)

        self.log_viewer.log(
            i.get(("test_started").format(self.current_drive['path']), "info")
        )
        self.app.main_window.update_status(i.get("testing", "Тестирование..."))

    def _confirm_test_start(self):
        i = self.app.i18n
        mode_text = i.get("mode_full") if self.test_mode.get() == 'full' else i.get("mode_free")
        patterns = []
        if self.test_ones.get():
            patterns.append(i.get("pattern_ones", "Единицы"))
        if self.test_zeros.get():
            patterns.append(i.get("pattern_zeros", "Нули"))
        if self.test_random.get():
            patterns.append(i.get("pattern_random", "Случайные"))
        patterns_str = ", ".join(patterns)

        warning_text = i.get(
            "confirm_test",
            f"⚠️ ВНИМАНИЕ! Данные на диске {self.current_drive['path']} могут быть уничтожены!\n\n"
            f"Режим: {mode_text}\n"
            f"Проходов: {self.passes_var.get()}\n"
            f"Паттерны: {patterns_str}\n"
            f"Размер блока: {self.chunk_size_var.get()} MB\n"
            f"Адаптивный блок: {'Да' if self.adaptive_chunk_var.get() else 'Нет'}\n"
            f"Параллельное тестирование: {'Да' if self.parallel_test_var.get() else 'Нет'}\n"
            f"Быстрый тест: {'Да' if self.quick_test_var.get() else 'Нет'}\n"
            f"Проверка чтения: {'Да' if self.verify_read.get() else 'Нет'}\n"
            f"Форматирование после теста: {'Да' if self.auto_format.get() else 'Нет'}\n\n"
            f"Вы уверены, что хотите продолжить?"
        )

        return messagebox.askyesno(
            i.get("confirm", "Подтверждение"),
            warning_text,
            icon='warning'
        )

    def pause_test(self):
        paused = self.app.disk_tester.pause()
        i = self.app.i18n

        if paused is not None:
            if paused:
                self.pause_btn.config(text=i.get("resume", "▶ Продолжить"))
                self.log_viewer.log(i.get("test_paused", "Тест приостановлен"), "warning")
            else:
                self.pause_btn.config(text=i.get("pause", "⏸ Пауза"))
                self.log_viewer.log(i.get("test_resumed", "Тест продолжен"), "info")

    def stop_test(self):
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

                        stats = self.app.disk_tester.get_statistics()
                        self.progress_panel.update_time(stats.get('elapsed_time', '00:00:00'))

                    elif msg_type == "bad_sector" and len(msg) >= 4:
                        self.log_viewer.log(
                            f"{self.app.i18n.get('bad_sector', 'Битый сектор')}: {msg[1]}",
                            "error"
                        )
                        self.progress_panel.add_bad_sector()

                    elif msg_type == "complete" and len(msg) >= 2:
                        self._on_test_complete(msg[1])

                    elif msg_type == "error" and len(msg) >= 2:
                        self._on_test_error(msg[1])

                    msg = self.app.disk_tester.get_message()

                if self.app.disk_tester.is_running():
                    if hasattr(self.app.disk_tester, 'paused') and self.app.disk_tester.paused:
                        self.pause_btn.config(text=self.app.i18n.get("resume", "▶ Продолжить"))
                    else:
                        self.pause_btn.config(text=self.app.i18n.get("pause", "⏸ Пауза"))
        except Exception as e:
            self.logger.error(f"Ошибка в process_messages: {e}")

        self.after(100, self.process_messages)

    def _on_test_complete(self, message):
        stats = self.app.disk_tester.get_statistics()

        self.log_viewer.log(message, "success")

        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        self.progress_panel.update_progress(100)
        self.app.main_window.update_status(self.app.i18n.get("ready", "Готов"))

        self.app.main_window.results_tab.update_results(stats)
        self.app.main_window.notebook.select(3)

    def _on_test_error(self, error_msg):
        self.log_viewer.log(f"{self.app.i18n.get('error', 'Ошибка')}: {error_msg}", "error")

        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        self.app.main_window.update_status(self.app.i18n.get("error", "Ошибка"), "error")

    def run_benchmark(self):
        if not self.current_drive:
            return

        drive_size = self.current_drive.get('total_bytes', 0) / (1024**3)

        if drive_size < 16:
            optimal_chunk = 16
        elif drive_size < 64:
            optimal_chunk = 32
        elif drive_size < 256:
            optimal_chunk = 64
        else:
            optimal_chunk = 128

        self.passes_var.set(1)
        self.test_ones.set(True)
        self.test_zeros.set(True)
        self.test_random.set(True)
        self.verify_read.set(True)
        self.auto_format.set(False)
        self.test_mode.set('free')
        self.chunk_size_var.set(optimal_chunk)
        self.adaptive_chunk_var.set(True)
        self.parallel_test_var.set(True)
        self.threads_var.set(min(8, os.cpu_count() or 4))
        self.quick_test_var.set(False)

        self.start_test()

    def update_language(self):
        i = self.app.i18n

        self.settings_frame.config(text=i.get("test_settings", "Настройки тестирования"))
        self.perf_frame.config(text=i.get("performance_settings", "⚡ Настройки производительности"))
        self.chart_frame.config(text=i.get("speed_chart", "График скорости"))
        self.log_frame.config(text=i.get("event_log", "Журнал событий"))

        self.passes_label.config(text=i.get("passes", "Проходы:"))
        self.mode_label.config(text=i.get("test_mode", "Режим:"))
        self.mode_free_rb.config(text=i.get("mode_free", "Только свободное место"))
        self.mode_full_rb.config(text=i.get("mode_full", "Полное тестирование (все сектора)"))
        self.patterns_label.config(text=i.get("patterns", "Паттерны:"))
        self.ones_cb.config(text=i.get("pattern_ones", "Единицы (0xFF)"))
        self.zeros_cb.config(text=i.get("pattern_zeros", "Нули (0x00)"))
        self.random_cb.config(text=i.get("pattern_random", "Случайные"))
        self.select_all_btn.config(text=i.get("select_all", "Все"))
        self.verify_cb.config(text=i.get("verify_read", "Проверка чтения"))
        self.auto_format_cb.config(text=i.get("auto_format", "Форматировать после теста"))

        self.chunk_label.config(text=i.get("chunk_size", "Размер блока (MB):"))
        self.adaptive_chunk_cb.config(text=i.get("adaptive_chunk", "🔄 Адаптивный размер блока"))
        self.parallel_test_cb.config(text=i.get("parallel_test", "⚡ Параллельное тестирование"))
        self.threads_label.config(text=i.get("threads", "Потоки:"))
        self.quick_test_cb.config(text=i.get("quick_test", "⚡ Быстрый тест"))

        self.start_btn.config(text=i.get("start_test", "🚀 Начать тест"))
        if self.pause_btn['state'] == tk.NORMAL:
            if hasattr(self.app.disk_tester, 'paused') and self.app.disk_tester.paused:
                self.pause_btn.config(text=i.get("resume", "▶ Продолжить"))
            else:
                self.pause_btn.config(text=i.get("pause", "⏸ Пауза"))
        else:
            self.pause_btn.config(text=i.get("pause", "⏸ Пауза"))
        self.stop_btn.config(text=i.get("stop", "⏹ Стоп"))

        self.progress_panel.update_language()
        self.chart_widget.update_language()

    def update_theme(self):
        self.chart_widget.update_theme()
        self.progress_panel.update_theme()
        self.log_viewer.update_theme()