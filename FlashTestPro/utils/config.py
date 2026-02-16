"""
Модуль для работы с конфигурацией
"""
import os
import json
from typing import Dict, Any
from utils.logger import get_logger

class ConfigManager:
    """Менеджер конфигурации"""
    
    DEFAULT_CONFIG = {
        "app": {
            "name": "FlashTest Pro",
            "version": "1.0.0",
            "auto_save_logs": True,
            "log_retention_days": 30,
            "check_updates": True
        },
        "ui": {
            "theme": "dark",
            "language": "ru",
            "window_width": 900,
            "window_height": 700,
            "min_width": 800,
            "min_height": 600,
            "show_tooltips": True
        },
        "testing": {
            "default_passes": 1,
            "chunk_size_mb": 32,
            "verify_read": True,
            "patterns": ["ones", "zeros", "random"],
            "bad_sector_threshold": 5,
            "speed_chart_points": 100
        },
        "formatting": {
            "default_filesystem": "FAT32",
            "quick_format_default": True,
            "allow_system_format": False
        },
        "wiping": {
            "default_passes": 3,
            "verify_after_wipe": True,
            "methods": ["simple", "dod", "gutmann"],
            "default_method": "dod"
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = get_logger(__name__)
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
    
    def load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_configs(self.config, user_config)
                self.logger.info(f"Конфигурация загружена из {self.config_path}")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфигурации: {e}")
        else:
            self.logger.info("Файл конфигурации не найден, используются настройки по умолчанию")
            self.save_config()
        
        return self.config
    
    def save_config(self) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Конфигурация сохранена в {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def _merge_configs(self, default: Dict, user: Dict):
        """Рекурсивное объединение конфигураций"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def update_config(self, section: str, key: str, value: Any):
        """Обновление конкретного параметра конфигурации"""
        if section in self.config:
            self.config[section][key] = value
            self.save_config()
        else:
            self.logger.warning(f"Секция {section} не найдена в конфигурации")
    
    def get_config(self) -> Dict[str, Any]:
        """Получение текущей конфигурации"""
        return self.config