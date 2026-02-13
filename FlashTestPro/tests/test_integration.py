"""
Integration tests for SD Card Tester Pro
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_save_load_cycle(self):
        """Тест цикла сохранения и загрузки конфигурации"""
        from main import AdvancedSDCardTester
        
        test_config = {
            'app': {'name': 'Test', 'version': '3.0'},
            'testing': {'default_passes': 5}
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.json')
        
        # Сохраняем конфигурацию
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        app.config = test_config
        
        # Мокаем open для сохранения
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            app.save_config()
            
            # Проверяем, что файл был открыт для записи
            mock_file.assert_called_once_with('config.json', 'w', encoding='utf-8')
    
    @patch('subprocess.run')
    def test_build_scripts(self, mock_subprocess):
        """Тест скриптов сборки"""
        # Можно протестировать, что скрипты сборки вызывают правильные команды
        pass
    
    def test_import_all_modules(self):
        """Тест импорта всех необходимых модулей"""
        import importlib
        
        required_modules = [
            'tkinter',
            'psutil',
            'matplotlib',
            'numpy',
            'queue',
            'json',
            'platform',
            'threading',
            'time',
            'datetime'
        ]
        
        for module_name in required_modules:
            try:
                importlib.import_module(module_name)
                self.assertTrue(True)  # Модуль импортирован успешно
            except ImportError as e:
                self.fail(f"Не удалось импортировать модуль {module_name}: {e}")

class TestErrorHandling(unittest.TestCase):
    """Тесты обработки ошибок"""
    
    def test_error_handling_in_thread(self):
        """Тест обработки ошибок в потоке"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Симулируем ошибку в потоке
        error_message = "Тестовая ошибка"
        app.message_queue.put(('error', error_message))
        
        # Вызываем обработку очереди
        app.check_queue()
        
        # Проверяем, что ошибка была обработана
        # (можно добавить проверку, если в app.test_error есть side effects)
    
    @patch('messagebox.showerror')
    def test_system_drive_protection(self, mock_messagebox):
        """Тест защиты системных дисков"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Симулируем выбор системного диска
        with patch.object(app.drive_tree, 'selection', return_value=['item1']):
            with patch.object(app.drive_tree, 'item') as mock_item:
                mock_item.return_value = {
                    'values': ['C:\\', 'СИСТЕМНЫЙ', '500 GB', 'NTFS'],
                    'tags': ('system',)
                }
                
                app.on_drive_select(None)
                
                # Проверяем, что кнопка старта заблокирована
                self.assertEqual(app.start_button['state'], 'disabled')

if __name__ == '__main__':
    unittest.main()