#!/usr/bin/env python3
"""
Comprehensive tests for HealthMonitor class

These tests ensure the critical healing system works correctly to prevent death.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock pyautogui before any imports
sys.modules['pyautogui'] = Mock()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitors.health_monitor import HealthMonitor
from core.config import GameConfig


class TestHealthMonitor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.config = GameConfig()
        self.config.max_hp = 1000  # Use round numbers for easy testing
        self.config.hp_critical_threshold = 0.55  # 55% = 550 HP
        self.config.hp_threshold = 0.75  # 75% = 750 HP
        self.config.cooldown = 0.1
        self.config.critical_heal_key = 'f6'
        self.config.heal_key = 'f1'
        
        self.debug_logger = Mock()
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)

    def test_should_trigger_critical_healing_when_hp_below_55_percent(self):
        """Test that critical healing (F6) is triggered when HP < 55%"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Test various critical HP values
            critical_hp_values = [540, 500, 400, 300, 100]
            
            for hp_value in critical_hp_values:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_critical_heal_press = 0  # Reset cooldown
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Should trigger critical healing
                    mock_press.assert_called_with('f6')
                    self.assertIsNotNone(result)
                    
                    # Verify debug log contains critical alert
                    self.debug_logger.log.assert_called()
                    calls = [call[0][0] for call in self.debug_logger.log.call_args_list]
                    critical_calls = [call for call in calls if "CRITICAL ALERT" in call or "IMMEDIATE CRITICAL" in call]
                    self.assertTrue(len(critical_calls) > 0, f"No critical alert logged for HP {hp_value}")
                    
                    # Reset for next test
                    mock_press.reset_mock()
                    self.debug_logger.reset_mock()

    def test_should_trigger_moderate_healing_when_hp_between_55_and_75_percent(self):
        """Test that moderate healing (F1) is triggered when 55% <= HP < 75%"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Test HP values that should trigger moderate healing
            moderate_hp_values = [740, 700, 650, 600, 560]
            
            for hp_value in moderate_hp_values:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_heal_press = 0  # Reset cooldown
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Should trigger moderate healing (F1)
                    mock_press.assert_called_with('f1')
                    self.assertIsNotNone(result)
                    
                    # Reset for next test
                    mock_press.reset_mock()

    def test_should_not_trigger_healing_when_hp_above_75_percent(self):
        """Test that no healing is triggered when HP >= 75%"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Test HP values that should NOT trigger healing
            healthy_hp_values = [1000, 900, 800, 750]
            
            for hp_value in healthy_hp_values:
                with self.subTest(hp_value=hp_value):
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Should NOT trigger any healing
                    mock_press.assert_not_called()
                    self.assertIsNotNone(result)
                    
                    # Reset for next test
                    mock_press.reset_mock()

    def test_should_prioritize_critical_over_moderate_healing(self):
        """Test that critical healing is ALWAYS checked first - most important test!"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Test the critical boundary case
            critical_hp = 549  # Just below 55% threshold (550)
            
            # Reset cooldowns
            self.health_monitor.last_critical_heal_press = 0
            self.health_monitor.last_heal_press = 0
            
            result = self.health_monitor.check_hp_and_heal(critical_hp)
            
            # Should trigger CRITICAL healing (F6), NOT moderate healing (F1)
            mock_press.assert_called_with('f6')
            self.assertIsNotNone(result)
            
            # Verify it was critical, not moderate
            calls = mock_press.call_args_list
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][0], 'f6')  # Should be F6, not F1

    def test_should_respect_cooldown_for_critical_healing(self):
        """Test that critical healing respects cooldown"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            critical_hp = 500
            
            # First call should work
            self.health_monitor.last_critical_heal_press = 0
            result1 = self.health_monitor.check_hp_and_heal(critical_hp)
            self.assertEqual(mock_press.call_count, 1)
            
            # Second call immediately after should be blocked by cooldown
            result2 = self.health_monitor.check_hp_and_heal(critical_hp)
            self.assertEqual(mock_press.call_count, 1)  # Still only 1 call

    def test_should_respect_cooldown_for_moderate_healing(self):
        """Test that moderate healing respects cooldown"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            moderate_hp = 700
            
            # First call should work
            self.health_monitor.last_heal_press = 0
            result1 = self.health_monitor.check_hp_and_heal(moderate_hp)
            self.assertEqual(mock_press.call_count, 1)
            
            # Second call immediately after should be blocked by cooldown
            result2 = self.health_monitor.check_hp_and_heal(moderate_hp)
            self.assertEqual(mock_press.call_count, 1)  # Still only 1 call

    def test_should_handle_invalid_hp_values(self):
        """Test handling of invalid HP values"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            invalid_values = [None, 0, -100, -1]
            
            for invalid_hp in invalid_values:
                with self.subTest(hp_value=invalid_hp):
                    result = self.health_monitor.check_hp_and_heal(invalid_hp)
                    
                    # Should not trigger any healing
                    mock_press.assert_not_called()
                    self.assertIsNone(result)
                    
                    # Reset for next test
                    mock_press.reset_mock()

    def test_should_increment_failure_counter_on_invalid_hp(self):
        """Test that failure counter is incremented for invalid HP"""
        initial_failures = self.health_monitor.consecutive_failures
        
        with patch('monitors.health_monitor.pyautogui.press'):
            self.health_monitor.check_hp_and_heal(None)
            
        self.assertEqual(self.health_monitor.consecutive_failures, initial_failures + 1)

    def test_should_reset_failure_counter_on_valid_hp(self):
        """Test that failure counter is reset on valid HP"""
        # Set some failures
        self.health_monitor.consecutive_failures = 3
        
        with patch('monitors.health_monitor.pyautogui.press'):
            self.health_monitor.check_hp_and_heal(800)  # Valid HP
            
        self.assertEqual(self.health_monitor.consecutive_failures, 0)

    def test_should_return_correct_hp_status(self):
        """Test HP status calculation"""
        test_cases = [
            (1000, 100.0, "✓"),  # Full HP
            (750, 75.0, "✓"),    # Threshold HP
            (550, 55.0, "✓"),    # Critical threshold
            (500, 50.0, "✓"),    # Critical HP
            (0, 0.0, "✗"),       # Zero HP
            (None, 0.0, "✗"),    # Invalid HP
        ]
        
        for hp_value, expected_percent, expected_status in test_cases:
            with self.subTest(hp_value=hp_value):
                status = self.health_monitor.get_hp_status(hp_value)
                
                self.assertEqual(status['value'], hp_value)
                self.assertEqual(status['percentage'], expected_percent)
                self.assertEqual(status['status'], expected_status)

    def test_should_handle_dramatic_hp_drops(self):
        """Test handling of dramatic HP drops (stability protection)"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Set a stable HP
            self.health_monitor.last_stable_hp = 900
            
            # Simulate dramatic drop
            dramatic_drop_hp = 400  # 900 -> 400 = 50% drop
            
            # First reading should be pending
            result1 = self.health_monitor.check_hp_and_heal(dramatic_drop_hp)
            self.assertEqual(mock_press.call_count, 0)  # Should not heal yet
            self.assertIsNotNone(self.health_monitor.pending_critical_hp)
            
            # Second similar reading should confirm
            similar_hp = 420  # Within 50 HP of previous reading
            result2 = self.health_monitor.check_hp_and_heal(similar_hp)
            self.assertEqual(mock_press.call_count, 1)  # Should heal now
            mock_press.assert_called_with('f6')

    def test_boundary_conditions(self):
        """Test exact boundary conditions"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            test_cases = [
                (550, 'f6'),  # Exactly at critical threshold (should be critical)
                (549, 'f6'),  # Just below critical threshold
                (551, 'f1'),  # Just above critical threshold (should be moderate)
                (750, 'f1'),  # Exactly at moderate threshold
                (749, 'f1'),  # Just below moderate threshold
                (751, None),  # Just above moderate threshold (no healing)
            ]
            
            for hp_value, expected_key in test_cases:
                with self.subTest(hp_value=hp_value):
                    # Reset cooldowns
                    self.health_monitor.last_critical_heal_press = 0
                    self.health_monitor.last_heal_press = 0
                    
                    self.health_monitor.check_hp_and_heal(hp_value)
                    
                    if expected_key:
                        mock_press.assert_called_with(expected_key)
                    else:
                        mock_press.assert_not_called()
                    
                    # Reset for next test
                    mock_press.reset_mock()

    def test_should_clear_pending_critical_on_healthy_hp(self):
        """Test that pending critical is cleared when HP becomes healthy"""
        # Set pending critical
        self.health_monitor.pending_critical_hp = 400
        
        with patch('monitors.health_monitor.pyautogui.press'):
            # Send healthy HP
            self.health_monitor.check_hp_and_heal(800)
            
        # Pending critical should be cleared
        self.assertIsNone(self.health_monitor.pending_critical_hp)

    def test_critical_healing_messages(self):
        """Test that critical healing generates appropriate log messages"""
        with patch('monitors.health_monitor.pyautogui.press'):
            self.health_monitor.last_critical_heal_press = 0
            
            self.health_monitor.check_hp_and_heal(400)  # Critical HP
            
            # Check that appropriate debug messages were logged
            calls = [call[0][0] for call in self.debug_logger.log.call_args_list]
            
            # Should contain critical alert
            critical_alerts = [call for call in calls if "CRITICAL ALERT" in call or "IMMEDIATE CRITICAL" in call]
            self.assertTrue(len(critical_alerts) > 0, "No critical alert message found")


class TestHealthMonitorIntegration(unittest.TestCase):
    """Integration tests for HealthMonitor with real configuration"""
    
    def test_should_work_with_real_config(self):
        """Test HealthMonitor works with actual GameConfig"""
        config = GameConfig()
        health_monitor = HealthMonitor(config)
        
        # Should initialize without errors
        self.assertIsNotNone(health_monitor.config)
        self.assertEqual(health_monitor.consecutive_failures, 0)
        self.assertEqual(health_monitor.last_heal_press, 0)
        self.assertEqual(health_monitor.last_critical_heal_press, 0)

    def test_should_use_correct_thresholds_from_config(self):
        """Test that HealthMonitor uses correct thresholds from config"""
        config = GameConfig()
        config.max_hp = 1425
        config.hp_critical_threshold = 0.55  # 55%
        config.hp_threshold = 0.75  # 75%
        
        health_monitor = HealthMonitor(config)
        
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Test critical threshold
            critical_hp = int(1425 * 0.55) - 1  # Just below critical
            health_monitor.last_critical_heal_press = 0
            health_monitor.check_hp_and_heal(critical_hp)
            mock_press.assert_called_with('f6')
            
            # Test moderate threshold
            mock_press.reset_mock()
            moderate_hp = int(1425 * 0.75) - 1  # Just below moderate
            health_monitor.last_heal_press = 0
            health_monitor.check_hp_and_heal(moderate_hp)
            mock_press.assert_called_with('f1')


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2) 