import time
import pyautogui
from .config import GameConfig
from .debug_logger import DebugLogger
from ..processing.ocr_processor import OCRProcessor
from ..processing.region_manager import RegionManager
from ..monitors.health_monitor import HealthMonitor
from ..monitors.mana_monitor import ManaMonitor


class GameHelper:
    def __init__(self):
        # Initialize configuration
        self.config = GameConfig()
        
        # Initialize debug logger
        self.debug_logger = DebugLogger(self.config)
        
        # Initialize OCR processor
        self.ocr_processor = OCRProcessor(self.config, self.debug_logger)
        
        # Initialize region manager
        self.region_manager = RegionManager(self.config, self.debug_logger, self.ocr_processor)
        
        # Initialize monitors
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
        self.mana_monitor = ManaMonitor(self.config, self.debug_logger)
        
        # Control flags
        self.running = True
        
        # Setup PyAutoGUI
        pyautogui.FAILSAFE = self.config.failsafe_enabled
        pyautogui.PAUSE = self.config.gui_pause
    
    def setup_game_values(self):
        """Setup max HP and Mana values"""
        try:
            max_hp_input = input(f"Enter max HP (default {self.config.DEFAULT_MAX_HP}): ").strip()
            max_mana_input = input(f"Enter max mana (default {self.config.DEFAULT_MAX_MANA}): ").strip()
            
            max_hp = int(max_hp_input) if max_hp_input else self.config.DEFAULT_MAX_HP
            max_mana = int(max_mana_input) if max_mana_input else self.config.DEFAULT_MAX_MANA
            
        except ValueError:
            print("Invalid input, using defaults")
            max_hp = self.config.DEFAULT_MAX_HP
            max_mana = self.config.DEFAULT_MAX_MANA
        
        self.config.set_max_values(max_hp, max_mana)
        return max_hp, max_mana
    
    def display_configuration(self):
        """Display current configuration"""
        thresholds = self.config.get_threshold_info()
        print(f"\nConfigured with Max HP: {self.config.max_hp}, Max Mana: {self.config.max_mana}")
        print(f"🎮 Smart Healing Strategy:")
        print(f"   🚨 {self.config.critical_heal_key.upper()} (Critical): HP below {thresholds['hp_critical']}")
        print(f"   💊 {self.config.heal_key.upper()} (Moderate): HP below {thresholds['hp_moderate']} (but above {thresholds['hp_critical']})")
        print(f"   💙 {self.config.mana_key.upper()} (Mana): Mana below {thresholds['mana']}")
        print(f"⚡ Cooldown: {self.config.cooldown}s between key presses")
        print(f"🔄 Monitor frequency: Every {self.config.monitor_frequency} seconds - ENHANCED OCR!")
    
    def get_current_values(self):
        """Get current HP and Mana values from OCR"""
        regions = self.region_manager.get_regions()
        hp_value = self.ocr_processor.extract_number_with_fallback(regions['hp'], "hp")
        mana_value = self.ocr_processor.extract_number_with_fallback(regions['mana'], "mana")
        
        self.debug_logger.log(f"OCR_RESULTS: HP: {hp_value}, Mana: {mana_value}")
        return hp_value, mana_value
    
    def display_status(self, hp_value, mana_value):
        """Display current status"""
        hp_status = self.health_monitor.get_hp_status(hp_value)
        mana_status = self.mana_monitor.get_mana_status(mana_value)
        
        status = f"HP: {hp_status['value'] or 'N/A'} ({hp_status['percentage']:.1f}%) [{hp_status['status']}] | Mana: {mana_status['value'] or 'N/A'} ({mana_status['percentage']:.1f}%) [{mana_status['status']}]"
        print(status)
    
    def check_and_respond(self, hp_value, mana_value):
        """Check values and respond with appropriate actions"""
        self.debug_logger.log(f"DECISION: Checking thresholds - HP: {hp_value}, Mana: {mana_value}")
        
        # Check HP and heal if needed
        self.health_monitor.check_hp_and_heal(hp_value)
        
        # Check Mana and restore if needed
        self.mana_monitor.check_mana_and_restore(mana_value)
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        print("\nStarting region-based game helper... - ENHANCED OCR!")
        print("Detection indicators: ✓ = Detected, ✗ = Failed to detect")
        thresholds = self.config.get_threshold_info()
        print(f"🎮 Smart Healing: {self.config.critical_heal_key.upper()} (<{thresholds['hp_critical']} HP), {self.config.heal_key.upper()} ({thresholds['hp_critical']}-{thresholds['hp_moderate']} HP), {self.config.mana_key.upper()} (<{thresholds['mana']} Mana)")
        print("🛡️ Enhanced OCR: Multiple methods with intelligent fallback strategies")
        print("🔧 Corrupted OCR Recovery: Fixes common misreadings (S64→864, B72→872)")
        print("🛠️ Stability Protection: Requires confirmation for dramatic HP drops (prevents false critical healing)")
        print("⚡ Smart failure tracking: Warns after consecutive OCR failures")
        print(f"📝 Debug logging: Detailed OCR analysis saved to {self.config.debug_log_file}")
        print("Press Ctrl+C to quit")
        print()
        
        regions = self.region_manager.get_regions()
        self.debug_logger.log_monitoring_start(regions)
        
        try:
            while self.running:
                hp_value, mana_value = self.get_current_values()
                self.display_status(hp_value, mana_value)
                self.check_and_respond(hp_value, mana_value)
                
                time.sleep(self.config.monitor_frequency)
                
        except KeyboardInterrupt:
            print("\nStopped by user")
            self.debug_logger.log_monitoring_stop("USER")
        except pyautogui.FailSafeException:
            print("\nFail-safe triggered! Mouse moved to corner.")
            self.debug_logger.log_monitoring_stop("FAILSAFE")
        except Exception as e:
            print(f"\nError: {e}")
            self.debug_logger.log_monitoring_stop(f"ERROR: {str(e)}")
        
        print("Game helper stopped.")
    
    def run(self):
        """Main entry point"""
        print("=== Game Helper ===")
        print("This tool monitors your game's HP and Mana values and automatically presses hotkeys.")
        print()
        
        # Try to load saved regions first
        if self.region_manager.load_saved_regions():
            # Setup game values
            max_hp, max_mana = self.setup_game_values()
            self.display_configuration()
            
            # Show regions being used
            regions = self.region_manager.get_regions()
            print(f"📍 Using saved regions: HP{regions['hp']}, Mana{regions['mana']}")
            
            input("\nPress Enter to start monitoring...")
            self.run_monitoring_loop()
            return
        
        # Manual setup if no saved regions
        max_hp, max_mana = self.setup_game_values()
        self.display_configuration()
        
        # Setup regions interactively
        self.region_manager.setup_regions()
        
        input("\nPress Enter to start monitoring...")
        self.run_monitoring_loop()


def main():
    """Main function"""
    game_helper = GameHelper()
    game_helper.run()


if __name__ == "__main__":
    main() 