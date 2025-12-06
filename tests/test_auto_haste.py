#!/usr/bin/env python3
"""
Tests for AutoHaste class

Verifies automatic haste spell casting functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Mock pyautogui and pynput before any imports
sys.modules['pyautogui'] = Mock()

mock_keyboard = MagicMock()
mock_controller_instance = MagicMock()
mock_keyboard.Controller.return_value = mock_controller_instance
sys.modules['pynput'] = MagicMock()
sys.modules['pynput.keyboard'] = mock_keyboard

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitors.auto_haste import AutoHaste


class TestConfig:
    """Test configuration for AutoHaste"""
    def __init__(self):
        self.haste_hotkey = 'x'
        self.haste_min_interval = 27
        self.haste_max_interval = 30


class TestAutoHaste(unittest.TestCase):
    """Tests for AutoHaste functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.debug_logger = Mock()
        
        # Reset the mock controller for each test
        mock_controller_instance.reset_mock()
        
        self.auto_haste = AutoHaste(self.config, self.debug_logger)
    
    def test_should_start_disabled(self):
        """AutoHaste should be disabled on initialization"""
        self.assertFalse(self.auto_haste.enabled)
        self.assertFalse(self.auto_haste._running)
        self.assertEqual(self.auto_haste.cast_count, 0)
    
    def test_toggle_should_switch_state(self):
        """Toggle should switch enabled state"""
        # Initially disabled
        self.assertFalse(self.auto_haste.enabled)
        
        # First toggle - enable
        result = self.auto_haste.toggle()
        self.assertTrue(result)
        self.assertTrue(self.auto_haste.enabled)
        
        # Second toggle - disable
        result = self.auto_haste.toggle()
        self.assertFalse(result)
        self.assertFalse(self.auto_haste.enabled)
    
    def test_toggle_should_return_new_state(self):
        """Toggle should return the new enabled state"""
        result1 = self.auto_haste.toggle()
        self.assertEqual(result1, self.auto_haste.enabled)
        
        result2 = self.auto_haste.toggle()
        self.assertEqual(result2, self.auto_haste.enabled)
    
    def test_should_cast_immediately_when_enabled(self):
        """Should cast haste immediately when toggled on"""
        initial_count = self.auto_haste.cast_count
        
        # Toggle on should trigger immediate cast
        self.auto_haste.toggle()
        
        # Cast count should have increased
        self.assertGreater(self.auto_haste.cast_count, initial_count)
    
    def test_cast_should_increment_counter(self):
        """Cast should increment the cast counter"""
        initial_count = self.auto_haste.cast_count
        
        # Manually call cast
        self.auto_haste._cast_haste()
        
        self.assertEqual(self.auto_haste.cast_count, initial_count + 1)
    
    def test_cast_should_update_last_cast_time(self):
        """Cast should update the last_cast_time"""
        self.assertEqual(self.auto_haste.last_cast_time, 0)
        
        before = time.time()
        self.auto_haste._cast_haste()
        after = time.time()
        
        self.assertGreaterEqual(self.auto_haste.last_cast_time, before)
        self.assertLessEqual(self.auto_haste.last_cast_time, after)
    
    def test_get_stats_returns_correct_data(self):
        """get_stats should return correct statistics"""
        # Initial stats
        stats = self.auto_haste.get_stats()
        self.assertEqual(stats['enabled'], False)
        self.assertEqual(stats['cast_count'], 0)
        
        # After toggle and cast
        self.auto_haste.toggle()
        stats = self.auto_haste.get_stats()
        self.assertEqual(stats['enabled'], True)
        self.assertGreaterEqual(stats['cast_count'], 1)  # Toggle causes immediate cast
    
    def test_is_enabled_returns_correct_state(self):
        """is_enabled should return current enabled state"""
        self.assertFalse(self.auto_haste.is_enabled())
        
        self.auto_haste.toggle()
        self.assertTrue(self.auto_haste.is_enabled())
        
        self.auto_haste.toggle()
        self.assertFalse(self.auto_haste.is_enabled())
    
    def test_is_running_returns_correct_state(self):
        """is_running should return current running state"""
        self.assertFalse(self.auto_haste.is_running())
        
        # Manually set running state (normally done by start())
        self.auto_haste._running = True
        self.assertTrue(self.auto_haste.is_running())
    
    def test_debug_log_calls_logger(self):
        """debug_log should call the logger when available"""
        self.auto_haste.debug_log("test message")
        self.debug_logger.log.assert_called_with("test message")
    
    def test_debug_log_handles_no_logger(self):
        """debug_log should handle missing logger gracefully"""
        auto_haste_no_logger = AutoHaste(self.config, None)
        
        # Should not raise exception
        auto_haste_no_logger.debug_log("test message")
    
    def test_cast_uses_keyboard_controller(self):
        """Cast should use the keyboard controller to press keys"""
        self.auto_haste._cast_haste()
        
        # Should call press and release on the controller
        self.auto_haste.keyboard_controller.press.assert_called()
        self.auto_haste.keyboard_controller.release.assert_called()


class TestAutoHasteStartStop(unittest.TestCase):
    """Tests for AutoHaste start/stop functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
    
    def test_start_sets_running_flag(self):
        """Start should set the running flag"""
        auto_haste = AutoHaste(self.config)
        
        self.assertFalse(auto_haste._running)
        
        auto_haste.start()
        self.assertTrue(auto_haste._running)
        
        # Clean up
        auto_haste.stop()
    
    def test_start_creates_thread(self):
        """Start should create a daemon thread"""
        auto_haste = AutoHaste(self.config)
        
        self.assertIsNone(auto_haste._thread)
        
        auto_haste.start()
        self.assertIsNotNone(auto_haste._thread)
        self.assertTrue(auto_haste._thread.daemon)
        
        # Clean up
        auto_haste.stop()
    
    def test_stop_clears_running_flag(self):
        """Stop should clear the running flag"""
        auto_haste = AutoHaste(self.config)
        
        auto_haste.start()
        self.assertTrue(auto_haste._running)
        
        auto_haste.stop()
        self.assertFalse(auto_haste._running)
        self.assertFalse(auto_haste.enabled)
    
    def test_start_is_idempotent(self):
        """Calling start multiple times should not create multiple threads"""
        auto_haste = AutoHaste(self.config)
        
        auto_haste.start()
        first_thread = auto_haste._thread
        
        auto_haste.start()  # Second call
        
        # Should be the same thread
        self.assertEqual(auto_haste._thread, first_thread)
        
        # Clean up
        auto_haste.stop()


if __name__ == '__main__':
    print("⚡ AUTO-HASTE TESTS")
    print("=" * 60)
    unittest.main(verbosity=2)
