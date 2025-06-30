import pyautogui
import time
import os


class RegionManager:
    def __init__(self, config, debug_logger=None, ocr_processor=None):
        self.config = config
        self.debug_logger = debug_logger
        self.ocr_processor = ocr_processor
        self.hp_region = None
        self.mana_region = None
        
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def wait_for_enter(self):
        """Wait for Enter key press"""
        print("Press ENTER when ready...")
        input()
    
    def select_region(self, region_name):
        """Interactive region selection"""
        print(f"\nSelecting {region_name} region:")
        print(f"1. Position your mouse at the TOP-LEFT corner of the {region_name} text/bar")
        self.wait_for_enter()
        
        x1, y1 = pyautogui.position()
        print(f"Top-left corner set at: ({x1}, {y1})")
        
        print(f"2. Now position your mouse at the BOTTOM-RIGHT corner of the {region_name} text/bar")
        self.wait_for_enter()
        
        x2, y2 = pyautogui.position()
        print(f"Bottom-right corner set at: ({x2}, {y2})")
        
        # Ensure proper ordering
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)
        
        region = (left, top, width, height)
        print(f"{region_name} region set to: {region}")
        return region
    
    def setup_regions(self):
        """Setup HP and Mana regions interactively"""
        print("=== Region Setup ===")
        print("You'll need to select the regions where HP and Mana values are displayed.")
        print("Make sure your game is visible and the values are clearly shown.")
        print("TIP: Select regions that contain ONLY the numbers, not the bars or labels.")
        print()
        
        thresholds = self.config.get_threshold_info()
        print(f"🎮 Smart Healing Strategy:")
        print(f"   🚨 {self.config.critical_heal_key.upper()} (Critical): HP below {thresholds['hp_critical']}")
        print(f"   💊 {self.config.heal_key.upper()} (Moderate): HP below {thresholds['hp_moderate']} (but above {thresholds['hp_critical']})")
        print(f"   💙 {self.config.mana_key.upper()} (Mana): Mana below {thresholds['mana']}")
        print()
        
        self.hp_region = self.select_region("HP")
        self.debug_log(f"SETUP: HP region selected: {self.hp_region}")
        time.sleep(1)
        
        self.mana_region = self.select_region("Mana")
        self.debug_log(f"SETUP: Mana region selected: {self.mana_region}")
        
        print("\nRegions configured successfully!")
        self.test_regions()
    
    def test_regions(self):
        """Test the configured regions"""
        if not self.ocr_processor:
            print("⚠️  Warning: No OCR processor available for testing")
            return
            
        print("Testing regions...")
        
        last_valid_hp = None
        last_valid_mana = None
        
        for i in range(5):
            hp_val = self.ocr_processor.extract_number_from_region(self.hp_region, "hp")
            mana_val = self.ocr_processor.extract_number_from_region(self.mana_region, "mana")
            hp_detected = hp_val is not None
            mana_detected = mana_val is not None
            
            if hp_detected:
                last_valid_hp = hp_val
                self.debug_log(f"SETUP: HP detected: {hp_val}")
            if mana_detected:
                last_valid_mana = mana_val
                self.debug_log(f"SETUP: Mana detected: {mana_val}")
            
            detection_status = f"HP: {'✓' if hp_detected else '✗'}, Mana: {'✓' if mana_detected else '✗'}"
            print(f"Test {i+1} - HP: {hp_val or 'Not detected'}, Mana: {mana_val or 'Not detected'} - Detection: {detection_status}")
            time.sleep(0.3)
        
        valid_readings = 0
        if last_valid_hp is not None:
            valid_readings += 1
        if last_valid_mana is not None:
            valid_readings += 1
            
        print(f"\n📈 Test Results:")
        if valid_readings >= 1:
            print(f"✅ At least one region is working!")
            if last_valid_hp:
                hp_percent = (last_valid_hp / self.config.max_hp) * 100
                print(f"   Current HP: {last_valid_hp} ({hp_percent:.1f}%)")
            if last_valid_mana:
                mana_percent = (last_valid_mana / self.config.max_mana) * 100
                print(f"   Current Mana: {last_valid_mana} ({mana_percent:.1f}%)")
        else:
            print(f"⚠️  Warning: No values detected!")
            print("Consider:")
            print("1. Selecting smaller regions with better contrast")
            print("2. Ensuring numbers are clearly visible and not blurry")
            print("3. Checking that no UI elements overlap the text")
    
    def load_saved_regions(self, filename="regions.txt"):
        """Load regions from file"""
        if not os.path.exists(filename):
            return False
            
        try:
            with open(filename, 'r') as f:
                saved_regions = {}
                for line in f:
                    if ':' in line:
                        name, region_str = line.strip().split(':', 1)
                        region = eval(region_str.strip())
                        saved_regions[name] = region
            
            if 'HP' in saved_regions and 'Mana' in saved_regions:
                self.hp_region = saved_regions['HP']
                self.mana_region = saved_regions['Mana']
                print("✅ Loaded saved regions!")
                print(f"📍 Using saved regions: HP{self.hp_region}, Mana{self.mana_region}")
                return True
        except Exception as e:
            print(f"❌ Error loading saved regions: {e}")
            
        return False
    
    def get_regions(self):
        """Get current regions as dictionary"""
        return {
            'hp': self.hp_region,
            'mana': self.mana_region
        } 