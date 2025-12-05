"""
Skinner - Right-click to hotkey functionality

Listens for right mouse button clicks and presses configured hotkey.
Toggle with button in overlay.
"""

import random
import time
from pynput import mouse, keyboard


def get_key_from_string(key_string: str):
    """Convert string to pynput key object."""
    key_string = key_string.lower()
    
    # Function key mapping
    function_keys = {
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
        "space": keyboard.Key.space,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "escape": keyboard.Key.esc,
        "esc": keyboard.Key.esc,
    }
    
    if key_string in function_keys:
        return function_keys[key_string]
    
    # For single characters
    if len(key_string) == 1:
        return key_string
    
    return keyboard.Key.f3  # Default to F3


class Skinner:
    """Right-click to hotkey - 'skins' monsters automatically"""
    
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        self.keyboard_controller = keyboard.Controller()
        
        self.enabled = False  # Starts disabled
        self._running = False
        self.listener = None
        
        # Statistics
        self.click_count = 0
    
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def toggle(self):
        """Toggle skinner on/off"""
        self.enabled = not self.enabled
        status = "WŁĄCZONY" if self.enabled else "WYŁĄCZONY"
        print(f"\n🔪 Skinner {status}")
        self.debug_log(f"SKINNER: Toggled to {'ENABLED' if self.enabled else 'DISABLED'}")
        return self.enabled
    
    def _on_click(self, x, y, button, pressed):
        """Handle mouse clicks"""
        # Only react to right button press (not release) and if enabled
        if button == mouse.Button.right and pressed and self.enabled:
            # Random delay
            delay = random.uniform(
                self.config.skinner_min_delay, 
                self.config.skinner_max_delay
            )
            time.sleep(delay)
            
            # Get target key
            target_key = get_key_from_string(self.config.skinner_hotkey)
            
            # Press the key
            self.keyboard_controller.press(target_key)
            self.keyboard_controller.release(target_key)
            
            self.click_count += 1
            self.debug_log(f"SKINNER: Right-click → {self.config.skinner_hotkey.upper()} (delay: {delay:.3f}s)")
            print(f"🔪 Prawy przycisk → {self.config.skinner_hotkey.upper()} (opóźnienie: {delay:.3f}s)")
    
    def start(self):
        """Start the skinner listener in background thread"""
        if self._running:
            return
        
        self._running = True
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
        print(f"🔪 Skinner gotowy - kliknij przycisk w overlay aby włączyć")
        print(f"   Klawisz: {self.config.skinner_hotkey.upper()}, Opóźnienie: {self.config.skinner_min_delay}s-{self.config.skinner_max_delay}s")
    
    def stop(self):
        """Stop the skinner listener"""
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("🔪 Skinner zatrzymany")
    
    def is_running(self):
        """Check if listener is running"""
        return self._running
    
    def is_enabled(self):
        """Check if skinner is enabled (responding to clicks)"""
        return self.enabled
    
    def get_stats(self):
        """Get statistics"""
        return {
            'enabled': self.enabled,
            'click_count': self.click_count
        }
