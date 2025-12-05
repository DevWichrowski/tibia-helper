"""
Game Overlay - Draggable, semi-transparent panel for displaying healer status

Uses tkinter to create a game-style overlay panel that shows:
- Bot status (active/paused)
- Skinner status with toggle button
- HP thresholds
- Heal counters (normal and critical)
- Compact hotkey list

IMPORTANT: On macOS, tkinter MUST run on the main thread.
"""

import tkinter as tk


class GameOverlay:
    def __init__(self, config, health_monitor, get_paused_callback, skinner=None):
        self.config = config
        self.health_monitor = health_monitor
        self.get_paused = get_paused_callback
        self.skinner = skinner
        
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
        self.skinner_btn = None
        self.skinner_clicks_label = None
        self.normal_heals_label = None
        self.critical_heals_label = None
    
    def _create_window(self):
        """Create the overlay window"""
        self.root = tk.Tk()
        self.root.title("Healer Panel")
        
        # Window configuration
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.9)
        
        # Position window in top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 280}+50")
        
        # Main frame with game-style border
        main_frame = tk.Frame(
            self.root,
            bg='#1a1a2e',
            highlightbackground='#c9a227',
            highlightthickness=2,
            padx=12,
            pady=8
        )
        main_frame.pack(fill='both', expand=True)
        
        # Enable dragging
        main_frame.bind('<Button-1>', self._start_drag)
        main_frame.bind('<B1-Motion>', self._on_drag)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🛡️ HEALER PANEL",
            font=('Helvetica', 13, 'bold'),
            fg='#c9a227',
            bg='#1a1a2e'
        )
        title_label.pack(pady=(0, 5))
        title_label.bind('<Button-1>', self._start_drag)
        title_label.bind('<B1-Motion>', self._on_drag)
        
        # Separator
        tk.Frame(main_frame, height=2, bg='#c9a227').pack(fill='x', pady=3)
        
        # Bot Status
        status_frame = tk.Frame(main_frame, bg='#1a1a2e')
        status_frame.pack(fill='x', pady=2)
        
        tk.Label(
            status_frame, text="Bot:", font=('Helvetica', 10),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.status_indicator = tk.Label(
            status_frame, text="● AKTYWNY", font=('Helvetica', 10, 'bold'),
            fg='#00ff88', bg='#1a1a2e'
        )
        self.status_indicator.pack(side='left', padx=(5, 0))
        
        # Skinner toggle button
        if self.skinner:
            skinner_frame = tk.Frame(main_frame, bg='#1a1a2e')
            skinner_frame.pack(fill='x', pady=2)
            
            tk.Label(
                skinner_frame, text="🔪 Skinner:", font=('Helvetica', 10),
                fg='#a0a0a0', bg='#1a1a2e'
            ).pack(side='left')
            
            self.skinner_btn = tk.Button(
                skinner_frame,
                text="OFF",
                font=('Helvetica', 9, 'bold'),
                fg='#ffffff',
                bg='#8b0000',
                activebackground='#a52a2a',
                relief='flat',
                padx=8,
                pady=1,
                cursor='hand2',
                command=self._toggle_skinner
            )
            self.skinner_btn.pack(side='left', padx=(5, 0))
            
            self.skinner_clicks_label = tk.Label(
                skinner_frame, text="(0)", font=('Helvetica', 9),
                fg='#ffaa00', bg='#1a1a2e'
            )
            self.skinner_clicks_label.pack(side='left', padx=(5, 0))
        
        # Separator
        tk.Frame(main_frame, height=1, bg='#444').pack(fill='x', pady=4)
        
        # HP Thresholds (compact)
        thresh_frame = tk.Frame(main_frame, bg='#1a1a2e')
        thresh_frame.pack(fill='x', pady=1)
        
        tk.Label(
            thresh_frame, text=f"HP: {int(self.config.hp_threshold * 100)}%",
            font=('Helvetica', 9), fg='#4da6ff', bg='#1a1a2e'
        ).pack(side='left')
        
        tk.Label(
            thresh_frame, text=f"  Crit: {int(self.config.hp_critical_threshold * 100)}%",
            font=('Helvetica', 9), fg='#ff6b6b', bg='#1a1a2e'
        ).pack(side='left')
        
        # Separator
        tk.Frame(main_frame, height=1, bg='#444').pack(fill='x', pady=4)
        
        # Stats section
        tk.Label(
            main_frame, text="STATISTICS", font=('Helvetica', 9, 'bold'),
            fg='#c9a227', bg='#1a1a2e'
        ).pack(pady=(0, 3))
        
        # Normal heals
        normal_frame = tk.Frame(main_frame, bg='#1a1a2e')
        normal_frame.pack(fill='x', pady=1)
        
        tk.Label(
            normal_frame, text="💊 Heals:", font=('Helvetica', 9),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.normal_heals_label = tk.Label(
            normal_frame, text="0", font=('Helvetica', 9, 'bold'),
            fg='#00ff88', bg='#1a1a2e'
        )
        self.normal_heals_label.pack(side='right')
        
        # Critical heals
        critical_frame = tk.Frame(main_frame, bg='#1a1a2e')
        critical_frame.pack(fill='x', pady=1)
        
        tk.Label(
            critical_frame, text="🚨 Critical:", font=('Helvetica', 9),
            fg='#a0a0a0', bg='#1a1a2e'
        ).pack(side='left')
        
        self.critical_heals_label = tk.Label(
            critical_frame, text="0", font=('Helvetica', 9, 'bold'),
            fg='#ff6b6b', bg='#1a1a2e'
        )
        self.critical_heals_label.pack(side='right')
        
        # Separator
        tk.Frame(main_frame, height=1, bg='#444').pack(fill='x', pady=4)
        
        # Hotkeys section (compact)
        hotkeys_frame = tk.Frame(main_frame, bg='#1a1a2e')
        hotkeys_frame.pack(fill='x', pady=1)
        
        hotkey_text = f"F9:bot  F10:skin  {self.config.heal_key.upper()}:heal  {self.config.critical_heal_key.upper()}:crit"
        
        tk.Label(
            hotkeys_frame, text=hotkey_text,
            font=('Helvetica', 8), fg='#666666', bg='#1a1a2e'
        ).pack()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _toggle_skinner(self):
        """Toggle skinner on/off"""
        if self.skinner:
            self.skinner.toggle()
            self._update_skinner_btn()
    
    def _update_skinner_btn(self):
        """Update skinner button appearance"""
        if self.skinner and self.skinner_btn:
            if self.skinner.is_enabled():
                self.skinner_btn.config(text="ON", bg='#006400', activebackground='#228b22')
            else:
                self.skinner_btn.config(text="OFF", bg='#8b0000', activebackground='#a52a2a')
    
    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def _on_close(self):
        self._stop_requested = True
        self.stop()
    
    def _update_display(self):
        """Update the overlay display"""
        if not self._running or not self.root or self._stop_requested:
            return
        
        try:
            # Update bot status with error checking
            is_paused = self.get_paused()
            error_status = self.health_monitor.get_error_status()
            
            if error_status['is_warning']:
                # Critical error - many OCR failures
                self.status_indicator.config(text="● BŁĄD OCR", fg='#ff0000')
            elif error_status['has_error']:
                # Minor error - some OCR failures
                self.status_indicator.config(text="● WYKRYWANIE...", fg='#ffaa00')
            elif is_paused:
                self.status_indicator.config(text="● STOP", fg='#ff6b6b')
            else:
                self.status_indicator.config(text="● AKTYWNY", fg='#00ff88')
            
            # Update skinner
            if self.skinner:
                self._update_skinner_btn()
                stats = self.skinner.get_stats()
                self.skinner_clicks_label.config(text=f"({stats['click_count']})")
            
            # Update heal counters
            summary = self.health_monitor.get_healing_summary()
            self.normal_heals_label.config(text=str(summary['moderate_heals']))
            self.critical_heals_label.config(text=str(summary['critical_heals']))
            
            self.root.after(100, self._update_display)
        except tk.TclError:
            pass
    
    def _run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        if not self._running or self._stop_requested:
            return
        
        try:
            if self._monitoring_callback:
                self._monitoring_callback()
            
            monitor_ms = int(self.config.monitor_frequency * 1000)
            self.root.after(monitor_ms, self._run_monitoring_cycle)
        except tk.TclError:
            pass
    
    def run_with_monitoring(self, monitoring_callback):
        """Run overlay on main thread with integrated monitoring"""
        self._monitoring_callback = monitoring_callback
        self._running = True
        self._stop_requested = False
        
        self._create_window()
        print("🖥️  Overlay panel started")
        
        self._update_display()
        self._run_monitoring_cycle()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            print("🖥️  Overlay panel stopped")
    
    def stop(self):
        """Stop the overlay"""
        self._stop_requested = True
        self._running = False
        if self.root:
            try:
                self.root.after(0, self._do_quit)
            except:
                pass
    
    def _do_quit(self):
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        self.root = None
    
    def is_running(self):
        return self._running and not self._stop_requested

