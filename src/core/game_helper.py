import time
import pyautogui
import signal
import sys
from .config import GameConfig
from .debug_logger import DebugLogger
from .hotkey_manager import HotkeyManager
from ..processing.ocr_processor import OCRProcessor
from ..processing.region_manager import RegionManager
from ..monitors.health_monitor import HealthMonitor
from ..monitors.skinner import Skinner
from ..monitors.auto_haste import AutoHaste
from ..ui.overlay import GameOverlay


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
        
        # Initialize health monitor
        self.health_monitor = HealthMonitor(self.config, self.debug_logger)
        
        # Initialize skinner
        self.skinner = Skinner(self.config, self.debug_logger)
        
        # Initialize auto-haste
        self.auto_haste = AutoHaste(self.config, self.debug_logger)
        
        # Control flags
        self.running = True
        self.paused = False  # Bot paused state (toggled by F9)
        
        # Initialize hotkey manager (F9 only)
        self.hotkey_manager = HotkeyManager(self.config, self._on_toggle)
        
        # Initialize overlay (will be started later)
        self.overlay = None
        
        # Setup PyAutoGUI
        pyautogui.FAILSAFE = self.config.failsafe_enabled
        pyautogui.PAUSE = self.config.gui_pause
    
    def _on_toggle(self):
        """Callback when F9 is pressed to toggle bot state"""
        self.paused = not self.paused
        status = "ZATRZYMANY" if self.paused else "AKTYWNY"
        print(f"\n🎮 Bot {status} (F9)")
        self.debug_logger.log(f"TOGGLE: Bot state changed to {'PAUSED' if self.paused else 'ACTIVE'}")
    
    def _get_paused_state(self):
        """Get current paused state (for overlay)"""
        return self.paused
    
    def setup_game_values(self):
        """Setup max HP value"""
        try:
            max_hp_input = input(f"Enter max HP (default {self.config.DEFAULT_MAX_HP}): ").strip()
            max_hp = int(max_hp_input) if max_hp_input else self.config.DEFAULT_MAX_HP
            
        except ValueError:
            print("Invalid input, using default")
            max_hp = self.config.DEFAULT_MAX_HP
        
        self.config.set_max_values(max_hp)
        return max_hp
    
    def display_configuration(self):
        """Display current configuration"""
        thresholds = self.config.get_threshold_info()
        print(f"\nConfigured with Max HP: {self.config.max_hp}")
        print(f"🎮 CRITICAL-FIRST Healing Strategy:")
        print(f"   🚨 STEP 1: {self.config.critical_heal_key.upper()} (Critical): HP below {thresholds['hp_critical']} - CHECKED FIRST!")
        print(f"   💊 STEP 2: {self.config.heal_key.upper()} (Moderate): HP below {thresholds['hp_moderate']} - Only if not critical")
        print(f"⚡ Cooldown: {self.config.cooldown}s between key presses")
        print(f"🔄 Monitor frequency: Every {self.config.monitor_frequency} seconds - ENHANCED OCR!")
        print(f"🛡️ SAFETY: Critical healing is ALWAYS checked first to prevent death!")
        print(f"🎯 Toggle hotkey: {self.config.toggle_key.upper()} to pause/resume bot")
    
    def get_current_values(self):
        """Get current HP value from OCR"""
        regions = self.region_manager.get_regions()
        hp_value = self.ocr_processor.extract_number_with_fallback(regions['hp'], "hp")
        
        self.debug_logger.log(f"OCR_RESULTS: HP: {hp_value}")
        return hp_value
    
    def display_status(self, hp_value):
        """Display current status"""
        hp_status = self.health_monitor.get_hp_status(hp_value)
        
        pause_indicator = " [PAUSED]" if self.paused else ""
        status = f"HP: {hp_status['value'] or 'N/A'} ({hp_status['percentage']:.1f}%) [{hp_status['status']}]{pause_indicator}"
        print(status)
    
    def check_and_respond(self, hp_value):
        """Check HP value and respond with appropriate actions"""
        # Skip healing actions if paused
        if self.paused:
            self.debug_logger.log(f"DECISION: Bot is PAUSED - skipping healing check")
            return
        
        self.debug_logger.log(f"DECISION: Checking thresholds - HP: {hp_value}")
        
        # Check HP and heal if needed
        self.health_monitor.check_hp_and_heal(hp_value)
    
    def display_healing_summary(self):
        """Display healing usage summary"""
        summary = self.health_monitor.get_healing_summary()
        
        print("\n" + "="*50)
        print("🏥 HEALING SUMMARY")
        print("="*50)
        print(f"💊 Moderate heals used: {summary['moderate_heals']}")
        print(f"🚨 Critical heals used:  {summary['critical_heals']}")
        print(f"📊 Total heals used:     {summary['total_heals']}")
        print("="*50)
    
    def _monitoring_cycle(self):
        """Single monitoring cycle - called by overlay's after() scheduler"""
        if not self.running:
            return
        
        try:
            hp_value = self.get_current_values()
            self.display_status(hp_value)
            self.check_and_respond(hp_value)
        except pyautogui.FailSafeException:
            print("\nFail-safe triggered! Mouse moved to corner.")
            self.debug_logger.log_monitoring_stop("FAILSAFE")
            self.running = False
            if self.overlay:
                self.overlay.stop()
        except Exception as e:
            print(f"\nError in monitoring: {e}")
            self.debug_logger.log(f"ERROR: {str(e)}")
    
    def run_monitoring_loop(self):
        """Main monitoring loop with overlay"""
        print("\nStarting health monitoring... - ENHANCED OCR!")
        print("Detection indicators: ✓ = Detected, ✗ = Failed to detect")
        thresholds = self.config.get_threshold_info()
        print(f"🎮 Smart Healing: {self.config.critical_heal_key.upper()} (<{thresholds['hp_critical']} HP), {self.config.heal_key.upper()} ({thresholds['hp_critical']}-{thresholds['hp_moderate']} HP)")
        print("🛡️ Enhanced OCR: Multiple methods with intelligent fallback strategies")
        print("🔧 Corrupted OCR Recovery: Fixes common misreadings (S64→864, B72→872)")
        print("🛠️ Stability Protection: Requires confirmation for dramatic HP drops (prevents false critical healing)")
        print("⚡ Smart failure tracking: Warns after consecutive OCR failures")
        print(f"📝 Debug logging: Detailed OCR analysis saved to {self.config.debug_log_file}")
        print(f"🎯 Press {self.config.toggle_key.upper()} to pause/resume bot")
        print("Close overlay window or press Ctrl+C to quit")
        print()
        
        regions = self.region_manager.get_regions()
        self.debug_logger.log_monitoring_start(regions)
        
        # Start hotkey listener, skinner, and auto-haste
        self.hotkey_manager.start()
        self.skinner.start()
        self.auto_haste.start()
        
        try:
            if self.config.overlay_enabled:
                # Create overlay and run with integrated monitoring
                self.overlay = GameOverlay(
                    self.config, 
                    self.health_monitor, 
                    self._get_paused_state,
                    self.skinner,
                    self.auto_haste
                )
                # This blocks until overlay is closed
                self.overlay.run_with_monitoring(self._monitoring_cycle)
            else:
                # Run without overlay (fallback mode)
                while self.running:
                    self._monitoring_cycle()
                    time.sleep(self.config.monitor_frequency)
        except KeyboardInterrupt:
            print("\nStopped by user")
            self.debug_logger.log_monitoring_stop("USER")
        finally:
            self.running = False
            self.hotkey_manager.stop()
            self.skinner.stop()
            self.auto_haste.stop()
        
        # Display healing summary before exit
        self.display_healing_summary()
        print("Health monitor stopped.")
    
    def run(self):
        """Main entry point - auto-starts using config.json values"""
        print("=== Health Monitor ===")
        print(f"Max HP: {self.config.max_hp}")
        self.display_configuration()
        
        # Try to load saved regions
        if not self.region_manager.load_saved_regions():
            print("⚠️  No saved regions found. Run from terminal first to set up regions.")
            print("   python3 main.py")
            return
        
        # Show regions being used
        regions = self.region_manager.get_regions()
        print(f"📍 Using saved region: HP{regions['hp']}")
        
        # Start monitoring immediately
        self.run_monitoring_loop()


def main():
    """Main function"""
    game_helper = GameHelper()
    game_helper.run()


if __name__ == "__main__":
    main()