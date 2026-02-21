"""
Вкладка отображения результатов тестирования
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import io
import base64
from datetime import datetime

import matplotlib.pyplot as plt

class ResultsTab(ttk.Frame):
    """Вкладка результатов"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None
        self.current_results = None
        self.summary_left_labels = []  # для хранения левых меток общей статистики

        self.create_widgets()

    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        self.export_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("export_report", "📄 Экспорт JSON"),
            command=self.export_report,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.html_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("export_html", "🌐 Экспорт HTML"),
            command=self.export_html,
            state=tk.DISABLED
        )
        self.html_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            buttons_frame,
            text=self.app.i18n.get("clear", "🗑 Очистить"),
            command=self.clear_results,
            state=tk.DISABLED
        )
        self.clear_btn.pack(side=tk.LEFT)

        # Область результатов
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка с общей статистикой
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text=self.app.i18n.get("summary", "Общая статистика"))
        self._create_summary_tab()

        # Вкладка с битыми секторами
        self.bad_sectors_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.bad_sectors_tab, text=self.app.i18n.get("bad_sectors", "Битые сектора"))
        self._create_bad_sectors_tab()

        # Вкладка с детальным отчетом
        self.detail_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.detail_tab, text=self.app.i18n.get("detailed", "Детальный отчет"))
        self._create_detail_tab()

    def _create_summary_tab(self):
        """Создание вкладки с общей статистикой"""
        frame = ttk.Frame(self.summary_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем метки для статистики
        self.summary_labels = {}
        self.summary_left_labels = []  # список для хранения левых меток

        # Ключи локализации для левых меток
        stats_keys = [
            ("drive", "drive"),
            ("mode", "test_mode"),
            ("total_size", "total_size"),
            ("tested", "tested"),
            ("avg_speed", "avg_speed"),
            ("max_speed", "max_speed"),
            ("min_speed", "min_speed"),
            ("test_time", "test_time"),
            ("bad_sectors", "bad_sectors"),
            ("passes", "passes"),
            ("status", "status")
        ]

        for key, loc_key in stats_keys:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=5)

            # Левая метка (локализованная)
            left_text = self.app.i18n.get(loc_key, loc_key).rstrip(':') + ':'
            left_label = ttk.Label(
                row_frame,
                text=left_text,
                font=("Segoe UI", 10, "bold"),
                width=20
            )
            left_label.pack(side=tk.LEFT)
            self.summary_left_labels.append((left_label, loc_key))  # сохраняем для обновления

            # Правая метка (значение)
            self.summary_labels[key] = ttk.Label(row_frame, text="---", font=("Segoe UI", 10))
            self.summary_labels[key].pack(side=tk.LEFT, padx=(10, 0))

    def _create_bad_sectors_tab(self):
        """Создание вкладки с битыми секторами"""
        frame = ttk.Frame(self.bad_sectors_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Таблица битых секторов
        columns = ("sector", "error_type", "time", "attempts")
        self.bad_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)

        self.bad_tree.heading("sector", text=self.app.i18n.get("sector", "Сектор"))
        self.bad_tree.heading("error_type", text=self.app.i18n.get("error_type", "Тип ошибки"))
        self.bad_tree.heading("time", text=self.app.i18n.get("time", "Время"))
        self.bad_tree.heading("attempts", text=self.app.i18n.get("attempts", "Попытки"))

        self.bad_tree.column("sector", width=150)
        self.bad_tree.column("error_type", width=200)
        self.bad_tree.column("time", width=100)
        self.bad_tree.column("attempts", width=80)

        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.bad_tree.yview)
        self.bad_tree.configure(yscrollcommand=scrollbar.set)

        self.bad_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_detail_tab(self):
        """Создание вкладки с детальным отчетом"""
        frame = ttk.Frame(self.detail_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.detail_text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 9))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=scrollbar.set)

        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_drive_selected(self, drive_info):
        """Обработка выбора диска"""
        self.current_drive = drive_info

    def update_results(self, stats):
        """Обновление результатов"""
        self.current_results = stats

        # Обновление общей статистики
        if stats:
            self.summary_labels["drive"].config(text=stats.get('drive_path', '---'))
            mode = stats.get('mode', 'free')
            mode_text = self.app.i18n.get("mode_full" if mode == 'full' else "mode_free", mode)
            self.summary_labels["mode"].config(text=mode_text)
            self.summary_labels["total_size"].config(text=f"{stats.get('total_size', 0):.2f} GB")
            self.summary_labels["tested"].config(text=f"{stats.get('tested', 0):.2f} GB")
            self.summary_labels["avg_speed"].config(text=f"{stats.get('avg_speed', 0):.1f} MB/s")
            self.summary_labels["max_speed"].config(text=f"{stats.get('max_speed', 0):.1f} MB/s")
            self.summary_labels["min_speed"].config(text=f"{stats.get('min_speed', 0):.1f} MB/s")
            self.summary_labels["test_time"].config(text=stats.get('elapsed_time', '00:00:00'))
            self.summary_labels["bad_sectors"].config(text=str(stats.get('bad_sectors_count', 0)))
            self.summary_labels["passes"].config(text=f"{stats.get('current_pass', 0)}/{stats.get('total_passes', 1)}")
            self.summary_labels["status"].config(text=self.app.i18n.get("completed", "Завершено"))

        # Обновление таблицы битых секторов
        for item in self.bad_tree.get_children():
            self.bad_tree.delete(item)

        if stats and 'bad_sectors' in stats:
            for sector in stats['bad_sectors']:
                self.bad_tree.insert("", tk.END, values=(
                    sector.get('sector', ''),
                    sector.get('error_type', ''),
                    sector.get('time', ''),
                    sector.get('attempts', 1)
                ))

        # Обновление детального отчета
        self.detail_text.delete(1.0, tk.END)
        if stats:
            self.detail_text.insert(tk.END, json.dumps(stats, indent=2, default=str))

        # Активация кнопок
        self.export_btn.config(state=tk.NORMAL)
        self.html_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)

    def export_report(self):
        """Экспорт отчета в JSON"""
        if not self.current_results:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialfile=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, default=str)

                messagebox.showinfo(
                    self.app.i18n.get("success", "Успех"),
                    self.app.i18n.get("report_saved", f"Отчет сохранен в {filename}")
                )
            except Exception as e:
                messagebox.showerror(
                    self.app.i18n.get("error", "Ошибка"),
                    str(e)
                )

    def export_html(self):
        """Экспорт отчета в HTML с графиком"""
        if not self.current_results:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML files", "*.html"),
                ("All files", "*.*")
            ],
            initialfile=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        if filename:
            try:
                html_content = self._generate_html_report()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                messagebox.showinfo(
                    self.app.i18n.get("success", "Успех"),
                    self.app.i18n.get("report_saved", f"Отчет сохранен в {filename}")
                )
            except Exception as e:
                messagebox.showerror(
                    self.app.i18n.get("error", "Ошибка"),
                    str(e)
                )

    def _generate_html_report(self):
        """Генерация HTML-отчёта"""
        stats = self.current_results
        if not stats:
            return "<html><body>Нет данных</body></html>"

        # Преобразуем режим
        mode = stats.get('mode', 'free')
        mode_display = self.app.i18n.get("mode_full" if mode == 'full' else "mode_free", mode)

        # Создаём график скорости
        times = stats.get('times', [])
        speeds = stats.get('speeds', [])
        img_base64 = ""
        if times and speeds:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(times, speeds, 'b-', linewidth=1)
            ax.set_xlabel(self.app.i18n.get("time_sec", "Время (с)"))
            ax.set_ylabel(self.app.i18n.get("speed_mbs", "Скорость (MB/s)"))
            ax.set_title(self.app.i18n.get("speed_chart", "График скорости"))
            ax.grid(True)
            # Сохраняем в буфер
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)

        # Таблица битых секторов
        bad_rows = ""
        for bs in stats.get('bad_sectors', []):
            bad_rows += f"<tr><td>{bs.get('sector')}</td><td>{bs.get('error_type')}</td><td>{bs.get('time')}</td><td>{bs.get('attempts')}</td></tr>"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.app.i18n.get("test_report_title", "Отчёт FlashTest Pro")}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{self.app.i18n.get("test_report", "Отчёт о тестировании FlashTest Pro")}</h1>
    <div class="summary">
        <p><strong>{self.app.i18n.get("drive", "Диск")}:</strong> {stats.get('drive_path', '')}</p>
        <p><strong>{self.app.i18n.get("mode", "Режим")}:</strong> {mode_display}</p>
        <p><strong>{self.app.i18n.get("passes", "Проходов")}:</strong> {stats.get('current_pass', 0)} / {stats.get('total_passes', 1)}</p>
        <p><strong>{self.app.i18n.get("total_size", "Общий размер")}:</strong> {stats.get('total_size', 0):.2f} GB</p>
        <p><strong>{self.app.i18n.get("tested", "Протестировано")}:</strong> {stats.get('tested', 0):.2f} GB</p>
        <p><strong>{self.app.i18n.get("avg_speed", "Средняя скорость")}:</strong> {stats.get('avg_speed', 0):.1f} MB/s</p>
        <p><strong>{self.app.i18n.get("max_speed", "Макс. скорость")}:</strong> {stats.get('max_speed', 0):.1f} MB/s</p>
        <p><strong>{self.app.i18n.get("min_speed", "Мин. скорость")}:</strong> {stats.get('min_speed', 0):.1f} MB/s</p>
        <p><strong>{self.app.i18n.get("test_time", "Время теста")}:</strong> {stats.get('elapsed_time', '00:00:00')}</p>
        <p><strong>{self.app.i18n.get("bad_sectors", "Битые сектора")}:</strong> {stats.get('bad_sectors_count', 0)}</p>
    </div>
    
    <h2>{self.app.i18n.get("speed_chart", "График скорости")}</h2>
    <div class="chart">
        <img src="data:image/png;base64,{img_base64}" alt="{self.app.i18n.get("speed_chart", "График скорости")}" style="max-width:100%;">
    </div>
    
    <h2>{self.app.i18n.get("bad_sectors", "Битые сектора")}</h2>
    <table>
        <tr>
            <th>{self.app.i18n.get("sector", "Сектор")}</th>
            <th>{self.app.i18n.get("error_type", "Тип ошибки")}</th>
            <th>{self.app.i18n.get("time", "Время")}</th>
            <th>{self.app.i18n.get("attempts", "Попытки")}</th>
        </tr>
        {bad_rows}
    </table>
    
    <p><em>{self.app.i18n.get("generated", "Сгенерировано")} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
</body>
</html>
"""
        return html

    def clear_results(self):
        """Очистка результатов"""
        if messagebox.askyesno(
                self.app.i18n.get("confirm", "Подтверждение"),
                self.app.i18n.get("confirm_clear", "Очистить результаты?")
        ):
            self.current_results = None

            # Очистка меток
            for key in self.summary_labels:
                self.summary_labels[key].config(text="---")

            # Очистка таблицы
            for item in self.bad_tree.get_children():
                self.bad_tree.delete(item)

            # Очистка текста
            self.detail_text.delete(1.0, tk.END)

            # Деактивация кнопок
            self.export_btn.config(state=tk.DISABLED)
            self.html_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)

    def update_language(self):
        """Обновление языка интерфейса"""
        # Обновление текста кнопок
        self.export_btn.config(text=self.app.i18n.get("export_report", "📄 Экспорт JSON"))
        self.html_btn.config(text=self.app.i18n.get("export_html", "🌐 Экспорт HTML"))
        self.clear_btn.config(text=self.app.i18n.get("clear", "🗑 Очистить"))

        # Обновление заголовков вкладок
        self.notebook.tab(0, text=self.app.i18n.get("summary", "Общая статистика"))
        self.notebook.tab(1, text=self.app.i18n.get("bad_sectors", "Битые сектора"))
        self.notebook.tab(2, text=self.app.i18n.get("detailed", "Детальный отчет"))

        # Обновление заголовков столбцов таблицы
        self.bad_tree.heading("sector", text=self.app.i18n.get("sector", "Сектор"))
        self.bad_tree.heading("error_type", text=self.app.i18n.get("error_type", "Тип ошибки"))
        self.bad_tree.heading("time", text=self.app.i18n.get("time", "Время"))
        self.bad_tree.heading("attempts", text=self.app.i18n.get("attempts", "Попытки"))

        # Обновление левых меток в общей статистике
        for label_widget, loc_key in self.summary_left_labels:
            new_text = self.app.i18n.get(loc_key, loc_key).rstrip(':') + ':'
            label_widget.config(text=new_text)

        # Обновление правого значения режима, если есть результаты
        if self.current_results:
            mode = self.current_results.get('mode', 'free')
            mode_text = self.app.i18n.get("mode_full" if mode == 'full' else "mode_free", mode)
            self.summary_labels["mode"].config(text=mode_text)

    def update_theme(self):
        """Обновление темы оформления"""
        colors = self.app.theme_manager.colors

        # Применяем цвета к текстовому виджету детального отчёта
        self.detail_text.config(
            bg=colors.get("entry_bg", "#ffffff"),
            fg=colors.get("entry_fg", "#000000")
        )