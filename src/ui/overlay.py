"""
Game Overlay - Draggable, semi-transparent panel for displaying healer status

Uses tkinter to create a game-style overlay panel that shows:
- Bot status (active/paused)
- Skinner status with toggle button
- Auto-Haste status with toggle button
- HP thresholds
- Heal counters (normal and critical)
- Compact hotkey list

IMPORTANT: On macOS, tkinter MUST run on the main thread.
"""

import tkinter as tk


class GameOverlay:
    def __init__(self, config, health_monitor, get_paused_callback, skinner=None, auto_haste=None):
        self.config = config
        self.health_monitor = health_monitor
        self.get_paused = get_paused_callback
        self.skinner = skinner
        self.auto_haste = auto_haste
        
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
        self.haste_btn = None
        self.haste_casts_label = None
        self.heal_btn = None
        self.normal_heals_label = None
        self.critical_btn = None
        self.critical_heals_label = None
    
    def _create_window(self):
        """Create the overlay window - Tibia style"""
        self.root = tk.Tk()
        self.root.title("Healer")
        
        # Tibia color scheme
        BG_DARK = '#404040'
        BG_DARKER = '#353535'
        BG_TITLE = '#505050'
        BORDER = '#606060'
        TEXT_BEIGE = '#c0b090'
        TEXT_DIM = '#707070'
        GREEN = '#00c000'
        RED = '#c00000'
        ORANGE = '#ff8800'
        BLUE = '#4080ff'
        GOLD = '#d4a017'
        
        # Window configuration
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 230}+100")
        
        # Outer border
        outer_frame = tk.Frame(self.root, bg=BORDER, padx=1, pady=1)
        outer_frame.pack(fill='both', expand=True)
        
        main_frame = tk.Frame(outer_frame, bg=BG_DARK)
        main_frame.pack(fill='both', expand=True)
        
        # === Title Bar ===
        title_frame = tk.Frame(main_frame, bg=BG_TITLE, height=20)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🛡️", font=('Arial', 10),
                 fg=GOLD, bg=BG_TITLE).pack(side='left', padx=(4, 2))
        
        title_label = tk.Label(title_frame, text="Healer Bot",
                               font=('Arial', 9, 'bold'), fg=TEXT_BEIGE, bg=BG_TITLE)
        title_label.pack(side='left')
        
        close_btn = tk.Label(title_frame, text="✕", font=('Arial', 10),
                             fg=TEXT_DIM, bg=BG_TITLE, cursor='hand2')
        close_btn.pack(side='right', padx=(0, 4))
        close_btn.bind('<Button-1>', lambda e: self._on_close())
        close_btn.bind('<Enter>', lambda e: close_btn.config(fg=RED))
        close_btn.bind('<Leave>', lambda e: close_btn.config(fg=TEXT_DIM))
        
        title_frame.bind('<Button-1>', self._start_drag)
        title_frame.bind('<B1-Motion>', self._on_drag)
        title_label.bind('<Button-1>', self._start_drag)
        title_label.bind('<B1-Motion>', self._on_drag)
        
        # === Content ===
        content = tk.Frame(main_frame, bg=BG_DARK, padx=24, pady=6)
        content.pack(fill='both', expand=True)
        
        # --- Status Row ---
        status_row = tk.Frame(content, bg=BG_DARK)
        status_row.pack(fill='x', pady=2)
        
        tk.Label(status_row, text="⚡ Status:", font=('Arial', 9),
                 fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
        
        self.status_indicator = tk.Label(status_row, text="ACTIVE",
                                         font=('Arial', 9, 'bold'), fg=GREEN, bg=BG_DARK)
        self.status_indicator.pack(side='right')
        
        # --- Separator ---
        tk.Frame(content, height=1, bg=BORDER).pack(fill='x', pady=4)
        
        # ========== FEATURES SECTION ==========
        feat_title = tk.Frame(content, bg=BG_DARKER, padx=4, pady=2)
        feat_title.pack(fill='x', pady=(0, 3))
        tk.Label(feat_title, text="⚙️ Features", font=('Arial', 8, 'bold'),
                 fg=GOLD, bg=BG_DARKER).pack(side='left')
        
        # Heal toggle with %
        heal_row = tk.Frame(content, bg=BG_DARK)
        heal_row.pack(fill='x', pady=1)
        
        tk.Label(heal_row, text=f"  💊 Heal (<{int(self.config.hp_threshold*100)}%):",
                 font=('Arial', 9), fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
        
        self.heal_btn = tk.Label(heal_row, text="[ON]", font=('Arial', 9, 'bold'),
                                 fg=GREEN, bg=BG_DARK, cursor='hand2')
        self.heal_btn.pack(side='right')
        self.heal_btn.bind('<Button-1>', lambda e: self._toggle_heal())
        
        # Critical toggle with %
        crit_row = tk.Frame(content, bg=BG_DARK)
        crit_row.pack(fill='x', pady=1)
        
        tk.Label(crit_row, text=f"  🚨 Critical (<{int(self.config.hp_critical_threshold*100)}%):",
                 font=('Arial', 9), fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
        
        self.critical_btn = tk.Label(crit_row, text="[ON]", font=('Arial', 9, 'bold'),
                                     fg=GREEN, bg=BG_DARK, cursor='hand2')
        self.critical_btn.pack(side='right')
        self.critical_btn.bind('<Button-1>', lambda e: self._toggle_critical())
        
        # Skinner toggle (only button, no counter)
        if self.skinner:
            skin_row = tk.Frame(content, bg=BG_DARK)
            skin_row.pack(fill='x', pady=1)
            
            tk.Label(skin_row, text="  🔪 Skinner:", font=('Arial', 9),
                     fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
            
            self.skinner_btn = tk.Label(skin_row, text="[OFF]", font=('Arial', 9, 'bold'),
                                        fg=RED, bg=BG_DARK, cursor='hand2')
            self.skinner_btn.pack(side='right')
            self.skinner_btn.bind('<Button-1>', lambda e: self._toggle_skinner())
        
        # Haste toggle (only button, no counter)
        if self.auto_haste:
            haste_row = tk.Frame(content, bg=BG_DARK)
            haste_row.pack(fill='x', pady=1)
            
            tk.Label(haste_row, text="  💨 Haste:", font=('Arial', 9),
                     fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
            
            self.haste_btn = tk.Label(haste_row, text="[OFF]", font=('Arial', 9, 'bold'),
                                      fg=RED, bg=BG_DARK, cursor='hand2')
            self.haste_btn.pack(side='right')
            self.haste_btn.bind('<Button-1>', lambda e: self._toggle_haste())
        
        # --- Separator ---
        tk.Frame(content, height=1, bg=BORDER).pack(fill='x', pady=4)
        
        # ========== STATISTICS SECTION ==========
        stats_title = tk.Frame(content, bg=BG_DARKER, padx=4, pady=2)
        stats_title.pack(fill='x', pady=(0, 3))
        tk.Label(stats_title, text="📊 Statistics", font=('Arial', 8, 'bold'),
                 fg=GOLD, bg=BG_DARKER).pack(side='left')
        
        # Heals count
        heals_row = tk.Frame(content, bg=BG_DARK)
        heals_row.pack(fill='x', pady=1)
        
        tk.Label(heals_row, text="  💊 Heals:", font=('Arial', 9),
                 fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
        
        self.normal_heals_label = tk.Label(heals_row, text="0",
                                           font=('Arial', 9, 'bold'), fg=GREEN, bg=BG_DARK)
        self.normal_heals_label.pack(side='right')
        
        # Critical count
        crit_count_row = tk.Frame(content, bg=BG_DARK)
        crit_count_row.pack(fill='x', pady=1)
        
        tk.Label(crit_count_row, text="  🚨 Critical:", font=('Arial', 9),
                 fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
        
        self.critical_heals_label = tk.Label(crit_count_row, text="0",
                                             font=('Arial', 9, 'bold'), fg=RED, bg=BG_DARK)
        self.critical_heals_label.pack(side='right')
        
        # Skinner count
        if self.skinner:
            skin_stats_row = tk.Frame(content, bg=BG_DARK)
            skin_stats_row.pack(fill='x', pady=1)
            
            tk.Label(skin_stats_row, text="  🔪 Skins:", font=('Arial', 9),
                     fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
            
            self.skinner_clicks_label = tk.Label(skin_stats_row, text="0",
                                                 font=('Arial', 9, 'bold'), fg=ORANGE, bg=BG_DARK)
            self.skinner_clicks_label.pack(side='right')
        
        # Haste count
        if self.auto_haste:
            haste_stats_row = tk.Frame(content, bg=BG_DARK)
            haste_stats_row.pack(fill='x', pady=1)
            
            tk.Label(haste_stats_row, text="  💨 Hastes:", font=('Arial', 9),
                     fg=TEXT_BEIGE, bg=BG_DARK).pack(side='left')
            
            self.haste_casts_label = tk.Label(haste_stats_row, text="0",
                                              font=('Arial', 9, 'bold'), fg=BLUE, bg=BG_DARK)
            self.haste_casts_label.pack(side='right')
        
        # --- Separator ---
        tk.Frame(content, height=1, bg=BORDER).pack(fill='x', pady=4)
        
        # ========== HOTKEYS SECTION ==========
        hk_title = tk.Frame(content, bg=BG_DARKER, padx=4, pady=2)
        hk_title.pack(fill='x', pady=(0, 3))
        tk.Label(hk_title, text="⌨️ Hotkeys", font=('Arial', 8, 'bold'),
                 fg=GOLD, bg=BG_DARKER).pack(side='left')
        
        # Row 1: F9 Bot | Heal key
        hk1 = tk.Frame(content, bg=BG_DARK)
        hk1.pack(fill='x', pady=1)
        
        left1 = tk.Frame(hk1, bg=BG_DARK)
        left1.pack(side='left')
        tk.Label(left1, text="  F9", font=('Arial', 8, 'bold'),
                 fg=ORANGE, bg=BG_DARK).pack(side='left')
        tk.Label(left1, text=" Bot", font=('Arial', 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(side='left')
        
        right1 = tk.Frame(hk1, bg=BG_DARK)
        right1.pack(side='right')
        tk.Label(right1, text=f"{self.config.heal_key.upper()}", font=('Arial', 8, 'bold'),
                 fg=GREEN, bg=BG_DARK).pack(side='left')
        tk.Label(right1, text=" Heal", font=('Arial', 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(side='left')
        
        # Row 2: Crit key | Haste key
        hk2 = tk.Frame(content, bg=BG_DARK)
        hk2.pack(fill='x', pady=1)
        
        left2 = tk.Frame(hk2, bg=BG_DARK)
        left2.pack(side='left')
        tk.Label(left2, text=f"  {self.config.critical_heal_key.upper()}", font=('Arial', 8, 'bold'),
                 fg=RED, bg=BG_DARK).pack(side='left')
        tk.Label(left2, text=" Crit", font=('Arial', 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(side='left')
        
        right2 = tk.Frame(hk2, bg=BG_DARK)
        right2.pack(side='right')
        tk.Label(right2, text=f"{self.config.haste_hotkey.upper()}", font=('Arial', 8, 'bold'),
                 fg=BLUE, bg=BG_DARK).pack(side='left')
        tk.Label(right2, text=" Haste", font=('Arial', 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(side='left')
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _toggle_skinner(self):
        """Toggle skinner on/off"""
        if self.skinner:
            self.skinner.toggle()
            self._update_skinner_btn()
    
    def _toggle_haste(self):
        """Toggle auto-haste on/off"""
        if self.auto_haste:
            self.auto_haste.toggle()
            self._update_haste_btn()
    
    def _toggle_heal(self):
        """Toggle normal heal on/off"""
        self.health_monitor.toggle_heal()
        self._update_heal_btn()
    
    def _toggle_critical(self):
        """Toggle critical heal on/off"""
        self.health_monitor.toggle_critical()
        self._update_critical_btn()
    
    def _update_skinner_btn(self):
        """Update skinner button appearance"""
        if self.skinner and self.skinner_btn:
            if self.skinner.is_enabled():
                self.skinner_btn.config(text="[ON]", fg='#00c000')
            else:
                self.skinner_btn.config(text="[OFF]", fg='#c00000')
    
    def _update_haste_btn(self):
        """Update haste button appearance"""
        if self.auto_haste and self.haste_btn:
            if self.auto_haste.is_enabled():
                self.haste_btn.config(text="[ON]", fg='#00c000')
            else:
                self.haste_btn.config(text="[OFF]", fg='#c00000')
    
    def _update_heal_btn(self):
        """Update heal button appearance"""
        if self.heal_btn:
            if self.health_monitor.heal_enabled:
                self.heal_btn.config(text="[ON]", fg='#00c000')
            else:
                self.heal_btn.config(text="[OFF]", fg='#c00000')
    
    def _update_critical_btn(self):
        """Update critical button appearance"""
        if self.critical_btn:
            if self.health_monitor.critical_enabled:
                self.critical_btn.config(text="[ON]", fg='#00c000')
            else:
                self.critical_btn.config(text="[OFF]", fg='#c00000')
    
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
                self.status_indicator.config(text="ERROR", fg='#ff0000')
            elif error_status['has_error']:
                self.status_indicator.config(text="DETECT...", fg='#ff8800')
            elif is_paused:
                self.status_indicator.config(text="PAUSED", fg='#c00000')
            else:
                self.status_indicator.config(text="ACTIVE", fg='#00c000')
            
            # Update skinner
            if self.skinner:
                self._update_skinner_btn()
                stats = self.skinner.get_stats()
                self.skinner_clicks_label.config(text=str(stats['click_count']))
            
            # Update auto-haste
            if self.auto_haste:
                self._update_haste_btn()
                stats = self.auto_haste.get_stats()
                self.haste_casts_label.config(text=str(stats['cast_count']))
            
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

