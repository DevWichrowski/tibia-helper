"""
Game Overlay - Draggable, semi-transparent panel for displaying healer status

Uses tkinter to create a game-style overlay panel that shows:
- Bot status (active/paused)
- HP thresholds
- Heal counters (normal and critical)

IMPORTANT: On macOS, tkinter MUST run on the main thread.
This module is designed to run tkinter mainloop on main thread,
with monitoring running as scheduled callbacks.
"""

import tkinter as tk
import threading
import time


class GameOverlay:
    def __init__(self, config, health_monitor, get_paused_callback):
        self.config = config
        self.health_monitor = health_monitor
        self.get_paused = get_paused_callback
        
        self.root = None
        self._running = False
        self._stop_requested = False
        
        # Monitoring callback
        self._monitoring_callback = None
        
        # Dragging state
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # UI elements
        self.status_indicator = None
        self.normal_heals_label = None
        self.critical_heals_label = None
    
    def _create_window(self):
        """Create the overlay window"""
        self.root = tk.Tk()
        self.root.title("Healer Panel")
        
        # Window configuration
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.9)  # Semi-transparent
        
        # Position window in top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 280}+50")
        
        # Main frame with game-style border
        main_frame = tk.Frame(
            self.root,
            bg='#1a1a2e',  # Dark blue-black background
            highlightbackground='#c9a227',  # Gold border
            highlightthickness=2,
            padx=15,
            pady=10
        )
        main_frame.pack(fill='both', expand=True)
        
        # Enable dragging on main frame
        main_frame.bind('<Button-1>', self._start_drag)
        main_frame.bind('<B1-Motion>', self._on_drag)
        
        # Title with icon
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill='x', pady=(0, 8))
        
        title_label = tk.Label(
            title_frame,
            text="🛡️ HEALER PANEL",
            font=('Helvetica', 14, 'bold'),
            fg='#c9a227',  # Gold text
            bg='#1a1a2e'
        )
        title_label.pack()
        title_label.bind('<Button-1>', self._start_drag)
        title_label.bind('<B1-Motion>', self._on_drag)
        
        # Separator
        tk.Frame(main_frame, height=2, bg='#c9a227').pack(fill='x', pady=5)
        
        # Status section
        status_frame = tk.Frame(main_frame, bg='#1a1a2e')
        status_frame.pack(fill='x', pady=3)
        
        tk.Label(
            status_frame, text="Status:", font=('Helvetica', 11),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.status_indicator = tk.Label(
            status_frame, text="● AKTYWNY", font=('Helvetica', 11, 'bold'),
            fg='#00ff88', bg='#1a1a2e'
        )
        self.status_indicator.pack(side='left', padx=(5, 0))
        
        # HP Threshold
        threshold_frame = tk.Frame(main_frame, bg='#1a1a2e')
        threshold_frame.pack(fill='x', pady=2)
        
        tk.Label(
            threshold_frame, text="HP Threshold:", font=('Helvetica', 10),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        tk.Label(
            threshold_frame, text=f"{int(self.config.hp_threshold * 100)}%",
            font=('Helvetica', 10, 'bold'), fg='#4da6ff', bg='#1a1a2e'
        ).pack(side='left', padx=(5, 0))
        
        # Critical Threshold
        critical_frame = tk.Frame(main_frame, bg='#1a1a2e')
        critical_frame.pack(fill='x', pady=2)
        
        tk.Label(
            critical_frame, text="Critical Threshold:", font=('Helvetica', 10),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        tk.Label(
            critical_frame, text=f"{int(self.config.hp_critical_threshold * 100)}%",
            font=('Helvetica', 10, 'bold'), fg='#ff6b6b', bg='#1a1a2e'
        ).pack(side='left', padx=(5, 0))
        
        # Separator
        tk.Frame(main_frame, height=2, bg='#c9a227').pack(fill='x', pady=8)
        
        # Heal counters section
        tk.Label(
            main_frame, text="HEAL STATISTICS", font=('Helvetica', 10, 'bold'),
            fg='#c9a227', bg='#1a1a2e'
        ).pack(pady=(0, 5))
        
        # Normal heals
        normal_frame = tk.Frame(main_frame, bg='#1a1a2e')
        normal_frame.pack(fill='x', pady=2)
        
        tk.Label(
            normal_frame, text="💊 Normal heals:", font=('Helvetica', 10),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.normal_heals_label = tk.Label(
            normal_frame, text="0", font=('Helvetica', 10, 'bold'),
            fg='#00ff88', bg='#1a1a2e'
        )
        self.normal_heals_label.pack(side='right')
        
        # Critical heals
        critical_heals_frame = tk.Frame(main_frame, bg='#1a1a2e')
        critical_heals_frame.pack(fill='x', pady=2)
        
        tk.Label(
            critical_heals_frame, text="🚨 Critical heals:", font=('Helvetica', 10),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.critical_heals_label = tk.Label(
            critical_heals_frame, text="0", font=('Helvetica', 10, 'bold'),
            fg='#ff6b6b', bg='#1a1a2e'
        )
        self.critical_heals_label.pack(side='right')
        
        # Hotkey hint
        tk.Label(
            main_frame, text="Press F9 to toggle", font=('Helvetica', 8),
            fg='#666666', bg='#1a1a2e'
        ).pack(pady=(10, 0))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _start_drag(self, event):
        """Start dragging the window"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        """Handle window dragging"""
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def _on_close(self):
        """Handle window close request"""
        self._stop_requested = True
        self.stop()
    
    def _update_display(self):
        """Update the overlay display with current values"""
        if not self._running or not self.root or self._stop_requested:
            return
        
        try:
            # Update status indicator
            is_paused = self.get_paused()
            if is_paused:
                self.status_indicator.config(text="● ZATRZYMANY", fg='#ff6b6b')
            else:
                self.status_indicator.config(text="● AKTYWNY", fg='#00ff88')
            
            # Update heal counters
            summary = self.health_monitor.get_healing_summary()
            self.normal_heals_label.config(text=str(summary['moderate_heals']))
            self.critical_heals_label.config(text=str(summary['critical_heals']))
            
            # Schedule next update (100ms)
            self.root.after(100, self._update_display)
        except tk.TclError:
            # Window was closed
            pass
    
    def _run_monitoring_cycle(self):
        """Run one cycle of monitoring (called from main thread via after())"""
        if not self._running or self._stop_requested:
            return
        
        try:
            # Call the monitoring callback if set
            if self._monitoring_callback:
                self._monitoring_callback()
            
            # Schedule next monitoring cycle (50ms = 20Hz matching config)
            monitor_ms = int(self.config.monitor_frequency * 1000)
            self.root.after(monitor_ms, self._run_monitoring_cycle)
        except tk.TclError:
            pass
    
    def run_with_monitoring(self, monitoring_callback):
        """
        Run overlay on main thread with integrated monitoring.
        This must be called from the main thread!
        
        Args:
            monitoring_callback: Function to call for each monitoring cycle
        """
        self._monitoring_callback = monitoring_callback
        self._running = True
        self._stop_requested = False
        
        # Create the window (on main thread)
        self._create_window()
        print("🖥️  Overlay panel started")
        
        # Start the display update loop
        self._update_display()
        
        # Start the monitoring loop
        self._run_monitoring_cycle()
        
        # Run tkinter mainloop (blocks until window closed)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            print("🖥️  Overlay panel stopped")
    
    def stop(self):
        """Stop the overlay (can be called from any thread)"""
        self._stop_requested = True
        self._running = False
        if self.root:
            try:
                # Schedule quit on main thread
                self.root.after(0, self._do_quit)
            except:
                pass
    
    def _do_quit(self):
        """Actually quit (must run on main thread)"""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        self.root = None
    
    def is_running(self):
        """Check if overlay is running"""
        return self._running and not self._stop_requested
