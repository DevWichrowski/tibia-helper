import pyautogui
import cv2
import numpy as np
import pytesseract
import time
import sys
from PIL import Image
import re

class RegionSelector:
    def __init__(self):
        self.regions = {}
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
    def wait_for_enter(self):
        """Wait for enter key press"""
        print("Press ENTER when ready...")
        input()
    def select_region_interactive(self, region_name):
        print(f"\n=== Selecting {region_name} Region ===")
        print("1. Position your mouse at the TOP-LEFT corner of the number")
        self.wait_for_enter()
        
        x1, y1 = pyautogui.position()
        print(f"Top-left: ({x1}, {y1})")
        
        print("2. Position your mouse at the BOTTOM-RIGHT corner of the number")
        self.wait_for_enter()
        
        x2, y2 = pyautogui.position()
        print(f"Bottom-right: ({x2}, {y2})")
        
        # Calculate region
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)
        region = (left, top, width, height)
        
        print(f"Region: {region}")
        
        return region
    
    def test_ocr_on_region(self, region, region_name):
        """Test OCR accuracy on a selected region"""
        if not region:
            return None
            
        print(f"\n🔍 Testing OCR on {region_name} region...")
        
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Save original image for review
            cv2.imwrite(f"{region_name}_original.png", img)
            print(f"Saved {region_name}_original.png")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Test different preprocessing methods
            methods = {
                "OTSU": cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                "Inverted_OTSU": cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
                "Adaptive": cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
                "High_Contrast": cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1],
                "Low_Contrast": cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]
            }
            
            results = {}
            
            for method_name, thresh in methods.items():
                # Scale up for better OCR
                scale_factor = 10
                height, width = thresh.shape
                scaled = cv2.resize(thresh, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
                
                # Clean up
                kernel = np.ones((2,2), np.uint8)
                cleaned = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
                cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
                cleaned = cv2.GaussianBlur(cleaned, (3, 3), 0)
                
                # Save processed image
                cv2.imwrite(f"{region_name}_{method_name}.png", cleaned)
                
                # Try OCR
                try:
                    text = pytesseract.image_to_string(cleaned, config='--psm 8 -c tesseract_char_whitelist=0123456789').strip()
                    numbers = re.findall(r'\d+', text)
                    
                    if numbers:
                        result = max([int(num) for num in numbers])
                        results[method_name] = result
                        print(f"  {method_name}: {result}")
                    else:
                        print(f"  {method_name}: No numbers found")
                        
                except Exception as e:
                    print(f"  {method_name}: OCR error - {e}")
            
            if results:
                # Find most common result
                from collections import Counter
                counts = Counter(results.values())
                most_common = counts.most_common(1)[0][0]
                print(f"\n📊 Most common result: {most_common}")
                print(f"📊 All results: {results}")
                return most_common
            else:
                print("❌ No valid OCR results found")
                return None
                
        except Exception as e:
            print(f"❌ Error testing region: {e}")
            return None
    
    def adjust_region(self, region, region_name):
        """Allow fine-tuning of region coordinates"""
        print(f"\n🔧 Current {region_name} region: {region}")
        print("Options:")
        print("1. Test current region")
        print("2. Make region smaller")
        print("3. Make region larger") 
        print("4. Move region")
        print("5. Reselect region")
        print("6. Accept region")
        
        choice = input("Choose option (1-6): ").strip()
        
        if choice == "1":
            self.test_ocr_on_region(region, region_name)
            return self.adjust_region(region, region_name)
        elif choice == "2":
            print("Making region 20% smaller...")
            left, top, width, height = region
            new_width = int(width * 0.8)
            new_height = int(height * 0.8)
            new_left = left + (width - new_width) // 2
            new_top = top + (height - new_height) // 2
            new_region = (new_left, new_top, new_width, new_height)
            return self.adjust_region(new_region, region_name)
        elif choice == "3":
            print("Making region 20% larger...")
            left, top, width, height = region
            new_width = int(width * 1.2)
            new_height = int(height * 1.2)
            new_left = left - (new_width - width) // 2
            new_top = top - (new_height - height) // 2
            new_region = (new_left, new_top, new_width, new_height)
            return self.adjust_region(new_region, region_name)
        elif choice == "4":
            print("Use arrow keys concept: +/- 10 pixels")
            direction = input("Direction (up/down/left/right): ").lower()
            left, top, width, height = region
            if direction == "up":
                new_region = (left, top - 10, width, height)
            elif direction == "down":
                new_region = (left, top + 10, width, height)
            elif direction == "left":
                new_region = (left - 10, top, width, height)
            elif direction == "right":
                new_region = (left + 10, top, width, height)
            else:
                print("Invalid direction")
                return self.adjust_region(region, region_name)
            return self.adjust_region(new_region, region_name)
        elif choice == "5":
            return self.select_region_interactive(region_name)
        elif choice == "6":
            return region
        else:
            print("Invalid choice")
            return self.adjust_region(region, region_name)
    
    def save_regions(self, filename="regions.txt"):
        """Save selected regions to file"""
        with open(filename, 'w') as f:
            for name, region in self.regions.items():
                f.write(f"{name}: {region}\n")
        print(f"✅ Regions saved to {filename}")
    
    def load_regions(self, filename="regions.txt"):
        """Load regions from file"""
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if ':' in line:
                        name, region_str = line.strip().split(':', 1)
                        region = eval(region_str.strip())
                        self.regions[name] = region
            print(f"✅ Regions loaded from {filename}")
        except FileNotFoundError:
            print(f"❌ {filename} not found")
    
    def run(self):
        print("=== Region Selection Tool ===")
        print("This tool helps you select perfect regions for OCR")
        print()
        
        # Select HP region
        hp_region = self.select_region_interactive("HP")
        hp_result = self.test_ocr_on_region(hp_region, "HP")
        hp_region = self.adjust_region(hp_region, "HP")
        self.regions["HP"] = hp_region
        
        print(f"\n✅ HP region finalized: {hp_region}")
        
        time.sleep(1)
        
        # Select Mana region
        mana_region = self.select_region_interactive("Mana")
        mana_result = self.test_ocr_on_region(mana_region, "Mana")
        mana_region = self.adjust_region(mana_region, "Mana")
        self.regions["Mana"] = mana_region
        
        print(f"\n✅ Mana region finalized: {mana_region}")
        
        # Save regions
        self.save_regions()
        
        print(f"\n🎯 Final Results:")
        print(f"HP Region: {self.regions['HP']}")
        print(f"Mana Region: {self.regions['Mana']}")
        print(f"\n📁 Check the generated PNG files to see what OCR is reading")
        print(f"📁 Regions saved to regions.txt")

def main():
    selector = RegionSelector()
    selector.run()

if __name__ == "__main__":
    main() 