"""
Вкладка форматирования дисков
"""
import tkinter as tk
from tkinter import ttk, messagebox

class FormatTab(ttk.Frame):
    """Вкладка форматирования"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_drive = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настройки форматирования
        settings_frame = ttk.LabelFrame(
            main_frame,
            text=self.app.i18n.get("format_settings", "Настройки форматирования")
        )
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Файловая система
        fs_frame = ttk.Frame(settings_frame)
        fs_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(fs_frame, text=self.app.i18n.get("filesystem_label", "Файловая система:")).pack(side=tk.LEFT)
        
        self.fs_var = tk.StringVar(value="FAT32")
        fs_combo = ttk.Combobox(
            fs_frame,
            textvariable=self.fs_var,
            values=["FAT32", "exFAT", "NTFS", "EXT4"],
            state="readonly",
            width=15
        )
        fs_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Метка тома
        label_frame = ttk.Frame(settings_frame)
        label_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(label_frame, text=self.app.i18n.get("volume_label", "Метка тома:")).pack(side=tk.LEFT)
        
        self.label_var = tk.StringVar()
        label_entry = ttk.Entry(label_frame, textvariable=self.label_var, width=20)
        label_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Быстрое форматирование
        self.quick_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text=self.app.i18n.get("quick_format", "Быстрое форматирование"),
            variable=self.quick_var
        ).pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Кнопка форматирования
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.format_btn = ttk.Button(
            button_frame,
            text=self.app.i18n.get("format_drive", "💾 Форматировать диск"),
            command=self.format_disk,
            width=25
        )
        self.format_btn.pack()
        
        # Информация
        info_frame = ttk.LabelFrame(main_frame, text=self.app.i18n.get("info", "Информация"))
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
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
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
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
        
        # Запуск форматирования
        success, message = self.app.disk_formatter.format_disk(
            self.current_drive['path'],
            self.fs_var.get(),
            self.quick_var.get(),
            self.label_var.get()
        )
        
        if success:
            messagebox.showinfo(
                self.app.i18n.get("success", "Успех"),
                message
            )
            self.app.refresh_drives()
        else:
            messagebox.showerror(
                self.app.i18n.get("error", "Ошибка"),
                message
            )
    
    def update_language(self):
        """Обновление языка"""
        # TODO: Обновить тексты
        pass
    
    def update_theme(self):
        """Обновление темы"""
        pass