"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import json
import os
from unittest.mock import MagicMock, patch

@pytest.fixture
def temp_config_file():
    """Создает временный файл конфигурации"""
    config_data = {
        "app": {
            "name": "SD Card Tester Pro",
            "version": "1.0.0",
            "auto_save_log": False,
            "auto_update_stats": True
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    
    yield config_path
    
    # Очистка
    if os.path.exists(config_path):
        os.unlink(config_path)

@pytest.fixture
def mock_tkinter():
    """Мокает Tkinter для тестов"""
    with patch('tkinter.Tk') as mock_tk:
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        yield mock_root

@pytest.fixture
def app_instance(mock_tkinter, temp_config_file):
    """Создает экземпляр приложения для тестирования"""
    with patch('main.tk.Tk', return_value=mock_tkinter):
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open()):
                from main import AdvancedSDCardTester
                app = AdvancedSDCardTester()
                yield app