import time
import pyautogui


class ManaMonitor:
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        
        # Timing tracking
        self.last_mana_press = 0
        
        # Failure tracking
        self.consecutive_failures = 0
        
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def press_key_with_cooldown(self, key, last_press_time, action_type="ACTION"):
        """Press a key with cooldown protection"""
        current_time = time.time()
        time_since_last = current_time - last_press_time
        
        if time_since_last >= self.config.cooldown:
            pyautogui.press(key)
            self.debug_log(f"KEY_PRESS: {key.upper()} pressed for {action_type} (cooldown: {time_since_last:.3f}s)")
            print(f"\n🚨 {action_type}: {key.upper()} pressed at {time.strftime('%H:%M:%S')}", flush=True)
            return current_time
        else:
            self.debug_log(f"KEY_BLOCKED: {key.upper()} blocked for {action_type} (cooldown remaining: {self.config.cooldown - time_since_last:.3f}s)")
            return last_press_time
    
    def check_mana_and_restore(self, mana_value):
        """Check mana value and restore if needed"""
        if mana_value is None or mana_value <= 0:
            self.debug_log(f"DECISION: Mana value invalid or zero - no mana action")
            self.consecutive_failures += 1
            if self.consecutive_failures == self.config.max_failures_warning:
                print(f"⚠️  Warning: Mana reading has failed {self.consecutive_failures} times in a row")
            return None
        
        # Reset failure counter on successful reading
        self.consecutive_failures = 0
        
        mana_percentage = mana_value / self.config.max_mana
        self.debug_log(f"DECISION: Mana {mana_value} = {mana_percentage*100:.1f}% (Threshold<{self.config.mana_threshold*100}%)")
        
        if mana_percentage < self.config.mana_threshold:
            self.debug_log(f"DECISION: Mana {mana_percentage*100:.1f}% < {self.config.mana_threshold*100}% - MANA restoration needed")
            self.last_mana_press = self.press_key_with_cooldown(
                self.config.mana_key, 
                self.last_mana_press, 
                "MANA"
            )
        else:
            self.debug_log(f"DECISION: Mana {mana_percentage*100:.1f}% is sufficient - no mana action")
        
        return mana_percentage
    
    def get_mana_status(self, mana_value):
        """Get mana status information"""
        if mana_value is not None and mana_value > 0:
            mana_percent = (mana_value / self.config.max_mana * 100)
            status = "✓"
        else:
            mana_percent = 0
            status = "✗"
        
        return {
            'value': mana_value,
            'percentage': mana_percent,
            'status': status
        } 