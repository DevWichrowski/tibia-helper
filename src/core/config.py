import json
import os


class GameConfig:
    def __init__(self):
        # Load from config.json if exists
        config_data = self._load_config()
        
        # Default game values
        self.DEFAULT_MAX_HP = config_data.get('max_hp', 1067)
        self.max_hp = self.DEFAULT_MAX_HP
        
        # Healing thresholds
        healing = config_data.get('healing', {})
        self.hp_threshold = healing.get('hp_threshold', 0.75)
        self.hp_critical_threshold = healing.get('hp_critical_threshold', 0.55)
        self.heal_key = healing.get('heal_key', 'f1')
        self.critical_heal_key = healing.get('critical_heal_key', 'f2')
        self.cooldown = healing.get('cooldown', 0.2)
        
        # Timing settings
        self.monitor_frequency = 0.05  # 20 Hz
        
        # OCR settings
        self.max_failures_warning = 5
        self.dramatic_drop_threshold = 0.4
        self.critical_confirmation_time = 0.5
        
        # Debug settings
        debug = config_data.get('debug', {})
        self.enable_debug = debug.get('enabled', True)
        self.debug_log_file = debug.get('log_file', 'debug/logs/game_helper_debug.log')
        
        # PyAutoGUI settings
        self.failsafe_enabled = True
        self.gui_pause = 0.001
        
        # Overlay settings
        overlay = config_data.get('overlay', {})
        self.overlay_enabled = overlay.get('enabled', True)
        self.overlay_opacity = overlay.get('opacity', 0.9)
        
        # Hotkey settings
        hotkeys = config_data.get('hotkeys', {})
        self.toggle_key = hotkeys.get('toggle_bot', 'f9')
        
        # Skinner settings
        skinner = config_data.get('skinner', {})
        self.skinner_hotkey = skinner.get('hotkey', 'f3')
        self.skinner_min_delay = skinner.get('min_delay', 0.2)
        self.skinner_max_delay = skinner.get('max_delay', 0.4)
        self.skinner_enabled_on_start = skinner.get('enabled_on_start', False)
        
        # Auto-haste settings
        auto_haste = config_data.get('auto_haste', {})
        self.haste_hotkey = auto_haste.get('hotkey', 'x')
        self.haste_min_interval = auto_haste.get('min_interval', 27)
        self.haste_max_interval = auto_haste.get('max_interval', 30)
        self.haste_enabled_on_start = auto_haste.get('enabled_on_start', False)
    
    def _load_config(self):
        """Load config from JSON file"""
        # Try multiple locations for config file
        possible_paths = [
            'config.json',
            os.path.join(os.path.dirname(__file__), '..', '..', 'config.json'),
            os.path.expanduser('~/Documents/Projects/auto-h/config.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except:
                    pass
        
        return {}  # Return empty dict if no config found
    
    def set_max_values(self, max_hp):
        """Set maximum HP value"""
        self.max_hp = max_hp
    
    def get_threshold_info(self):
        """Get formatted threshold information for display"""
        return {
            'hp_critical': f"{self.hp_critical_threshold * 100}%",
            'hp_moderate': f"{self.hp_threshold * 100}%"
        }