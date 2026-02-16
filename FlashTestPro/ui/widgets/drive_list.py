"""
Виджет списка дисков
"""
import tkinter as tk
from tkinter import ttk

class DriveListWidget(ttk.Frame):
    """Виджет для отображения списка дисков"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.drives = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        # Создаем Treeview
        columns = ("drive", "type", "size", "fs")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=10,
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("drive", text=self.app.i18n.get("drive", "Диск"))
        self.tree.heading("type", text=self.app.i18n.get("type", "Тип"))
        self.tree.heading("size", text=self.app.i18n.get("size", "Размер"))
        self.tree.heading("fs", text=self.app.i18n.get("filesystem", "ФС"))
        
        self.tree.column("drive", width=100)
        self.tree.column("type", width=100)
        self.tree.column("size", width=80)
        self.tree.column("fs", width=70)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка событий
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Контекстное меню
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Обновить", command=self._refresh)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Свойства", command=self._show_properties)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Показать контекстное меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _refresh(self):
        """Обновление списка"""
        self.app.refresh_drives()
    
    def _show_properties(self):
        """Показать свойства диска"""
        selected = self.get_selected_drive()
        if selected:
            props = f"""
Диск: {selected['path']}
Тип: {selected['type']}
Файловая система: {selected['fs']}
Размер: {selected['total_size']}
Использовано: {selected['used']} ({selected['percent_used']}%)
Свободно: {selected['free']}
Метка: {selected['label'] or 'Нет'}
            """
            tk.messagebox.showinfo("Свойства диска", props)
    
    def _on_select(self, event):
        """Обработка выбора диска"""
        selected = self.get_selected_drive()
        if selected:
            self.app.main_window.update_selected_drive(selected)
    
    def update_drives(self, drives):
        """Обновление списка дисков"""
        self.drives = drives
        
        # Очистка текущего списка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Добавление новых дисков
        for drive in drives:
            values = (
                drive["path"],
                drive["type"],
                drive["total_size"],
                drive["fs"]
            )
            
            item_id = self.tree.insert("", tk.END, values=values)
            
            # Выделение системных дисков красным
            if drive.get("is_system", False):
                self.tree.tag_configure("system", background="#550000")
                self.tree.item(item_id, tags=("system",))
    
    def get_selected_drive(self):
        """Получение выбранного диска"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        if not item or not self.drives:
            return None
        
        # Находим соответствующий диск
        values = item["values"]
        for drive in self.drives:
            if drive["path"] == values[0]:
                return drive
        
        return None