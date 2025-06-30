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
        
        # Stability tracking to prevent false critical healing from bad OCR
        self.last_stable_hp = None
        self.last_stable_hp_time = 0
        self.pending_critical_hp = None  # HP value that needs confirmation for critical healing
        
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
    
    def check_hp_and_heal(self, hp_value):
        """Check HP value and perform healing if needed - CRITICAL HEALING FIRST!"""
        if hp_value is None or hp_value <= 0:
            self.debug_log(f"DECISION: HP value invalid or zero - no HP action")
            self.consecutive_failures += 1
            if self.consecutive_failures == self.config.max_failures_warning:
                print(f"⚠️  Warning: HP reading has failed {self.consecutive_failures} times in a row")
            return None
        
        # Reset failure counter on successful reading
        self.consecutive_failures = 0
        
        hp_percentage = hp_value / self.config.max_hp
        current_time = time.time()
        
        self.debug_log(f"DECISION: HP {hp_value} = {hp_percentage*100:.1f}% (Critical<{self.config.hp_critical_threshold*100}%, Moderate<{self.config.hp_threshold*100}%)")
        
        # ==========================================
        # STEP 1: CRITICAL HEALING CHECK - FIRST PRIORITY!
        # ==========================================
        # This MUST be checked before anything else to prevent death!
        if hp_percentage < self.config.hp_critical_threshold:
            self.debug_log(f"🚨 CRITICAL ALERT: HP {hp_percentage*100:.1f}% < {self.config.hp_critical_threshold*100}% - IMMEDIATE CRITICAL HEALING REQUIRED!")
            
            # Check for dramatic HP drops that might be OCR errors
            is_dramatic_drop = False
            if self.last_stable_hp is not None:
                hp_drop_percent = (self.last_stable_hp - hp_value) / self.config.max_hp
                if hp_drop_percent > self.config.dramatic_drop_threshold:
                    is_dramatic_drop = True
                    self.debug_log(f"STABILITY: Dramatic HP drop detected: {self.last_stable_hp} → {hp_value} (drop: {hp_drop_percent*100:.1f}%)")
            
            if is_dramatic_drop:
                if self.pending_critical_hp is None:
                    # First time seeing this low HP after a dramatic drop
                    self.pending_critical_hp = hp_value
                    self.debug_log(f"STABILITY: Critical HP {hp_percentage*100:.1f}% needs confirmation due to dramatic drop")
                    return hp_percentage  # Wait for confirmation
                elif abs(hp_value - self.pending_critical_hp) <= 50:  # Similar HP reading - CONFIRMED CRITICAL
                    self.debug_log(f"🚨 CONFIRMED CRITICAL: HP drop confirmed ({self.pending_critical_hp} → {hp_value}) - EXECUTING EMERGENCY HEAL!")
                    self.last_critical_heal_press = self.press_key_with_cooldown(
                        self.config.critical_heal_key, 
                        self.last_critical_heal_press, 
                        "🚨 EMERGENCY CRITICAL HEAL"
                    )
                    self.pending_critical_hp = None
                    return hp_percentage  # CRITICAL HEALING EXECUTED - EXIT IMMEDIATELY
                else:
                    # Different HP reading - update pending
                    self.pending_critical_hp = hp_value
                    self.debug_log(f"STABILITY: Critical HP reading changed, updating pending: {hp_value}")
                    return hp_percentage
            else:
                # No dramatic drop - IMMEDIATE CRITICAL HEALING
                self.debug_log(f"🚨 IMMEDIATE CRITICAL: HP {hp_percentage*100:.1f}% - NO DELAY, EXECUTING CRITICAL HEAL NOW!")
                self.last_critical_heal_press = self.press_key_with_cooldown(
                    self.config.critical_heal_key, 
                    self.last_critical_heal_press, 
                    "🚨 IMMEDIATE CRITICAL HEAL"
                )
                self.pending_critical_hp = None
                return hp_percentage  # CRITICAL HEALING EXECUTED - EXIT IMMEDIATELY
        
        # ==========================================
        # STEP 2: MODERATE HEALING - ONLY IF NOT CRITICAL
        # ==========================================
        # We only get here if HP is NOT critical (>= 55%)
        elif hp_percentage < self.config.hp_threshold:
            self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% needs moderate healing (not critical)")
            self.last_heal_press = self.press_key_with_cooldown(
                self.config.heal_key, 
                self.last_heal_press, 
                "MODERATE HEAL"
            )
            self.pending_critical_hp = None  # Clear any pending critical
        
        # ==========================================
        # STEP 3: HEALTHY - NO HEALING NEEDED
        # ==========================================
        else:
            self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% is healthy - no healing needed")
            self.pending_critical_hp = None  # Clear any pending critical
        
        # Update stable HP tracking
        if hp_percentage > self.config.hp_critical_threshold:
            # This reading seems stable, update our reference
            self.last_stable_hp = hp_value
            self.last_stable_hp_time = current_time
            self.debug_log(f"STABILITY: Updated stable HP reference to {hp_value}")
        
        return hp_percentage
    
    def get_hp_status(self, hp_value):
        """Get HP status information"""
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