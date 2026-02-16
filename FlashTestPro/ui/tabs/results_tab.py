"""
Вкладка отображения результатов тестирования
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime

class ResultsTab(ttk.Frame):
    """Вкладка результатов"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None
        self.current_results = None
        
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
            text=self.app.i18n.get("export_report", "📄 Экспорт отчета"),
            command=self.export_report,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
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
        
        stats = [
            ("drive", "Диск:"),
            ("total_size", "Общий размер:"),
            ("tested", "Протестировано:"),
            ("avg_speed", "Средняя скорость:"),
            ("max_speed", "Макс. скорость:"),
            ("min_speed", "Мин. скорость:"),
            ("test_time", "Время теста:"),
            ("bad_sectors", "Битые сектора:"),
            ("passes", "Проходов выполнено:"),
            ("status", "Статус:")
        ]
        
        for i, (key, label) in enumerate(stats):
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(row_frame, text=label, font=("Segoe UI", 10, "bold"), width=20).pack(side=tk.LEFT)
            
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
        self.clear_btn.config(state=tk.NORMAL)
    
    def export_report(self):
        """Экспорт отчета в файл"""
        if not self.current_results:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
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
            self.clear_btn.config(state=tk.DISABLED)
    
    def update_language(self):
        """Обновление языка"""
        # TODO: Обновить заголовки
        pass
    
    def update_theme(self):
        """Обновление темы"""
        pass