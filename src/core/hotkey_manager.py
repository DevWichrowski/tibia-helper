"""
Hotkey Manager - Global hotkey handling for bot control

Uses pynput to listen for global keyboard events.
F9 toggles the bot on/off.
"""

import threading
from pynput import keyboard


class HotkeyManager:
    def __init__(self, config, on_toggle_callback=None):
        self.config = config
        self.on_toggle_callback = on_toggle_callback
        self.listener = None
        self._running = False
        
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            # Check if it's the toggle key (F9)
            if key == keyboard.Key.f9:
                if self.on_toggle_callback:
                    self.on_toggle_callback()
        except AttributeError:
            # Regular key, not a special key
            pass
    
    def start(self):
        """Start listening for hotkeys in background thread"""
        if self._running:
            return
            
        self._running = True
        self.listener = keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()
        print("🎮 Hotkey listener started - Press F9 to toggle bot ON/OFF")
    
    def stop(self):
        """Stop the hotkey listener"""
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("🎮 Hotkey listener stopped")
    
    def is_running(self):
        """Check if listener is running"""
        return self._running
