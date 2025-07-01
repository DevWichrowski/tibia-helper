#!/usr/bin/env python3
"""
Simplified Health Monitor Tests

Critical tests to ensure healing logic works correctly.
"""

import unittest
from unittest.mock import Mock, patch
import time


# Mock the pyautogui module
class MockPyAutoGUI:
    @staticmethod
    def press(key):
        pass


# Simple config class for testing
class TestConfig:
    def __init__(self):
        self.max_hp = 1000
        self.hp_critical_threshold = 0.55  # 55%
        self.hp_threshold = 0.75  # 75%
        self.cooldown = 0.1
        self.critical_heal_key = 'f6'
        self.heal_key = 'f1'
        self.max_failures_warning = 5
        self.dramatic_drop_threshold = 0.4


# Simplified HealthMonitor for testing (copy of core logic)
class TestHealthMonitor:
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        self.last_heal_press = 0
        self.last_critical_heal_press = 0
        self.consecutive_failures = 0
        self.last_stable_hp = None
        self.last_stable_hp_time = 0
        self.pending_critical_hp = None

    def debug_log(self, message):
        if self.debug_logger:
            self.debug_logger.log(message)

    def press_key_with_cooldown(self, key, last_press_time, action_type="ACTION"):
        current_time = time.time()
        time_since_last = current_time - last_press_time
        
        if time_since_last >= self.config.cooldown:
            MockPyAutoGUI.press(key)
            self.debug_log(f"KEY_PRESS: {key.upper()} pressed for {action_type}")
            return current_time
        else:
            self.debug_log(f"KEY_BLOCKED: {key.upper()} blocked for {action_type}")
            return last_press_time

    def check_hp_and_heal(self, hp_value):
        """Core healing logic - CRITICAL HEALING FIRST!"""
        if hp_value is None or hp_value <= 0:
            self.debug_log(f"DECISION: HP value invalid or zero - no HP action")
            self.consecutive_failures += 1
            return None
        
        self.consecutive_failures = 0
        hp_percentage = hp_value / self.config.max_hp
        current_time = time.time()
        
        self.debug_log(f"DECISION: HP {hp_value} = {hp_percentage*100:.1f}%")
        
        # STEP 1: CRITICAL HEALING CHECK - FIRST PRIORITY!
        if hp_percentage < self.config.hp_critical_threshold:
            self.debug_log(f"🚨 CRITICAL ALERT: HP {hp_percentage*100:.1f}% - IMMEDIATE CRITICAL HEALING REQUIRED!")
            
            # Check for dramatic drops
            is_dramatic_drop = False
            if self.last_stable_hp is not None:
                hp_drop_percent = (self.last_stable_hp - hp_value) / self.config.max_hp
                if hp_drop_percent > self.config.dramatic_drop_threshold:
                    is_dramatic_drop = True
                    self.debug_log(f"STABILITY: Dramatic HP drop detected")
            
            if is_dramatic_drop:
                if self.pending_critical_hp is None:
                    self.pending_critical_hp = hp_value
                    self.debug_log(f"STABILITY: Critical HP needs confirmation")
                    return hp_percentage
                elif abs(hp_value - self.pending_critical_hp) <= 50:
                    self.debug_log(f"🚨 CONFIRMED CRITICAL: Executing emergency heal!")
                    self.last_critical_heal_press = self.press_key_with_cooldown(
                        self.config.critical_heal_key, 
                        self.last_critical_heal_press, 
                        "🚨 EMERGENCY CRITICAL HEAL"
                    )
                    self.pending_critical_hp = None
                    return hp_percentage
                else:
                    self.pending_critical_hp = hp_value
                    return hp_percentage
            else:
                self.debug_log(f"🚨 IMMEDIATE CRITICAL: Executing critical heal NOW!")
                self.last_critical_heal_press = self.press_key_with_cooldown(
                    self.config.critical_heal_key, 
                    self.last_critical_heal_press, 
                    "🚨 IMMEDIATE CRITICAL HEAL"
                )
                self.pending_critical_hp = None
                return hp_percentage
        
        # STEP 2: MODERATE HEALING - ONLY IF NOT CRITICAL
        elif hp_percentage < self.config.hp_threshold:
            self.debug_log(f"DECISION: HP needs moderate healing (not critical)")
            self.last_heal_press = self.press_key_with_cooldown(
                self.config.heal_key, 
                self.last_heal_press, 
                "MODERATE HEAL"
            )
            self.pending_critical_hp = None
        
        # STEP 3: HEALTHY - NO HEALING NEEDED
        else:
            self.debug_log(f"DECISION: HP is healthy - no healing needed")
            self.pending_critical_hp = None
        
        # Update stable HP tracking
        if hp_percentage > self.config.hp_critical_threshold:
            self.last_stable_hp = hp_value
            self.last_stable_hp_time = current_time
        
        return hp_percentage

    def get_hp_status(self, hp_value):
        if hp_value is not None and hp_value > 0:
            hp_percent = (hp_value / self.config.max_hp * 100)
            status = "✓"
        else:
            hp_percent = 0
            status = "✗"
        
        return {
            'value': hp_value,
            'percentage': hp_percent,
            'status': status
        }


class TestHealthMonitorLogic(unittest.TestCase):
    def setUp(self):
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = TestHealthMonitor(self.config, self.debug_logger)

    def test_should_trigger_critical_healing_when_hp_below_55_percent(self):
        """🚨 CRITICAL TEST: F6 must trigger when HP < 55%"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            critical_hp_values = [540, 500, 400, 300, 100]
            
            for hp_value in critical_hp_values:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_critical_heal_press = 0
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    mock_press.assert_called_with('f6')
                    self.assertIsNotNone(result)
                    mock_press.reset_mock()

    def test_should_trigger_moderate_healing_when_hp_between_55_and_75_percent(self):
        """💊 F1 must trigger when 55% <= HP < 75%"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            moderate_hp_values = [740, 700, 650, 600, 560]
            
            for hp_value in moderate_hp_values:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_heal_press = 0
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    mock_press.assert_called_with('f1')
                    self.assertIsNotNone(result)
                    mock_press.reset_mock()

    def test_should_not_trigger_healing_when_hp_above_75_percent(self):
        """✅ No healing when HP >= 75%"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            healthy_hp_values = [1000, 900, 800, 750]
            
            for hp_value in healthy_hp_values:
                with self.subTest(hp_value=hp_value):
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    mock_press.assert_not_called()
                    self.assertIsNotNone(result)
                    mock_press.reset_mock()

    def test_should_prioritize_critical_over_moderate_healing(self):
        """🚨 MOST IMPORTANT: Critical must ALWAYS be checked first!"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            critical_hp = 549  # Just below 55% threshold
            
            self.health_monitor.last_critical_heal_press = 0
            self.health_monitor.last_heal_press = 0
            
            result = self.health_monitor.check_hp_and_heal(critical_hp)
            
            # Must be F6 (critical), never F1 (moderate)
            mock_press.assert_called_with('f6')
            self.assertEqual(mock_press.call_count, 1)

    def test_boundary_conditions_exact_thresholds(self):
        """🎯 Test exact boundary conditions"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            test_cases = [
                # Critical threshold is < 55% (< 550 HP)
                (549, 'f6'),  # Just below critical threshold → F6
                (550, 'f1'),  # Exactly 55% → F1 (not critical)
                (551, 'f1'),  # Just above critical threshold → F1
                
                # Moderate threshold is < 75% (< 750 HP)  
                (749, 'f1'),  # Just below moderate threshold → F1
                (750, None),  # Exactly 75% → No healing (not moderate)
                (751, None),  # Just above moderate threshold → No healing
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
                    
                    mock_press.reset_mock()

    def test_should_handle_invalid_hp_values(self):
        """🛡️ Handle invalid HP safely"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            invalid_values = [None, 0, -100, -1]
            
            for invalid_hp in invalid_values:
                with self.subTest(hp_value=invalid_hp):
                    result = self.health_monitor.check_hp_and_heal(invalid_hp)
                    
                    mock_press.assert_not_called()
                    self.assertIsNone(result)
                    mock_press.reset_mock()

    def test_should_respect_cooldown(self):
        """⏱️ Cooldown must be respected"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            critical_hp = 500
            
            # First call should work
            self.health_monitor.last_critical_heal_press = 0
            self.health_monitor.check_hp_and_heal(critical_hp)
            self.assertEqual(mock_press.call_count, 1)
            
            # Second call immediately should be blocked
            self.health_monitor.check_hp_and_heal(critical_hp)
            self.assertEqual(mock_press.call_count, 1)

    def test_should_return_correct_hp_status(self):
        """📊 HP status calculation"""
        test_cases = [
            (1000, 100.0, "✓"),
            (750, 75.0, "✓"),
            (550, 55.0, "✓"),
            (0, 0.0, "✗"),
            (None, 0.0, "✗"),
        ]
        
        for hp_value, expected_percent, expected_status in test_cases:
            with self.subTest(hp_value=hp_value):
                status = self.health_monitor.get_hp_status(hp_value)
                
                self.assertEqual(status['value'], hp_value)
                # Use round to handle floating point precision
                self.assertEqual(round(status['percentage'], 1), expected_percent)
                self.assertEqual(status['status'], expected_status)

    def test_should_increment_failure_counter(self):
        """📈 Failure counter tracking"""
        initial_failures = self.health_monitor.consecutive_failures
        
        with patch.object(MockPyAutoGUI, 'press'):
            self.health_monitor.check_hp_and_heal(None)
            
        self.assertEqual(self.health_monitor.consecutive_failures, initial_failures + 1)

    def test_should_reset_failure_counter_on_valid_hp(self):
        """🔄 Reset failure counter on success"""
        self.health_monitor.consecutive_failures = 3
        
        with patch.object(MockPyAutoGUI, 'press'):
            self.health_monitor.check_hp_and_heal(800)
            
        self.assertEqual(self.health_monitor.consecutive_failures, 0)

    def test_critical_healing_with_real_thresholds(self):
        """🎮 Test with real game values"""
        # Use real config values
        self.config.max_hp = 1425
        self.config.hp_critical_threshold = 0.55  # 783.75 HP
        self.config.hp_threshold = 0.75  # 1068.75 HP
        
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Test critical threshold
            critical_hp = 783  # Just below 55%
            self.health_monitor.last_critical_heal_press = 0
            self.health_monitor.check_hp_and_heal(critical_hp)
            mock_press.assert_called_with('f6')
            
            # Test moderate threshold
            mock_press.reset_mock()
            moderate_hp = 1068  # Just below 75%
            self.health_monitor.last_heal_press = 0
            self.health_monitor.check_hp_and_heal(moderate_hp)
            mock_press.assert_called_with('f1')


if __name__ == '__main__':
    print("🧪 Running Health Monitor Tests...")
    print("🚨 Testing critical healing priority system")
    print("💊 Testing moderate healing logic")
    print("🛡️ Testing safety mechanisms")
    print()
    
    unittest.main(verbosity=2) 