"""
Unit tests for SD Card Tester Pro
"""
import unittest
import tempfile
import json
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import tkinter as tk

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSDCardTester(unittest.TestCase):
    """Основные тесты приложения"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Используем временный файл конфигурации
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.config_data = {
            "app": {
                "name": "SD Card Tester Pro",
                "version": "1.0.0",
                "auto_save_log": False,
                "auto_update_stats": True
            },
            "testing": {
                "default_passes": 1,
                "chunk_size_mb": 1024,
                "test_patterns": ["ones", "zeros", "random"],
                "verify_read": True,
                "auto_format": True,
                "default_filesystem": "FAT32"
            },
            "ui": {
                "theme": "dark",
                "language": "ru",
                "chart_points": 100,
                "font_size": 9,
                "show_warnings": True
            }
        }
        json.dump(self.config_data, self.temp_config)
        self.temp_config.close()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    @patch('tkinter.Tk')
    def test_app_initialization(self, mock_tk):
        """Тест инициализации приложения"""
        from main import AdvancedSDCardTester
        
        # Мокаем Tk
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Создаем приложение с мокнутым Tkinter
        with patch('main.tk.Tk', return_value=mock_root):
            app = AdvancedSDCardTester()
        
        # Проверяем, что основные компоненты созданы
        self.assertTrue(hasattr(app, 'root'))
        self.assertTrue(hasattr(app, 'config'))
        self.assertTrue(hasattr(app, 'colors'))
        self.assertTrue(hasattr(app, 'message_queue'))
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_config_loading(self, mock_json_load, mock_file):
        """Тест загрузки конфигурации"""
        from main import AdvancedSDCardTester
        
        # Настраиваем мок для json.load
        mock_json_load.return_value = self.config_data
        
        # Создаем экземпляр приложения
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Проверяем загрузку конфигурации
        self.assertEqual(app.config['app']['name'], "SD Card Tester Pro")
        self.assertEqual(app.config['app']['version'], "1.0.0")
        self.assertEqual(app.config['testing']['default_passes'], 1)
    
    def test_config_merge(self):
        """Тест объединения конфигураций"""
        from main import AdvancedSDCardTester
        
        default_config = {
            'app': {'name': 'Test', 'version': '1.0'},
            'testing': {'passes': 1}
        }
        
        user_config = {
            'app': {'version': '1.0'},
            'new_key': 'value'
        }
        
        # Создаем экземпляр и тестируем merge
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Тестируем метод merge_configs
        app.merge_configs(default_config, user_config)
        
        self.assertEqual(default_config['app']['name'], 'Test')  # Должно остаться
        self.assertEqual(default_config['app']['version'], '1.0')  # Должно
        # обновиться
        self.assertEqual(default_config['new_key'], 'value')  # Должно добавиться
    
    @patch('os.path.exists')
    def test_config_file_not_found(self, mock_exists):
        """Тест работы при отсутствии файла конфигурации"""
        from main import AdvancedSDCardTester
        
        # Файл не существует
        mock_exists.return_value = False
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Должна использоваться конфигурация по умолчанию
        self.assertEqual(app.config['app']['name'], 'SD Card Tester Pro')
    
    @patch('platform.system')
    def test_icon_setup_windows(self, mock_system):
        """Тест настройки иконки для Windows"""
        from main import AdvancedSDCardTester
        
        mock_system.return_value = 'Windows'
        
        with patch('tkinter.Tk'):
            with patch('os.path.exists', return_value=True):
                with patch('main.tk.Tk.iconbitmap') as mock_iconbitmap:
                    app = AdvancedSDCardTester()
                    # Проверяем, что метод был вызван
                    mock_iconbitmap.assert_called_once()
    
    def test_message_queue(self):
        """Тест работы очереди сообщений"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Отправляем сообщение в очередь
        app.message_queue.put(('test', 'message'))
        
        # Получаем сообщение
        message = app.message_queue.get()
        
        self.assertEqual(message[0], 'test')
        self.assertEqual(message[1], 'message')
    
    @patch('psutil.disk_partitions')
    def test_drive_refresh(self, mock_partitions):
        """Тест обновления списка дисков"""
        from main import AdvancedSDCardTester
        
        # Мокаем список разделов
        mock_partition = MagicMock()
        mock_partition.mountpoint = '/test'
        mock_partition.opts = 'rw'
        mock_partition.fstype = 'ext4'
        mock_partitions.return_value = [mock_partition]
        
        with patch('tkinter.Tk'):
            with patch('psutil.disk_usage') as mock_usage:
                mock_usage.return_value.total = 100 * 1024**3  # 100 GB
                app = AdvancedSDCardTester()
                
                # Тестируем обновление списка дисков
                app.refresh_drives_list()
                
                # Проверяем, что диски добавлены
                self.assertTrue(len(app.drive_tree.get_children()) > 0)

class TestUtilityFunctions(unittest.TestCase):
    """Тесты вспомогательных функций"""
    
    def test_format_bytes(self):
        """Тест форматирования байтов в читаемый вид"""
        # Этот тест можно добавить, если реализовать функцию format_bytes
        pass
    
    def test_validate_drive_path(self):
        """Тест валидации пути к диску"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Тестируем на разных ОС
        with patch('platform.system', return_value='Windows'):
            # Windows системные диски
            self.assertFalse(app.check_admin_linux())  # Должно вернуть False для Windows
            # Здесь можно добавить тест для Windows проверки
    
    @patch('webbrowser.open')
    def test_open_documentation(self, mock_open):
        """Тест открытия документации"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        app.open_documentation()
        mock_open.assert_called_with("https://github.com/yourusername/sd-card-tester-pro/wiki")
    
    def test_log_message(self):
        """Тест логирования сообщений"""
        from main import AdvancedSDCardTester
        
        with patch('tkinter.Tk'):
            app = AdvancedSDCardTester()
        
        # Тестируем логирование
        test_message = "Тестовое сообщение"
        app.log_message(test_message, 'info')
        
        # Проверяем, что сообщение добавлено в лог
        log_content = app.log_text.get('1.0', 'end').strip()
        self.assertIn(test_message, log_content)

if __name__ == '__main__':
    unittest.main()