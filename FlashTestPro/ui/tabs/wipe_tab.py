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
        
        self.create_widgets()
        
        # Запуск обработки сообщений
        self.after(100, self.process_messages)
    
    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настройки затирания
        settings_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("wipe_settings", "Настройки затирания")
        )
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Метод затирания
        method_frame = ttk.Frame(settings_frame)
        method_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(method_frame, text=self.app.i18n.get("wipe_method", "Метод затирания:")).pack(side=tk.LEFT)
        
        self.method_var = tk.StringVar(value="dod")
        method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.method_var,
            values=[
                "simple",
                "dod",
                "gutmann"
            ],
            state="readonly",
            width=30
        )
        method_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Количество проходов (для пользовательского метода)
        passes_frame = ttk.Frame(settings_frame)
        passes_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(passes_frame, text=self.app.i18n.get("wipe_passes", "Количество проходов:")).pack(side=tk.LEFT)
        
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
        ttk.Checkbutton(
            settings_frame,
            text=self.app.i18n.get("verify_wipe", "Проверить после затирания"),
            variable=self.verify_var
        ).pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Кнопки управления
        buttons_frame = ttk.Frame(settings_frame)
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
        progress_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("progress", "Прогресс"))
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(pady=(0, 10))
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("log", "Лог"))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
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
            self.method_var.get(),
            self.passes_var.get()
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
                    self._log(f"Ошибка: {msg[1]}", is_error=True)
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
        """Обновление языка"""
        pass
    
    def update_theme(self):
        """Обновление темы"""
        pass