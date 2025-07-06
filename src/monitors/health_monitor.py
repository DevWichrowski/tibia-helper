import time
import pyautogui


class HealthMonitor:
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        
        # Timing tracking
        self.last_heal_press = 0
        self.last_critical_heal_press = 0
        
        # Failure tracking
        self.consecutive_failures = 0
        
        # Healing usage counters
        self.moderate_heal_count = 0
        self.critical_heal_count = 0
        
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def press_key_with_cooldown(self, key, last_press_time, action_type="ACTION", cooldown=None):
        """Press a key with cooldown protection"""
        current_time = time.time()
        time_since_last = current_time - last_press_time
        
        # Use provided cooldown or default to regular cooldown
        effective_cooldown = cooldown if cooldown is not None else self.config.cooldown
        
        if time_since_last >= effective_cooldown:
            pyautogui.press(key)
            self.debug_log(f"KEY_PRESS: {key.upper()} pressed for {action_type} (cooldown: {time_since_last:.3f}s, required: {effective_cooldown:.3f}s)")
            print(f"\n🚨 {action_type}: {key.upper()} pressed at {time.strftime('%H:%M:%S')}", flush=True)
            return current_time
        else:
            self.debug_log(f"KEY_BLOCKED: {key.upper()} blocked for {action_type} (cooldown remaining: {effective_cooldown - time_since_last:.3f}s)")
            return last_press_time
    
    def check_hp_and_heal(self, hp_value):
        """Check HP value and perform healing if needed - CRITICAL HEALING IS IMMEDIATE!"""
        if hp_value is None or hp_value <= 0:
            self.debug_log(f"DECISION: HP value invalid or zero - no HP action")
            self.consecutive_failures += 1
            if self.consecutive_failures == self.config.max_failures_warning:
                print(f"⚠️  Warning: HP reading has failed {self.consecutive_failures} times in a row")
            return None
        
        # Handle invalid max HP configuration gracefully
        if self.config.max_hp <= 0:
            self.debug_log(f"ERROR: Invalid max HP configuration: {self.config.max_hp}")
            print(f"❌ Error: Invalid max HP configuration: {self.config.max_hp}")
            return None
        
        # Reset failure counter on successful reading
        self.consecutive_failures = 0
        
        hp_percentage = hp_value / self.config.max_hp
        
        self.debug_log(f"DECISION: HP {hp_value} = {hp_percentage*100:.1f}% (Critical<{self.config.hp_critical_threshold*100}%, Moderate<{self.config.hp_threshold*100}%)")
        
        # ==========================================
        # STEP 1: CRITICAL HEALING - FIRST PRIORITY!
        # ==========================================
        if hp_percentage < self.config.hp_critical_threshold:
            self.debug_log(f"🚨 CRITICAL ALERT: HP {hp_percentage*100:.1f}% < {self.config.hp_critical_threshold*100}% - CRITICAL HEALING!")
            old_time = self.last_critical_heal_press
            self.last_critical_heal_press = self.press_key_with_cooldown(
                self.config.critical_heal_key, 
                self.last_critical_heal_press, 
                "🚨 CRITICAL HEAL",
                cooldown=self.config.critical_cooldown
            )
            # Increment counter only if key was actually pressed
            if self.last_critical_heal_press > old_time:
                self.critical_heal_count += 1
        
        # ==========================================
        # STEP 2: MODERATE HEALING - SECOND PRIORITY
        # ==========================================
        elif hp_percentage < self.config.hp_threshold:
            self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% needs moderate healing")
            old_time = self.last_heal_press
            self.last_heal_press = self.press_key_with_cooldown(
                self.config.heal_key, 
                self.last_heal_press, 
                "MODERATE HEAL",
                cooldown=self.config.critical_cooldown
            )
            # Increment counter only if key was actually pressed
            if self.last_heal_press > old_time:
                self.moderate_heal_count += 1
        
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
    
    def get_healing_summary(self):
        """Get healing usage summary"""
        return {
            'moderate_heals': self.moderate_heal_count,
            'critical_heals': self.critical_heal_count,
            'total_heals': self.moderate_heal_count + self.critical_heal_count
        } 