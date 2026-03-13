import pytest
import platform
from unittest.mock import Mock, patch, MagicMock
from core.drive_manager import DriveManager

class TestDriveManager:
    @patch('psutil.disk_partitions')
    def test_get_drives_list_with_all_true(self, mock_partitions):
        """Проверяем, что при отсутствии WMI используется psutil с all=True."""
        mock_part = Mock()
        mock_part.mountpoint = 'C:\\'
        mock_part.device = 'C:'
        mock_part.fstype = 'NTFS'
        mock_part.opts = 'rw,fixed'
        mock_partitions.return_value = [mock_part]

        with patch('psutil.disk_usage') as mock_usage:
            mock_usage.return_value.total = 100 * 1024**3
            mock_usage.return_value.used = 50 * 1024**3
            mock_usage.return_value.free = 50 * 1024**3
            mock_usage.return_value.percent = 50.0

            dm = DriveManager()
            dm.wmi_conn = None  # эмулируем отсутствие WMI
            dm._is_system_drive = Mock(return_value=True)
            dm._get_volume_label = Mock(return_value="System")
            dm._is_removable = Mock(return_value=False)

            drives = dm.get_drives_list()
            assert len(drives) == 1
            assert drives[0]['path'] == 'C:\\'
            assert drives[0]['is_system'] is True
            assert drives[0]['label'] == "System"
            # Проверяем, что all=True передаётся
            mock_partitions.assert_called_with(all=True)

    def test_is_system_drive_windows(self):
        dm = DriveManager()
        dm.system = "Windows"
        with patch.dict('os.environ', {'SystemDrive': 'C:'}):
            assert dm._is_system_drive('C:\\') is True
            assert dm._is_system_drive('D:\\') is False

    def test_is_system_drive_linux(self):
        dm = DriveManager()
        dm.system = "Linux"
        assert dm._is_system_drive('/') is True
        assert dm._is_system_drive('/home') is False

    @patch('core.drive_manager.wmi', None)
    def test_get_device_path_windows_fallback(self):
        dm = DriveManager()
        dm.system = "Windows"
        # при отсутствии wmi возвращает None
        assert dm._get_physical_drive_index_from_path('C:\\') is None

    # Новые тесты для S.M.A.R.T. (можно заглушить)
    def test_get_smart_data_returns_dict(self):
        dm = DriveManager()
        smart = dm.get_smart_data('C:\\')
        assert isinstance(smart, dict)
        assert 'status' in smart