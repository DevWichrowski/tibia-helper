#!/usr/bin/env python3
"""
Tests for HealthMonitor toggle, counter, and status features

Tests the toggle on/off functionality, heal counters, and status methods.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Mock pyautogui before any imports
sys.modules['pyautogui'] = Mock()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitors.health_monitor import HealthMonitor


class TestConfig:
    """Test configuration for HealthMonitor"""
    def __init__(self):
        self.max_hp = 1000
        self.hp_critical_threshold = 0.55  # 55%
        self.hp_threshold = 0.75  # 75%
        self.cooldown = 0.1
        self.critical_heal_key = 'f6'
        self.heal_key = 'f1'
        self.max_failures_warning = 5


class TestHealthMonitorToggle(unittest.TestCase):
    """Tests for heal toggle functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
    
    def test_heal_enabled_by_default(self):
        """Normal heal should be enabled by default"""
        self.assertTrue(self.health_monitor.heal_enabled)
    
    def test_critical_enabled_by_default(self):
        """Critical heal should be enabled by default"""
        self.assertTrue(self.health_monitor.critical_enabled)
    
    def test_toggle_heal_switches_state(self):
        """toggle_heal should switch between enabled/disabled"""
        # Initially enabled
        self.assertTrue(self.health_monitor.heal_enabled)
        
        # First toggle - disable
        result = self.health_monitor.toggle_heal()
        self.assertFalse(result)
        self.assertFalse(self.health_monitor.heal_enabled)
        
        # Second toggle - enable
        result = self.health_monitor.toggle_heal()
        self.assertTrue(result)
        self.assertTrue(self.health_monitor.heal_enabled)
    
    def test_toggle_heal_returns_new_state(self):
        """toggle_heal should return the new enabled state"""
        result1 = self.health_monitor.toggle_heal()
        self.assertEqual(result1, self.health_monitor.heal_enabled)
        
        result2 = self.health_monitor.toggle_heal()
        self.assertEqual(result2, self.health_monitor.heal_enabled)
    
    def test_toggle_critical_switches_state(self):
        """toggle_critical should switch between enabled/disabled"""
        # Initially enabled
        self.assertTrue(self.health_monitor.critical_enabled)
        
        # First toggle - disable
        result = self.health_monitor.toggle_critical()
        self.assertFalse(result)
        self.assertFalse(self.health_monitor.critical_enabled)
        
        # Second toggle - enable
        result = self.health_monitor.toggle_critical()
        self.assertTrue(result)
        self.assertTrue(self.health_monitor.critical_enabled)
    
    def test_toggle_critical_returns_new_state(self):
        """toggle_critical should return the new enabled state"""
        result1 = self.health_monitor.toggle_critical()
        self.assertEqual(result1, self.health_monitor.critical_enabled)
        
        result2 = self.health_monitor.toggle_critical()
        self.assertEqual(result2, self.health_monitor.critical_enabled)


class TestHealthMonitorDisabledHealing(unittest.TestCase):
    """Tests for disabled healing behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
    
    def test_should_not_moderate_heal_when_disabled(self):
        """Should not trigger moderate heal when heal_enabled is False"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Disable normal heal
            self.health_monitor.heal_enabled = False
            
            # Send moderate HP
            moderate_hp = 700  # 70% - needs moderate heal
            self.health_monitor.check_hp_and_heal(moderate_hp)
            
            # Should NOT press any key
            mock_press.assert_not_called()
    
    def test_should_not_critical_heal_when_disabled(self):
        """Should not trigger critical heal when critical_enabled is False"""
        with patch('monitors.health_monitor.pyautogui.press') as mock_press:
            # Disable critical heal
            self.health_monitor.critical_enabled = False
            
            # Send critical HP
            critical_hp = 400  # 40% - needs critical heal
            self.health_monitor.check_hp_and_heal(critical_hp)
            
            # Should NOT press any key
            mock_press.assert_not_called()
    
    def test_should_log_when_heal_disabled(self):
        """Should log when heal is disabled"""
        self.health_monitor.heal_enabled = False
        
        # Send moderate HP
        self.health_monitor.check_hp_and_heal(700)
        
        # Check debug log was called with disabled message
        calls = [call[0][0] for call in self.debug_logger.log.call_args_list]
        disabled_calls = [c for c in calls if 'DISABLED' in c and 'MODERATE' in c]
        self.assertTrue(len(disabled_calls) > 0)
    
    def test_should_log_when_critical_disabled(self):
        """Should log when critical heal is disabled"""
        self.health_monitor.critical_enabled = False
        
        # Send critical HP
        self.health_monitor.check_hp_and_heal(400)
        
        # Check debug log was called with disabled message
        calls = [call[0][0] for call in self.debug_logger.log.call_args_list]
        disabled_calls = [c for c in calls if 'DISABLED' in c and 'CRITICAL' in c]
        self.assertTrue(len(disabled_calls) > 0)


class TestHealthMonitorCounters(unittest.TestCase):
    """Tests for heal counters"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
    
    def test_counters_start_at_zero(self):
        """Counters should start at zero"""
        self.assertEqual(self.health_monitor.moderate_heal_count, 0)
        self.assertEqual(self.health_monitor.critical_heal_count, 0)
    
    def test_moderate_heal_increments_counter(self):
        """Moderate heal should increment moderate_heal_count"""
        with patch('monitors.health_monitor.pyautogui.press'):
            # Ensure cooldown is cleared
            self.health_monitor.last_heal_press = 0
            
            # Send moderate HP
            self.health_monitor.check_hp_and_heal(700)
            
            self.assertEqual(self.health_monitor.moderate_heal_count, 1)
            self.assertEqual(self.health_monitor.critical_heal_count, 0)
    
    def test_critical_heal_increments_counter(self):
        """Critical heal should increment critical_heal_count"""
        with patch('monitors.health_monitor.pyautogui.press'):
            # Ensure cooldown is cleared
            self.health_monitor.last_heal_press = 0
            
            # Send critical HP
            self.health_monitor.check_hp_and_heal(400)
            
            self.assertEqual(self.health_monitor.critical_heal_count, 1)
            self.assertEqual(self.health_monitor.moderate_heal_count, 0)
    
    def test_counter_not_incremented_when_cooldown_blocked(self):
        """Counter should NOT increment when heal is blocked by cooldown"""
        with patch('monitors.health_monitor.pyautogui.press'):
            import time
            # Set recent heal time (within cooldown)
            self.health_monitor.last_heal_press = time.time()
            
            # Try to moderate heal (should be blocked)
            self.health_monitor.check_hp_and_heal(700)
            
            # Counter should remain at 0
            self.assertEqual(self.health_monitor.moderate_heal_count, 0)
    
    def test_multiple_heals_increment_counter(self):
        """Multiple successful heals should increment counter multiple times"""
        with patch('monitors.health_monitor.pyautogui.press'):
            for i in range(5):
                # Clear cooldown each time
                self.health_monitor.last_heal_press = 0
                self.health_monitor.check_hp_and_heal(700)
            
            self.assertEqual(self.health_monitor.moderate_heal_count, 5)


class TestHealthMonitorSummary(unittest.TestCase):
    """Tests for get_healing_summary"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.health_monitor = HealthMonitor(self.config)
    
    def test_get_healing_summary_initial(self):
        """Initial summary should show zero heals"""
        summary = self.health_monitor.get_healing_summary()
        
        self.assertEqual(summary['moderate_heals'], 0)
        self.assertEqual(summary['critical_heals'], 0)
        self.assertEqual(summary['total_heals'], 0)
    
    def test_get_healing_summary_after_heals(self):
        """Summary should reflect actual heal counts"""
        self.health_monitor.moderate_heal_count = 10
        self.health_monitor.critical_heal_count = 3
        
        summary = self.health_monitor.get_healing_summary()
        
        self.assertEqual(summary['moderate_heals'], 10)
        self.assertEqual(summary['critical_heals'], 3)
        self.assertEqual(summary['total_heals'], 13)


class TestHealthMonitorErrorStatus(unittest.TestCase):
    """Tests for get_error_status"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.config.max_failures_warning = 5
        self.health_monitor = HealthMonitor(self.config)
    
    def test_get_error_status_initial(self):
        """Initial error status should show no errors"""
        status = self.health_monitor.get_error_status()
        
        self.assertEqual(status['consecutive_failures'], 0)
        self.assertFalse(status['has_error'])
        self.assertFalse(status['is_warning'])
    
    def test_get_error_status_below_threshold(self):
        """Below threshold should not trigger error or warning"""
        self.health_monitor.consecutive_failures = 2
        
        status = self.health_monitor.get_error_status()
        
        self.assertEqual(status['consecutive_failures'], 2)
        self.assertFalse(status['has_error'])
        self.assertFalse(status['is_warning'])
    
    def test_get_error_status_has_error(self):
        """3+ failures should trigger has_error"""
        self.health_monitor.consecutive_failures = 3
        
        status = self.health_monitor.get_error_status()
        
        self.assertTrue(status['has_error'])
        self.assertFalse(status['is_warning'])
    
    def test_get_error_status_is_warning(self):
        """5+ failures should trigger is_warning"""
        self.health_monitor.consecutive_failures = 5
        
        status = self.health_monitor.get_error_status()
        
        self.assertTrue(status['has_error'])
        self.assertTrue(status['is_warning'])


class TestHealthMonitorGlobalCooldown(unittest.TestCase):
    """Tests for global cooldown between all heal types"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
    
    def test_uses_single_global_cooldown(self):
        """Should use single last_heal_press for all heal types"""
        with patch('monitors.health_monitor.pyautogui.press'):
            import time
            
            # First critical heal
            self.health_monitor.last_heal_press = 0
            self.health_monitor.check_hp_and_heal(400)  # Critical
            
            first_heal_time = self.health_monitor.last_heal_press
            self.assertGreater(first_heal_time, 0)
            
            # Immediate moderate heal attempt should be blocked
            self.health_monitor.check_hp_and_heal(700)  # Moderate
            
            # Moderate heal count should be 0 (blocked by cooldown)
            self.assertEqual(self.health_monitor.moderate_heal_count, 0)
    
    def test_critical_shares_cooldown_with_moderate(self):
        """Critical heal should share cooldown with moderate heal"""
        with patch('monitors.health_monitor.pyautogui.press'):
            import time
            
            # First moderate heal
            self.health_monitor.last_heal_press = 0
            self.health_monitor.check_hp_and_heal(700)  # Moderate
            
            # Immediate critical heal attempt should be blocked
            self.health_monitor.check_hp_and_heal(400)  # Critical
            
            # Critical heal count should be 0 (blocked by cooldown from moderate)
            self.assertEqual(self.health_monitor.critical_heal_count, 0)


class TestHealthMonitorHPStatus(unittest.TestCase):
    """Extended tests for get_hp_status"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        self.health_monitor = HealthMonitor(self.config)
    
    def test_hp_status_rounds_percentage(self):
        """Percentage should be rounded to 1 decimal place"""
        # 333/1000 = 33.3%
        status = self.health_monitor.get_hp_status(333)
        self.assertEqual(status['percentage'], 33.3)
        
        # 666/1000 = 66.6%
        status = self.health_monitor.get_hp_status(666)
        self.assertEqual(status['percentage'], 66.6)
    
    def test_hp_status_full_hp(self):
        """Full HP should show 100%"""
        status = self.health_monitor.get_hp_status(1000)
        self.assertEqual(status['percentage'], 100.0)
        self.assertEqual(status['status'], '✓')
    
    def test_hp_status_zero_hp(self):
        """Zero HP should show 0%"""
        status = self.health_monitor.get_hp_status(0)
        self.assertEqual(status['percentage'], 0.0)
        self.assertEqual(status['status'], '✗')
    
    def test_hp_status_none_hp(self):
        """None HP should show 0%"""
        status = self.health_monitor.get_hp_status(None)
        self.assertEqual(status['percentage'], 0.0)
        self.assertEqual(status['status'], '✗')


class TestHealthMonitorDebugLogger(unittest.TestCase):
    """Tests for debug logging"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
    
    def test_debug_log_calls_logger(self):
        """debug_log should call the logger when available"""
        debug_logger = Mock()
        health_monitor = HealthMonitor(self.config, debug_logger)
        
        health_monitor.debug_log("test message")
        debug_logger.log.assert_called_with("test message")
    
    def test_debug_log_handles_no_logger(self):
        """debug_log should handle missing logger gracefully"""
        health_monitor = HealthMonitor(self.config, None)
        
        # Should not raise exception
        health_monitor.debug_log("test message")


if __name__ == '__main__':
    print("💊 HEALTH MONITOR EXTENDED TESTS")
    print("=" * 60)
    print("🔄 Toggle functionality")
    print("📊 Counter tracking")
    print("⚠️ Error status")
    print("⏱️ Global cooldown")
    print()
    unittest.main(verbosity=2)
