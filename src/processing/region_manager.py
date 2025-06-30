import pyautogui
import time
import os


class RegionManager:
    def __init__(self, config, debug_logger=None, ocr_processor=None):
        self.config = config
        self.debug_logger = debug_logger
        self.ocr_processor = ocr_processor
        self.hp_region = None
        
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
        """Setup HP region interactively"""
        print("=== Region Setup ===")
        print("You'll need to select the region where HP values are displayed.")
        print("Make sure your game is visible and the values are clearly shown.")
        print("TIP: Select a region that contains ONLY the numbers, not the bars or labels.")
        print()
        
        thresholds = self.config.get_threshold_info()
        print(f"🎮 Smart Healing Strategy:")
        print(f"   🚨 {self.config.critical_heal_key.upper()} (Critical): HP below {thresholds['hp_critical']}")
        print(f"   💊 {self.config.heal_key.upper()} (Moderate): HP below {thresholds['hp_moderate']} (but above {thresholds['hp_critical']})")
        print()
        
        self.hp_region = self.select_region("HP")
        self.debug_log(f"SETUP: HP region selected: {self.hp_region}")
        
        print("\nRegion configured successfully!")
        self.test_regions()
        
        # Save the region to file
        self.save_regions()
    
    def save_regions(self, filename="regions.txt"):
        """Save regions to file"""
        try:
            with open(filename, 'w') as f:
                if self.hp_region:
                    f.write(f"HP: {self.hp_region}\n")
            
            print(f"✅ Region saved to {filename}")
            self.debug_log(f"SETUP: Region saved to {filename} - HP: {self.hp_region}")
            
        except Exception as e:
            print(f"❌ Error saving regions: {e}")
            self.debug_log(f"SETUP: Error saving regions: {e}")
    
    def test_regions(self):
        """Test the configured region"""
        if not self.ocr_processor:
            print("⚠️  Warning: No OCR processor available for testing")
            return
            
        print("Testing region...")
        
        last_valid_hp = None
        
        for i in range(5):
            hp_val = self.ocr_processor.extract_number_from_region(self.hp_region, "hp")
            hp_detected = hp_val is not None
            
            if hp_detected:
                last_valid_hp = hp_val
                self.debug_log(f"SETUP: HP detected: {hp_val}")
            
            detection_status = f"HP: {'✓' if hp_detected else '✗'}"
            print(f"Test {i+1} - HP: {hp_val or 'Not detected'} - Detection: {detection_status}")
            time.sleep(0.3)
        
        print(f"\n📈 Test Results:")
        if last_valid_hp is not None:
            print(f"✅ HP region is working!")
            hp_percent = (last_valid_hp / self.config.max_hp) * 100
            print(f"   Current HP: {last_valid_hp} ({hp_percent:.1f}%)")
        else:
            print(f"⚠️  Warning: No HP values detected!")
            print("Consider:")
            print("1. Selecting a smaller region with better contrast")
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
            
            if 'HP' in saved_regions:
                self.hp_region = saved_regions['HP']
                print("✅ Loaded saved region!")
                print(f"📍 Using saved region: HP{self.hp_region}")
                return True
        except Exception as e:
            print(f"❌ Error loading saved regions: {e}")
            
        return False
    
    def get_regions(self):
        """Get current region as dictionary"""
        return {
            'hp': self.hp_region
        } 