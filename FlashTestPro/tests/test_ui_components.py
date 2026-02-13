"""
Tests for UI components
"""
import pytest
from unittest.mock import MagicMock, patch

def test_create_widgets_structure(app_instance):
    """Test that all UI widgets are created"""
    # Mock the widget creation methods
    with patch.object(app_instance, 'create_menu') as mock_menu:
        with patch.object(app_instance, 'setup_speed_chart') as mock_chart:
            with patch.object(app_instance, 'setup_stats_tab') as mock_stats:
                with patch.object(app_instance, 'setup_log_tab') as mock_log:
                    with patch.object(app_instance, 'setup_info_tab') as mock_info:
                        app_instance.create_widgets()
                        
                        # Verify all widget creation methods were called
                        mock_menu.assert_called_once()
                        mock_chart.assert_called_once()
                        mock_stats.assert_called_once()
                        mock_log.assert_called_once()
                        mock_info.assert_called_once()

def test_button_states(app_instance):
    """Test button states in different modes"""
    # Initial state
    assert app_instance.start_button['state'] == 'normal'
    assert app_instance.pause_button['state'] == 'disabled'
    assert app_instance.stop_button['state'] == 'disabled'
    
    # During test
    app_instance.test_running = True
    app_instance.update_button_states()  # You'll need to implement this method
    assert app_instance.start_button['state'] == 'disabled'
    assert app_instance.pause_button['state'] == 'normal'
    assert app_instance.stop_button['state'] == 'normal'

def test_drive_tree_columns(app_instance):
    """Test drive treeview columns"""
    columns = app_instance.drive_tree['columns']
    expected_columns = ('drive', 'type', 'size', 'filesystem')
    
    assert columns == expected_columns
    
    # Check column headings
    for col in expected_columns:
        heading = app_instance.drive_tree.heading(col)
        assert 'text' in heading

def test_progress_bar_updates(app_instance):
    """Test progress bar functionality"""
    # Initial value
    assert app_instance.progress_bar['value'] == 0
    
    # Update progress
    app_instance.progress_bar['value'] = 50
    assert app_instance.progress_bar['value'] == 50
    
    # Update label
    app_instance.progress_label.config(text="50% complete")
    assert app_instance.progress_label.cget('text') == "50% complete"