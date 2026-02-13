# [file name]: test_locales.py
# [file content begin]
"""
Tests for localization
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import locales

class TestLocales(unittest.TestCase):
    """Tests for locales module"""
    
    def test_get_translation(self):
        """Test getting translations"""
        # Russian
        self.assertEqual(locales.get_translation("ru", "app_title"), "SD Card Tester Pro")
        self.assertEqual(locales.get_translation("ru", "start_test"), "🚀 НАЧАТЬ ТЕСТ")
        
        # English
        self.assertEqual(locales.get_translation("en", "app_title"), "SD Card Tester Pro")
        self.assertEqual(locales.get_translation("en", "start_test"), "🚀 START TEST")
        
        # Chinese
        self.assertEqual(locales.get_translation("zh", "app_title"), "SD卡测试专业版")
        self.assertEqual(locales.get_translation("zh", "start_test"), "🚀 开始测试")
    
    def test_get_translation_with_format(self):
        """Test translations with formatting"""
        # Test with arguments
        result = locales.get_translation("en", "selected_drive", 
                                        "C:", "Fixed", "500 GB", "NTFS")
        self.assertIn("C:", result)
        self.assertIn("Fixed", result)
        self.assertIn("500 GB", result)
        self.assertIn("NTFS", result)
    
    def test_get_available_languages(self):
        """Test getting available languages"""
        languages = locales.get_available_languages()
        self.assertIn("ru", languages)
        self.assertIn("en", languages)
        self.assertIn("zh", languages)
        self.assertEqual(len(languages), 3)
    
    def test_default_language(self):
        """Test fallback to default language"""
        # Test non-existent language
        result = locales.get_translation("fr", "start_test")  # French doesn't exist
        self.assertEqual(result, "start_test")  # Should return key
        
        # Test non-existent key
        result = locales.get_translation("en", "non_existent_key")
        self.assertEqual(result, "non_existent_key")

if __name__ == '__main__':
    unittest.main()
# [file content end]