#!/usr/bin/env python3
"""
Tests for Skinner class

Verifies right-click to hotkey functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Mock pyautogui before any imports
sys.modules['pyautogui'] = Mock()

# Create mock pynput modules
mock_pynput = MagicMock()
mock_keyboard = MagicMock()
mock_mouse = MagicMock()

# Set up keyboard mock
mock_controller_instance = MagicMock()
mock_keyboard.Controller.return_value = mock_controller_instance

sys.modules['pynput'] = mock_pynput
sys.modules['pynput.keyboard'] = mock_keyboard
sys.modules['pynput.mouse'] = mock_mouse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import skinner - this uses the mocked modules
from monitors.skinner import Skinner, get_key_from_string, mouse, keyboard


class SkinnerTestConfig:
    """Test configuration for Skinner"""
    def __init__(self):
        self.skinner_hotkey = 'f3'
        self.skinner_min_delay = 0.001  # Very short delay for tests
        self.skinner_max_delay = 0.002


class TestGetKeyFromString(unittest.TestCase):
    """Tests for get_key_from_string helper function"""
    
    def test_handles_function_keys(self):
        """Should handle function keys F1-F12"""
        # Use the module's actual keyboard.Key references
        result = get_key_from_string('f3')
        self.assertEqual(result, keyboard.Key.f3)
        
        result = get_key_from_string('F6')  # Case insensitive
        self.assertEqual(result, keyboard.Key.f6)
    
    def test_handles_special_keys(self):
        """Should handle special keys like space, enter, tab"""
        self.assertEqual(get_key_from_string('space'), keyboard.Key.space)
        self.assertEqual(get_key_from_string('enter'), keyboard.Key.enter)
        self.assertEqual(get_key_from_string('tab'), keyboard.Key.tab)
        self.assertEqual(get_key_from_string('escape'), keyboard.Key.esc)
        self.assertEqual(get_key_from_string('esc'), keyboard.Key.esc)
    
    def test_handles_single_characters(self):
        """Should return single characters as-is"""
        self.assertEqual(get_key_from_string('x'), 'x')
        self.assertEqual(get_key_from_string('a'), 'a')
        self.assertEqual(get_key_from_string('1'), '1')
    
    def test_defaults_to_f3_for_unknown(self):
        """Should default to F3 for unknown multi-character strings"""
        result = get_key_from_string('unknown_key')
        self.assertEqual(result, keyboard.Key.f3)


class TestSkinner(unittest.TestCase):
    """Tests for Skinner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = SkinnerTestConfig()
        self.debug_logger = Mock()
        
        self.skinner = Skinner(self.config, self.debug_logger)
        # Reset keyboard controller mock for this instance
        self.skinner.keyboard_controller.reset_mock()
    
    def test_should_start_disabled(self):
        """Skinner should be disabled on initialization"""
        self.assertFalse(self.skinner.enabled)
        self.assertFalse(self.skinner._running)
        self.assertEqual(self.skinner.click_count, 0)
    
    def test_toggle_should_switch_state(self):
        """Toggle should switch enabled state"""
        # Initially disabled
        self.assertFalse(self.skinner.enabled)
        
        # First toggle - enable
        result = self.skinner.toggle()
        self.assertTrue(result)
        self.assertTrue(self.skinner.enabled)
        
        # Second toggle - disable
        result = self.skinner.toggle()
        self.assertFalse(result)
        self.assertFalse(self.skinner.enabled)
    
    def test_toggle_should_return_new_state(self):
        """Toggle should return the new enabled state"""
        result1 = self.skinner.toggle()
        self.assertEqual(result1, self.skinner.enabled)
        
        result2 = self.skinner.toggle()
        self.assertEqual(result2, self.skinner.enabled)
    
    def test_toggle_should_log_state_change(self):
        """Toggle should log the state change"""
        self.skinner.toggle()
        
        self.debug_logger.log.assert_called()
        call_args = self.debug_logger.log.call_args[0][0]
        self.assertIn('SKINNER', call_args)
        self.assertIn('ENABLED', call_args)
    
    def test_should_not_respond_when_disabled(self):
        """Should not press key when disabled"""
        # Ensure disabled
        self.skinner.enabled = False
        
        # Simulate right click using the module's button reference
        self.skinner._on_click(100, 200, mouse.Button.right, True)
        
        # Should not press any key
        self.skinner.keyboard_controller.press.assert_not_called()
        self.skinner.keyboard_controller.release.assert_not_called()
    
    def test_should_press_key_on_right_click_when_enabled(self):
        """Should press configured key on right click when enabled"""
        self.skinner.enabled = True
        
        # Simulate right click using the module's button reference
        self.skinner._on_click(100, 200, mouse.Button.right, True)
        
        # Should press and release the key
        self.skinner.keyboard_controller.press.assert_called_once()
        self.skinner.keyboard_controller.release.assert_called_once()
    
    def test_should_not_respond_to_left_click(self):
        """Should not respond to left mouse button clicks"""
        self.skinner.enabled = True
        
        # Simulate left click
        self.skinner._on_click(100, 200, mouse.Button.left, True)
        
        # Should not press any key
        self.skinner.keyboard_controller.press.assert_not_called()
    
    def test_should_not_respond_to_button_release(self):
        """Should not respond to button release events"""
        self.skinner.enabled = True
        
        # Simulate right click release (pressed=False)
        self.skinner._on_click(100, 200, mouse.Button.right, False)
        
        # Should not press any key
        self.skinner.keyboard_controller.press.assert_not_called()
    
    def test_click_should_increment_counter(self):
        """Successful click should increment the counter"""
        self.skinner.enabled = True
        initial_count = self.skinner.click_count
        
        self.skinner._on_click(100, 200, mouse.Button.right, True)
        
        self.assertEqual(self.skinner.click_count, initial_count + 1)
    
    def test_get_stats_returns_correct_data(self):
        """get_stats should return correct statistics"""
        # Initial stats
        stats = self.skinner.get_stats()
        self.assertEqual(stats['enabled'], False)
        self.assertEqual(stats['click_count'], 0)
        
        # After toggle
        self.skinner.toggle()
        stats = self.skinner.get_stats()
        self.assertEqual(stats['enabled'], True)
    
    def test_is_enabled_returns_correct_state(self):
        """is_enabled should return current enabled state"""
        self.assertFalse(self.skinner.is_enabled())
        
        self.skinner.toggle()
        self.assertTrue(self.skinner.is_enabled())
        
        self.skinner.toggle()
        self.assertFalse(self.skinner.is_enabled())
    
    def test_is_running_returns_correct_state(self):
        """is_running should return current running state"""
        self.assertFalse(self.skinner.is_running())
        
        # Manually set running state (normally done by start())
        self.skinner._running = True
        self.assertTrue(self.skinner.is_running())
    
    def test_debug_log_calls_logger(self):
        """debug_log should call the logger when available"""
        self.skinner.debug_log("test message")
        self.debug_logger.log.assert_called_with("test message")
    
    def test_debug_log_handles_no_logger(self):
        """debug_log should handle missing logger gracefully"""
        skinner_no_logger = Skinner(self.config, None)
        
        # Should not raise exception
        skinner_no_logger.debug_log("test message")


class TestSkinnerStartStop(unittest.TestCase):
    """Tests for Skinner start/stop functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = SkinnerTestConfig()
    
    def test_start_sets_running_flag(self):
        """Start should set the running flag"""
        skinner = Skinner(self.config)
        
        self.assertFalse(skinner._running)
        
        skinner.start()
        self.assertTrue(skinner._running)
        
        # Clean up
        skinner.stop()
    
    def test_start_creates_listener(self):
        """Start should create a mouse listener"""
        skinner = Skinner(self.config)
        
        self.assertIsNone(skinner.listener)
        
        skinner.start()
        self.assertIsNotNone(skinner.listener)
        
        # Clean up
        skinner.stop()
    
    def test_stop_clears_running_flag(self):
        """Stop should clear the running flag"""
        skinner = Skinner(self.config)
        
        skinner.start()
        self.assertTrue(skinner._running)
        
        skinner.stop()
        self.assertFalse(skinner._running)
    
    def test_stop_clears_listener(self):
        """Stop should clear the listener"""
        skinner = Skinner(self.config)
        
        skinner.start()
        self.assertIsNotNone(skinner.listener)
        
        skinner.stop()
        self.assertIsNone(skinner.listener)
    
    def test_start_is_idempotent(self):
        """Calling start multiple times should not create multiple listeners"""
        skinner = Skinner(self.config)
        
        skinner.start()
        first_listener = skinner.listener
        
        skinner.start()  # Second call
        
        # Should be the same listener
        self.assertEqual(skinner.listener, first_listener)
        
        # Clean up
        skinner.stop()


if __name__ == '__main__':
    print("🔪 SKINNER TESTS")
    print("=" * 60)
    unittest.main(verbosity=2)
