"""
Auto-Haste - Automatic haste spell casting

Periodically presses the configured haste hotkey to maintain the buff.
Toggle with button in overlay.
"""

import random
import time
import threading
from pynput import keyboard


class AutoHaste:
    """Automatically casts haste spell at regular intervals"""
    
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        self.keyboard_controller = keyboard.Controller()
        
        self.enabled = False
        self._running = False
        self._thread = None
        
        # Statistics
        self.cast_count = 0
        self.last_cast_time = 0
    
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def toggle(self):
        """Toggle auto-haste on/off"""
        self.enabled = not self.enabled
        status = "WŁĄCZONY" if self.enabled else "WYŁĄCZONY"
        print(f"\n⚡ Auto-Haste {status}")
        self.debug_log(f"AUTO_HASTE: Toggled to {'ENABLED' if self.enabled else 'DISABLED'}")
        
        if self.enabled:
            # Cast immediately when enabled
            self._cast_haste()
        
        return self.enabled
    
    def _cast_haste(self):
        """Cast the haste spell"""
        key = self.config.haste_hotkey.lower()
        
        # Press the key
        if len(key) == 1:
            self.keyboard_controller.press(key)
            self.keyboard_controller.release(key)
        else:
            # Handle special keys if needed
            self.keyboard_controller.press(key)
            self.keyboard_controller.release(key)
        
        self.cast_count += 1
        self.last_cast_time = time.time()
        self.debug_log(f"AUTO_HASTE: Cast haste ({self.config.haste_hotkey.upper()})")
        print(f"⚡ Auto-Haste: {self.config.haste_hotkey.upper()} pressed")
    
    def _haste_loop(self):
        """Background loop that casts haste periodically"""
        while self._running:
            if self.enabled:
                # Random delay between min and max
                delay = random.uniform(
                    self.config.haste_min_interval,
                    self.config.haste_max_interval
                )
                
                # Wait in small increments to check for stop
                wait_time = 0
                while wait_time < delay and self._running and self.enabled:
                    time.sleep(0.5)
                    wait_time += 0.5
                
                # Cast if still enabled and running
                if self._running and self.enabled:
                    self._cast_haste()
            else:
                time.sleep(0.5)
    
    def start(self):
        """Start the auto-haste thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._haste_loop, daemon=True)
        self._thread.start()
        print(f"⚡ Auto-Haste gotowy - kliknij przycisk w overlay aby włączyć")
        print(f"   Klawisz: {self.config.haste_hotkey.upper()}, Interwał: {self.config.haste_min_interval}-{self.config.haste_max_interval}s")
    
    def stop(self):
        """Stop the auto-haste thread"""
        self._running = False
        self.enabled = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None
        print("⚡ Auto-Haste zatrzymany")
    
    def is_running(self):
        """Check if thread is running"""
        return self._running
    
    def is_enabled(self):
        """Check if auto-haste is enabled"""
        return self.enabled
    
    def get_stats(self):
        """Get statistics"""
        return {
            'enabled': self.enabled,
            'cast_count': self.cast_count
        }
