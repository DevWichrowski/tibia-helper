class GameConfig:
    def __init__(self):
        # Default game values
        self.DEFAULT_MAX_HP = 1425
        self.DEFAULT_MAX_MANA = 1234
        
        # Current game values (can be overridden)
        self.max_hp = self.DEFAULT_MAX_HP
        self.max_mana = self.DEFAULT_MAX_MANA
        
        # Healing thresholds
        self.hp_threshold = 0.83  # 83% - use F1 for moderate healing
        self.hp_critical_threshold = 0.55  # 55% - use F6 for critical healing
        self.mana_threshold = 0.55  # 55% - use F4 for mana restoration
        
        # Key mappings
        self.heal_key = 'f1'  # Moderate healing
        self.critical_heal_key = 'f6'  # Critical healing
        self.mana_key = 'f4'  # Mana restoration
        
        # Timing settings
        self.cooldown = 0.2  # Seconds between key presses
        self.monitor_frequency = 0.05  # Monitor every 0.05 seconds (20 Hz)
        
        # OCR settings
        self.max_failures_warning = 5  # Warn after 5 consecutive failures
        self.dramatic_drop_threshold = 0.4  # 40% drop is considered dramatic
        self.critical_confirmation_time = 0.5  # Require confirmation within 0.5 seconds
        
        # Debug settings
        self.enable_debug = True
        self.debug_log_file = "debug/logs/game_helper_debug.log"
        
        # PyAutoGUI settings
        self.failsafe_enabled = True
        self.gui_pause = 0.001  # Ultra-fast GUI operations
    
    def set_max_values(self, max_hp, max_mana):
        """Set maximum HP and Mana values"""
        self.max_hp = max_hp
        self.max_mana = max_mana
    
    def get_threshold_info(self):
        """Get formatted threshold information for display"""
        return {
            'hp_critical': f"{self.hp_critical_threshold * 100}%",
            'hp_moderate': f"{self.hp_threshold * 100}%",
            'mana': f"{self.mana_threshold * 100}%"
        } 