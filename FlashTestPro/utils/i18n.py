"""
Модуль интернационализации
"""
import os
import json
from typing import Dict, Any
from utils.logger import get_logger

class I18n:
    """Класс для работы с переводами"""
    
    def __init__(self, language: str = "ru"):
        self.logger = get_logger(__name__)
        self.language = language
        self.translations: Dict[str, Any] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Загрузка переводов из файлов"""
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        
        # Загрузка русского как базового
        ru_file = os.path.join(locales_dir, "ru.json")
        if os.path.exists(ru_file):
            with open(ru_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        
        # Загрузка выбранного языка
        lang_file = os.path.join(locales_dir, f"{self.language}.json")
        if os.path.exists(lang_file) and self.language != "ru":
            with open(lang_file, 'r', encoding='utf-8') as f:
                user_translations = json.load(f)
                self.translations.update(user_translations)
    
    def get(self, key: str, default: str = "") -> str:
        """Получение перевода по ключу"""
        if key in self.translations:
            return self.translations[key]
        return default or key
    
    def set_language(self, language: str):
        """Смена языка"""
        self.language = language
        self._load_translations()