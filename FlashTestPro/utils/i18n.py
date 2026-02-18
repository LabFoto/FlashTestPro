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
                # Рекурсивное обновление словаря
                self._deep_update(self.translations, user_translations)
        
        self.logger.debug(f"Загружены переводы для языка: {self.language}")
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Рекурсивное обновление словаря"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key: str, default: str = "") -> str:
        """Получение перевода по ключу"""
        if key in self.translations:
            return self.translations[key]
        
        # Если ключ не найден, логируем и возвращаем default или ключ
        if default:
            return default
        return key
    
    def set_language(self, language: str):
        """Смена языка"""
        if language != self.language:
            self.language = language
            self._load_translations()
            self.logger.info(f"Язык изменен на: {language}")