import datetime
import os


class DebugLogger:
    def __init__(self, config):
        self.config = config
        self.log_file = config.debug_log_file
        self.enabled = config.enable_debug
        self.init_log()
    
    def init_log(self):
        """Initialize debug log file"""
        if self.enabled:
            try:
                with open(self.log_file, 'w') as f:
                    f.write(f"=== Game Helper Debug Log Started ===\n")
                    f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Max HP: {self.config.max_hp}, Max Mana: {self.config.max_mana}\n")
                    thresholds = self.config.get_threshold_info()
                    f.write(f"Thresholds: HP Critical={thresholds['hp_critical']}, HP Moderate={thresholds['hp_moderate']}, Mana={thresholds['mana']}\n")
                    f.write(f"Cooldown: {self.config.cooldown}s\n")
                    f.write("="*50 + "\n\n")
                print(f"📝 Debug logging enabled: {self.log_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize debug log: {e}")
                self.enabled = False
    
    def log(self, message):
        """Write debug message to log file with timestamp"""
        if not self.enabled:
            return
        try:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            pass  # Silently fail to avoid disrupting the main flow
    
    def log_section(self, section_name):
        """Log a section separator"""
        self.log(f"=== {section_name} ===")
    
    def log_monitoring_start(self, regions):
        """Log monitoring start information"""
        self.log_section("MONITORING STARTED")
        self.log(f"Monitor frequency: Every {self.config.monitor_frequency} seconds")
        self.log(f"Regions: HP{regions.get('hp')}, Mana{regions.get('mana')}")
    
    def log_monitoring_stop(self, reason="USER"):
        """Log monitoring stop information"""
        self.log_section(f"MONITORING STOPPED BY {reason}")
        self.log("=== SESSION ENDED ===\n") 