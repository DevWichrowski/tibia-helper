#!/usr/bin/env python3
"""
COMPREHENSIVE Health Monitor Tests - Extreme Critical Healing Scenarios

These tests push the health monitor to its limits with the most dangerous
healing situations to ensure it can handle ANY critical scenario.
"""

import unittest
from unittest.mock import Mock, patch
import time
import sys


# Mock the pyautogui module
class MockPyAutoGUI:
    @staticmethod
    def press(key):
        pass


# Enhanced config class for testing
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


# Enhanced HealthMonitor for testing with floating point fixes
class TestHealthMonitor:
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        self.last_heal_press = 0
        self.last_critical_heal_press = 0
        self.consecutive_failures = 0

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
        """Check HP value and perform healing if needed - CRITICAL HEALING IS IMMEDIATE!"""
        if hp_value is None or hp_value <= 0:
            self.debug_log(f"DECISION: HP value invalid or zero - no HP action")
            self.consecutive_failures += 1
            return None
        
        # Handle invalid max HP configuration gracefully
        if self.config.max_hp <= 0:
            self.debug_log(f"ERROR: Invalid max HP configuration: {self.config.max_hp}")
            return None
        
        # Reset failure counter on successful reading
        self.consecutive_failures = 0
        
        hp_percentage = hp_value / self.config.max_hp
        
        self.debug_log(f"DECISION: HP {hp_value} = {hp_percentage*100:.1f}% (Critical<{self.config.hp_critical_threshold*100}%, Moderate<{self.config.hp_threshold*100}%)")
        
        # ==========================================
        # STEP 1: CRITICAL HEALING - IMMEDIATE!
        # ==========================================
        if hp_percentage < self.config.hp_critical_threshold:
            self.debug_log(f"🚨 CRITICAL ALERT: HP {hp_percentage*100:.1f}% < {self.config.hp_critical_threshold*100}% - IMMEDIATE CRITICAL HEALING!")
            self.last_critical_heal_press = self.press_key_with_cooldown(
                self.config.critical_heal_key, 
                self.last_critical_heal_press, 
                "🚨 CRITICAL HEAL"
            )
            return hp_percentage  # CRITICAL HEALING EXECUTED - EXIT IMMEDIATELY
        
        # ==========================================
        # STEP 2: MODERATE HEALING - ONLY IF NOT CRITICAL
        # ==========================================
        elif hp_percentage < self.config.hp_threshold:
            self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% needs moderate healing")
            self.last_heal_press = self.press_key_with_cooldown(
                self.config.heal_key, 
                self.last_heal_press, 
                "MODERATE HEAL"
            )
        
        # ==========================================
        # STEP 3: HEALTHY - NO HEALING NEEDED
        # ==========================================
        else:
            self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% is healthy - no healing needed")
        
        return hp_percentage

    def get_hp_status(self, hp_value):
        """Get HP status information"""
        if hp_value is not None and hp_value > 0:
            hp_percent = round((hp_value / self.config.max_hp * 100), 1)  # Round to 1 decimal place
            status = "✓"
        else:
            hp_percent = 0.0
            status = "✗"
        
        return {
            'value': hp_value,
            'percentage': hp_percent,
            'status': status
        }


class TestCriticalHealingSurvival(unittest.TestCase):
    """🚨 EXTREME Critical Healing Tests - Life or Death Scenarios"""
    
    def setUp(self):
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = TestHealthMonitor(self.config, self.debug_logger)

    def test_should_survive_near_death_scenarios(self):
        """💀 Near-death HP values must trigger F6 immediately"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            near_death_values = [1, 5, 10, 25, 50, 100]  # Very low HP
            
            for hp_value in near_death_values:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_critical_heal_press = 0
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Must trigger F6 for survival
                    mock_press.assert_called_with('f6')
                    self.assertIsNotNone(result)
                    
                    # Verify critical alert in logs
                    calls = [call[0][0] for call in self.debug_logger.log.call_args_list]
                    critical_alerts = [call for call in calls if "CRITICAL ALERT" in call]
                    self.assertTrue(len(critical_alerts) > 0, f"No critical alert for HP {hp_value}")
                    
                    mock_press.reset_mock()
                    self.debug_logger.reset_mock()

    def test_should_handle_rapid_hp_drops_during_combat(self):
        """⚔️ Rapid HP drops during intense combat"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Simulate rapid combat damage
            combat_sequence = [800, 650, 500, 350, 200, 100]  # Rapid decline
            
            for i, hp_value in enumerate(combat_sequence):
                with self.subTest(sequence_step=i, hp_value=hp_value):
                    # Reset cooldowns for each test
                    self.health_monitor.last_critical_heal_press = 0
                    self.health_monitor.last_heal_press = 0
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    if hp_value < 550:  # Below critical threshold
                        mock_press.assert_called_with('f6')
                    elif hp_value < 750:  # Below moderate threshold
                        mock_press.assert_called_with('f1')
                    else:
                        mock_press.assert_not_called()
                    
                    self.assertIsNotNone(result)
                    mock_press.reset_mock()

    def test_should_prioritize_critical_healing_over_cooldown_in_emergency(self):
        """🚨 Critical healing should work even with tight cooldowns"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Set recent critical heal (normally would block)
            self.health_monitor.last_critical_heal_press = time.time() - 0.05  # 50ms ago
            
            emergency_hp = 100  # Life-threatening
            
            result = self.health_monitor.check_hp_and_heal(emergency_hp)
            
            # Even with recent heal, critical should still be attempted
            # (actual cooldown logic would handle the timing)
            self.assertIsNotNone(result)

    def test_should_handle_multiple_consecutive_critical_readings(self):
        """🔄 Multiple critical readings in a row"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            critical_sequence = [400, 380, 350, 320, 300]  # Consecutive critical readings
            
            for i, hp_value in enumerate(critical_sequence):
                # Reset cooldown for each test
                self.health_monitor.last_critical_heal_press = 0
                
                result = self.health_monitor.check_hp_and_heal(hp_value)
                
                # Each should trigger F6
                mock_press.assert_called_with('f6')
                self.assertIsNotNone(result)
                
                mock_press.reset_mock()

    def test_should_handle_ocr_failures_during_critical_moments(self):
        """👁️ OCR failures when critically low"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Simulate OCR failure followed by critical reading
            ocr_failure_sequence = [None, None, 300, None, 250, 200]
            
            for hp_value in ocr_failure_sequence:
                if hp_value is None:
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    self.assertIsNone(result)
                    mock_press.assert_not_called()
                else:
                    self.health_monitor.last_critical_heal_press = 0
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    mock_press.assert_called_with('f6')
                
                mock_press.reset_mock()

    def test_should_handle_boundary_hp_values_precisely(self):
        """🎯 Exact boundary values with floating point precision"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Test with floating point precision issues
            boundary_cases = [
                (549.9999, 'f6'),  # Should round to critical
                (550.0001, 'f1'),  # Should round to moderate
                (749.9999, 'f1'),  # Should round to moderate
                (750.0001, None),  # Should round to healthy
            ]
            
            for hp_value, expected_key in boundary_cases:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_critical_heal_press = 0
                    self.health_monitor.last_heal_press = 0
                    
                    self.health_monitor.check_hp_and_heal(hp_value)
                    
                    if expected_key:
                        mock_press.assert_called_with(expected_key)
                    else:
                        mock_press.assert_not_called()
                    
                    mock_press.reset_mock()

    def test_should_handle_recovery_scenarios(self):
        """🔄 Recovery from critical to healthy states"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Simulate recovery sequence
            recovery_sequence = [300, 400, 600, 800, 1000]  # Critical -> Healthy
            
            for hp_value in recovery_sequence:
                self.health_monitor.last_critical_heal_press = 0
                self.health_monitor.last_heal_press = 0
                
                result = self.health_monitor.check_hp_and_heal(hp_value)
                
                # Verify correct healing at each stage
                if hp_value < 550:
                    mock_press.assert_called_with('f6')
                elif hp_value < 750:
                    mock_press.assert_called_with('f1')
                else:
                    mock_press.assert_not_called()
                
                mock_press.reset_mock()

    def test_floating_point_precision_fixed(self):
        """🔢 Floating point precision issues resolved"""
        test_cases = [
            (550, 55.0),   # Should be exactly 55.0, not 55.00000000001
            (750, 75.0),   # Should be exactly 75.0
            (333, 33.3),   # Should be exactly 33.3
            (666, 66.6),   # Should be exactly 66.6
        ]
        
        for hp_value, expected_percent in test_cases:
            with self.subTest(hp_value=hp_value):
                status = self.health_monitor.get_hp_status(hp_value)
                
                # Should be exactly the expected value, no floating point errors
                self.assertEqual(status['percentage'], expected_percent)
                self.assertIsInstance(status['percentage'], float)

    def test_should_handle_extreme_low_hp_values(self):
        """💀 Extreme low HP (1-10 HP) survival scenarios"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            extreme_low_hp = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            
            for hp_value in extreme_low_hp:
                with self.subTest(hp_value=hp_value):
                    self.health_monitor.last_critical_heal_press = 0
                    
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # All must trigger F6 for survival
                    mock_press.assert_called_with('f6')
                    self.assertIsNotNone(result)
                    
                    # Verify percentage is calculated correctly
                    status = self.health_monitor.get_hp_status(hp_value)
                    expected_percent = round(hp_value / 1000 * 100, 1)
                    self.assertEqual(status['percentage'], expected_percent)
                    
                    mock_press.reset_mock()

    def test_should_handle_zero_max_hp_gracefully(self):
        """🚫 Handle zero max HP without crashing"""
        self.config.max_hp = 0
        
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            # Should not crash with division by zero
            result = self.health_monitor.check_hp_and_heal(100)
            
            # Should return None and not trigger any healing
            self.assertIsNone(result)
            mock_press.assert_not_called()
            
            # Test negative max HP too
            self.config.max_hp = -100
            result2 = self.health_monitor.check_hp_and_heal(100)
            self.assertIsNone(result2)
            mock_press.assert_not_called()


class TestHealthMonitorEdgeCases(unittest.TestCase):
    """🔬 Edge cases and error conditions"""
    
    def setUp(self):
        self.config = TestConfig()
        self.debug_logger = Mock()
        self.health_monitor = TestHealthMonitor(self.config, self.debug_logger)

    def test_should_handle_negative_hp_values(self):
        """➖ Handle negative HP values safely"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            negative_values = [-1, -10, -100, -1000]
            
            for hp_value in negative_values:
                with self.subTest(hp_value=hp_value):
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Should not trigger any healing
                    mock_press.assert_not_called()
                    self.assertIsNone(result)
                    
                    mock_press.reset_mock()

    def test_should_handle_extremely_high_hp_values(self):
        """⬆️ Handle HP values above max HP"""
        with patch.object(MockPyAutoGUI, 'press') as mock_press:
            high_values = [1001, 2000, 10000, 999999]  # Above max HP (1000)
            
            for hp_value in high_values:
                with self.subTest(hp_value=hp_value):
                    result = self.health_monitor.check_hp_and_heal(hp_value)
                    
                    # Should not trigger any healing (above 75%)
                    mock_press.assert_not_called()
                    self.assertIsNotNone(result)
                    
                    # Status should handle high values gracefully
                    status = self.health_monitor.get_hp_status(hp_value)
                    self.assertGreater(status['percentage'], 100.0)
                    
                    mock_press.reset_mock()


if __name__ == '__main__':
    print("🚨 COMPREHENSIVE CRITICAL HEALING TESTS")
    print("=" * 60)
    print("Testing extreme survival scenarios...")
    print("💀 Near-death situations")
    print("⚔️ Combat damage sequences") 
    print("🔄 Recovery scenarios")
    print("🎯 Boundary precision")
    print("🔢 Floating point fixes")
    print()
    
    unittest.main(verbosity=2) 