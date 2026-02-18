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
        
        # Применение темы к списку
        self._apply_theme()
    
    def _apply_theme(self):
        """Применение темы к списку дисков через стили"""
        colors = self.app.theme_manager.colors
        
        # Получаем кастомный стиль для Treeview
        custom_style = self.app.theme_manager.get_treeview_style()
        
        # Применяем стиль к дереву
        self.tree.configure(style=custom_style)
        
        # Настройка тегов для цветов дисков
        self._configure_tags()
    
    def _configure_tags(self):
        """Настройка тегов для разных типов дисков"""
        colors = self.app.theme_manager.colors
        
        # Тег для системных дисков (красный)
        self.tree.tag_configure(
            "system_disk",
            foreground=colors["system_disk_fg"]
        )
        
        # Тег для выделенного системного диска (красный на зеленом фоне)
        self.tree.tag_configure(
            "system_disk_selected",
            foreground=colors["system_disk_fg"],
            background=colors["tree_select_bg"]
        )
        
        # Тег для съемных дисков (голубой в темной теме)
        if self.app.theme_manager.current_theme == "dark":
            self.tree.tag_configure(
                "removable_disk",
                foreground=colors["removable_disk_fg"]
            )
            self.tree.tag_configure(
                "removable_disk_selected",
                foreground=colors["removable_disk_fg"],
                background=colors["tree_select_bg"]
            )
        
        # Тег для обычных дисков
        self.tree.tag_configure(
            "normal_disk",
            foreground=colors["normal_disk_fg"]
        )
        self.tree.tag_configure(
            "normal_disk_selected",
            foreground=colors["normal_disk_fg"],
            background=colors["tree_select_bg"]
        )
    
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
            
            # Обновляем теги для правильного отображения выделения
            self._update_selection_tags()
    
    def _update_selection_tags(self):
        """Обновление тегов для правильного отображения выделения"""
        # Получаем все элементы
        for item in self.tree.get_children():
            current_tags = self.tree.item(item, "tags")
            if current_tags:
                # Определяем базовый тег (без _selected)
                if isinstance(current_tags, tuple):
                    base_tag = current_tags[0].replace("_selected", "")
                else:
                    base_tag = current_tags.replace("_selected", "")
                
                # Проверяем, выделен ли элемент
                if item in self.tree.selection():
                    # Если выделен, добавляем _selected
                    self.tree.item(item, tags=(f"{base_tag}_selected",))
                else:
                    # Если не выделен, используем базовый тег
                    self.tree.item(item, tags=(base_tag,))
    
    def update_drives(self, drives):
        """Обновление списка дисков"""
        self.drives = drives
        
        # Очистка текущего списка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Пересоздаем теги (на случай смены темы)
        self._configure_tags()
        
        # Добавление новых дисков
        for drive in drives:
            values = (
                drive["path"],
                drive["type"],
                drive["total_size"],
                drive["fs"]
            )
            
            item_id = self.tree.insert("", tk.END, values=values)
            
            # Применение тегов в зависимости от типа диска
            if drive.get("is_system", False):
                # Системный диск
                self.tree.item(item_id, tags=("system_disk",))
            elif drive.get("is_removable", False) and self.app.theme_manager.current_theme == "dark":
                # Съемный диск (только в темной теме)
                self.tree.item(item_id, tags=("removable_disk",))
            else:
                # Обычный диск
                self.tree.item(item_id, tags=("normal_disk",))
        
        # Обновляем выделение
        self._update_selection_tags()
    
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
    
    def update_theme(self):
        """Обновление темы"""
        self._apply_theme()
        self.update_drives(self.drives)