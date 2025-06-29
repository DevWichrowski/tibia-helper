import pyautogui
import cv2
import numpy as np
import pytesseract
import time
import sys
from PIL import Image
import re
import threading
import datetime
import os

class RegionGameHelper:
    def __init__(self):
        self.max_hp = 1415
        self.max_mana = 1224
        self.hp_threshold = 0.83  # 83% - use F1 for moderate healing
        self.hp_critical_threshold = 0.55  # 55% - use F6 for critical healing
        self.mana_threshold = 0.75  # 75% - changed from 70%
        self.last_f1_press = 0
        self.last_f6_press = 0  # New for critical healing
        self.last_f4_press = 0
        self.cooldown = 0.2  # Increased to 0.2 seconds for better accuracy
        self.running = True
        
        # Regions to be set by user
        self.hp_region = None
        self.mana_region = None
        
        # Simple failure tracking - just count consecutive failures
        self.hp_consecutive_failures = 0
        self.mana_consecutive_failures = 0
        self.max_failures_warning = 5  # Warn after 5 consecutive failures
        
        # Stability tracking to prevent false critical healing from bad OCR
        self.last_stable_hp = None
        self.last_stable_hp_time = 0
        self.pending_critical_hp = None  # HP value that needs confirmation for critical healing
        self.critical_confirmation_time = 0.5  # Require confirmation within 0.5 seconds
        self.dramatic_drop_threshold = 0.4  # 40% drop is considered dramatic
        
        # Debug logging
        self.debug_log_file = "game_helper_debug.log"
        self.enable_debug = True
        self.init_debug_log()
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.001  # Ultra-fast GUI operations
        
    def parse_health_value(self, text, value_type="unknown"):
        """Parse health/mana value from OCR text - handles corrupted OCR readings"""
        if not text:
            return None
            
        self.debug_log(f"PARSE {value_type.upper()}: Raw OCR text: '{text}'")
        
        # Pattern 1: Simple number with word boundaries (preferred)
        simple_match = re.search(r'\b(\d{3,4})\b', text)
        if simple_match:
            result = int(simple_match.group(1))
            self.debug_log(f"PARSE {value_type.upper()}: Found bounded number: {result}")
            return result
        
        # Pattern 2: Any sequence of 3-4 digits (fallback)
        digit_match = re.search(r'(\d{3,4})', text)
        if digit_match:
            result = int(digit_match.group(1))
            self.debug_log(f"PARSE {value_type.upper()}: Found digit sequence: {result}")
            return result
        
        # Pattern 3: Handle corrupted OCR - look for numbers with letters mixed in
        # Examples: "S64" -> "864", "86 4" -> "864", "B72" -> "872"
        corrupted_patterns = [
            # Replace common OCR mistakes with numbers
            (r'[SB](\d{2,3})', r'8\1'),  # S64 -> 864, B72 -> 872
            (r'(\d+)\s+(\d+)', r'\1\2'),  # 86 4 -> 864
            (r'[O](\d{2,3})', r'0\1'),   # O64 -> 064
            (r'[Gg](\d{2,3})', r'6\1'),  # G64 -> 664
            (r'[lI](\d{2,3})', r'1\1'),  # l64 -> 164, I64 -> 164
            (r'(\d{2,3})[lI]', r'\1'),   # 64l -> 64, 64I -> 64
        ]
        
        for pattern, replacement in corrupted_patterns:
            try:
                fixed_text = re.sub(pattern, replacement, text)
                if fixed_text != text:
                    self.debug_log(f"PARSE {value_type.upper()}: Applied fix '{pattern}' -> '{fixed_text}'")
                    # Try to parse the fixed text
                    digit_match = re.search(r'(\d{3,4})', fixed_text)
                    if digit_match:
                        result = int(digit_match.group(1))
                        max_value = self.max_hp if value_type == "hp" else self.max_mana
                        if 1 <= result <= max_value:
                            self.debug_log(f"PARSE {value_type.upper()}: Fixed corrupted text to: {result}")
                            return result
            except:
                continue
        
        # Pattern 4: Any digits (last resort - take the largest)
        all_numbers = re.findall(r'\d+', text)
        if all_numbers:
            numbers = [int(num) for num in all_numbers if 100 <= int(num) <= 3000]
            if numbers:
                result = max(numbers)  # Take the largest valid number
                self.debug_log(f"PARSE {value_type.upper()}: Found largest valid number: {result}")
                return result
            
        self.debug_log(f"PARSE {value_type.upper()}: No valid patterns found")
        return None
        
    def init_debug_log(self):
        """Initialize debug log file"""
        if self.enable_debug:
            try:
                with open(self.debug_log_file, 'w') as f:
                    f.write(f"=== Game Helper Debug Log Started ===\n")
                    f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Max HP: {self.max_hp}, Max Mana: {self.max_mana}\n")
                    f.write(f"Thresholds: HP Critical={self.hp_critical_threshold*100}%, HP Moderate={self.hp_threshold*100}%, Mana={self.mana_threshold*100}%\n")
                    f.write(f"Cooldown: {self.cooldown}s\n")
                    f.write("="*50 + "\n\n")
                print(f"📝 Debug logging enabled: {self.debug_log_file}")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize debug log: {e}")
                self.enable_debug = False
    
    def debug_log(self, message):
        """Write debug message to log file with timestamp"""
        if not self.enable_debug:
            return
        try:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
            with open(self.debug_log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            pass  # Silently fail to avoid disrupting the main flow
        
    def wait_for_spacebar(self):
        """Wait for spacebar press using a simple approach"""
        print("Press ENTER when ready...")
        input()
        
    def select_region(self, region_name):
        print(f"\nSelecting {region_name} region:")
        print("1. Position your mouse at the TOP-LEFT corner of the " + region_name + " text/bar")
        self.wait_for_spacebar()
        
        x1, y1 = pyautogui.position()
        print(f"Top-left corner set at: ({x1}, {y1})")
        
        print("2. Now position your mouse at the BOTTOM-RIGHT corner of the " + region_name + " text/bar")
        self.wait_for_spacebar()
        
        x2, y2 = pyautogui.position()
        print(f"Bottom-right corner set at: ({x2}, {y2})")
        
        # Ensure proper ordering
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)
        
        region = (left, top, width, height)
        print(f"{region_name} region set to: {region}")
        return region
    
    def extract_number_from_region(self, region, value_type="unknown"):
        if not region:
            self.debug_log(f"OCR {value_type.upper()}: No region defined")
            return None
            
        self.debug_log(f"OCR {value_type.upper()}: Starting extraction from region {region}")
        
        try:
            # Take screenshot of the specific region
            screenshot = pyautogui.screenshot(region=region)
            
            # Convert to OpenCV format
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Fast OCR with only best methods for speed
            results = []
            methods_used = []
            
            # Try all methods and collect valid results
            methods = [
                ("OTSU", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                ("InvOTSU", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
                ("LowContrast", cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]),
                ("HighContrast", cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]),
                ("Adaptive", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
            ]
            
            valid_results = []
            
            for method_name, thresh in methods:
                # Try fast mode first
                result = self._ocr_from_image(thresh, fast_mode=True, value_type=value_type)
                
                # Validate using exact max bounds (HP ≤ 1415, Mana ≤ 1224)
                max_value = self.max_hp if value_type == "hp" else self.max_mana
                if result is not None and 1 <= result <= max_value:
                    valid_results.append(result)
                    self.debug_log(f"OCR {value_type.upper()}: {method_name} method SUCCESS: {result}")
                    
                    # If we have multiple valid results, return the most common one
                    if len(valid_results) >= 2:
                        from collections import Counter
                        counts = Counter(valid_results)
                        most_common = counts.most_common(1)[0][0]
                        self.debug_log(f"OCR {value_type.upper()}: Multiple valid results, returning most common: {most_common}")
                        return most_common
                elif result is not None:
                    results.append(result)
                    methods_used.append(f"{method_name}:{result}")
                    
            # If we found at least one valid result, return it
            if valid_results:
                result = valid_results[0]
                self.debug_log(f"OCR {value_type.upper()}: Single valid result: {result}")
                return result
            
            self.debug_log(f"OCR {value_type.upper()}: Raw results from methods: {', '.join(methods_used) if methods_used else 'None'}")
            
            if results:
                # Return the most common result, but prefer 4-digit numbers for mana and HP
                from collections import Counter
                counts = Counter(results)
                
                if value_type in ["hp", "mana"]:
                    # Prefer 3-4 digit numbers for HP/mana
                    valid_results = [r for r in results if 100 <= r <= 9999]
                    if valid_results:
                        counts = Counter(valid_results)
                        self.debug_log(f"OCR {value_type.upper()}: Filtered to valid range: {valid_results}")
                
                if counts:
                    final_result = counts.most_common(1)[0][0]
                    self.debug_log(f"OCR {value_type.upper()}: Final result selected: {final_result} (from {list(counts.keys())})")
                    return final_result
            
            self.debug_log(f"OCR {value_type.upper()}: No valid results found")
                    
        except Exception as e:
            self.debug_log(f"OCR {value_type.upper()}: Exception occurred: {str(e)}")
        
        return None
    
    def _ocr_from_image(self, thresh, fast_mode=False, value_type="unknown"):
        """Enhanced OCR with better text extraction and parsing"""
        all_texts = []
        
        try:
            if fast_mode:
                # Fast mode: try multiple scaling factors
                scale_factors = [3, 5, 8]
                configs = [
                    '--psm 8 -c tesseract_char_whitelist=0123456789',
                    '--psm 7 -c tesseract_char_whitelist=0123456789',
                    '--psm 6 -c tesseract_char_whitelist=0123456789'
                ]
            else:
                # Full mode: comprehensive approach
                scale_factors = [5, 8, 10]
                configs = [
                    '--psm 8 -c tesseract_char_whitelist=0123456789',
                    '--psm 7 -c tesseract_char_whitelist=0123456789',
                    '--psm 6 -c tesseract_char_whitelist=0123456789',
                    '--psm 13 -c tesseract_char_whitelist=0123456789'
                ]
            
            height, width = thresh.shape
            
            # Try different scaling factors
            for scale_factor in scale_factors:
                scaled = cv2.resize(thresh, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
                
                if not fast_mode:
                    # Apply cleaning operations for full mode
                    kernel = np.ones((2,2), np.uint8)
                    cleaned = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
                    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
                    cleaned = cv2.GaussianBlur(cleaned, (3, 3), 0)
                else:
                    cleaned = scaled
                
                # Try different OCR configurations
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(cleaned, config=config).strip()
                        if text and len(text) > 0:
                            all_texts.append(text)
                            self.debug_log(f"OCR {value_type.upper()}: Scale {scale_factor}, Config {config.split()[0]}: '{text}'")
                            
                            # Try to parse this text immediately
                            parsed_value = self.parse_health_value(text, value_type)
                            if parsed_value and 100 <= parsed_value <= 3000:
                                self.debug_log(f"OCR {value_type.upper()}: SUCCESS - Found valid value {parsed_value}")
                                return parsed_value
                    except Exception as e:
                        self.debug_log(f"OCR {value_type.upper()}: Config {config} failed: {str(e)}")
                        continue
            
            # If no immediate success, try parsing all collected texts
            self.debug_log(f"OCR {value_type.upper()}: Trying to parse from all texts: {all_texts}")
            for text in all_texts:
                parsed_value = self.parse_health_value(text, value_type)
                if parsed_value and 100 <= parsed_value <= 3000:
                    self.debug_log(f"OCR {value_type.upper()}: FALLBACK SUCCESS - Found valid value {parsed_value}")
                    return parsed_value
                    
        except Exception as e:
            self.debug_log(f"OCR {value_type.upper()}: Exception in _ocr_from_image: {str(e)}")
        
        self.debug_log(f"OCR {value_type.upper()}: No valid values found from any method")
        return None
    
    def extract_number_from_region_with_fallback(self, region, value_type="unknown"):
        """Enhanced OCR with fallback strategies for better reliability"""
        if not region:
            self.debug_log(f"FALLBACK {value_type.upper()}: No region defined")
            return None
            
        # Strategy 1: Try normal OCR first
        result = self.extract_number_from_region(region, value_type)
        if result is not None:
            self.debug_log(f"FALLBACK {value_type.upper()}: Normal OCR succeeded: {result}")
            return result
        
        self.debug_log(f"FALLBACK {value_type.upper()}: Normal OCR failed, trying fallback strategies")
        
        # Strategy 2: Try simple direct OCR with basic preprocessing
        try:
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Simple approaches
            fallback_methods = [
                # Very basic thresholding
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
                # Inverted binary
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1],
                # Just grayscale
                gray
            ]
            
            for i, processed_img in enumerate(fallback_methods):
                try:
                    # Simple OCR with minimal processing
                    text = pytesseract.image_to_string(processed_img, config='--psm 8 -c tesseract_char_whitelist=0123456789').strip()
                    if text:
                        self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} raw text: '{text}'")
                        parsed = self.parse_health_value(text, value_type)
                        max_value = self.max_hp if value_type == "hp" else self.max_mana
                        if parsed and 1 <= parsed <= max_value:
                            self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} SUCCESS: {parsed}")
                            return parsed
                except Exception as e:
                    self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} failed: {str(e)}")
                    continue
            
            # Strategy 3: Try to extract numbers from the previous garbage OCR attempts
            # Sometimes OCR reads "S64" when it should be "864", etc.
            self.debug_log(f"FALLBACK {value_type.upper()}: Trying number extraction from corrupted readings")
            
            # Try OCR one more time and look for partial numbers
            for processed_img in fallback_methods:
                try:
                    text = pytesseract.image_to_string(processed_img, config='--psm 7').strip()
                    if text:
                        self.debug_log(f"FALLBACK {value_type.upper()}: Corrupted text analysis: '{text}'")
                        # Look for any digit sequences in the corrupted text
                        import re
                        digit_sequences = re.findall(r'\d+', text)
                        if digit_sequences:
                            for seq in digit_sequences:
                                if len(seq) >= 3:  # At least 3 digits
                                    num = int(seq)
                                    max_value = self.max_hp if value_type == "hp" else self.max_mana
                                    if 1 <= num <= max_value:
                                        self.debug_log(f"FALLBACK {value_type.upper()}: Extracted number from corrupted text: {num}")
                                        return num
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.debug_log(f"FALLBACK {value_type.upper()}: Exception in fallback: {str(e)}")
        
        self.debug_log(f"FALLBACK {value_type.upper()}: All strategies failed")
        return None
    
    def get_hp_mana_values(self):
        # Get fresh readings from OCR with fallback retry
        hp_value = self.extract_number_from_region_with_fallback(self.hp_region, "hp")
        mana_value = self.extract_number_from_region_with_fallback(self.mana_region, "mana")
        
        # Debug log raw OCR results
        self.debug_log(f"OCR_RESULTS: HP: {hp_value}, Mana: {mana_value}")
        
        # Simple validation - only check if values are within reasonable bounds
        hp_valid = hp_value is not None and 1 <= hp_value <= self.max_hp
        mana_valid = mana_value is not None and 1 <= mana_value <= self.max_mana
        
        self.debug_log(f"VALIDATION: HP {hp_value} is {'VALID' if hp_valid else 'INVALID'}, Mana {mana_value} is {'VALID' if mana_valid else 'INVALID'}")
        
        # Track consecutive failures for warning purposes only
        if not hp_valid:
            self.hp_consecutive_failures += 1
            self.debug_log(f"FAILURES: HP consecutive failures: {self.hp_consecutive_failures}")
            if self.hp_consecutive_failures == self.max_failures_warning:
                print(f"⚠️  Warning: HP reading has failed {self.hp_consecutive_failures} times in a row")
        else:
            self.hp_consecutive_failures = 0  # Reset on success
            
        if not mana_valid:
            self.mana_consecutive_failures += 1
            self.debug_log(f"FAILURES: Mana consecutive failures: {self.mana_consecutive_failures}")
            if self.mana_consecutive_failures == self.max_failures_warning:
                print(f"⚠️  Warning: Mana reading has failed {self.mana_consecutive_failures} times in a row")
        else:
            self.mana_consecutive_failures = 0  # Reset on success
        
        # Return the actual values (or None if invalid) - no caching
        final_hp = hp_value if hp_valid else None
        final_mana = mana_value if mana_valid else None
        
        self.debug_log(f"FINAL_VALUES: HP={final_hp}, Mana={final_mana}")
        
        return final_hp, final_mana
    
    def press_key_with_cooldown(self, key, last_press_time, action_type="ACTION"):
        current_time = time.time()
        time_since_last = current_time - last_press_time
        
        if time_since_last >= self.cooldown:
            pyautogui.press(key)
            self.debug_log(f"KEY_PRESS: {key.upper()} pressed for {action_type} (cooldown: {time_since_last:.3f}s)")
            print(f"\n🚨 {action_type}: {key.upper()} pressed at {time.strftime('%H:%M:%S')}", flush=True)
            return current_time
        else:
            self.debug_log(f"KEY_BLOCKED: {key.upper()} blocked for {action_type} (cooldown remaining: {self.cooldown - time_since_last:.3f}s)")
            return last_press_time
    
    def check_and_respond(self, hp_value, mana_value):
        self.debug_log(f"DECISION: Checking thresholds - HP: {hp_value}, Mana: {mana_value}")
        
        if hp_value is not None and hp_value > 0:
            hp_percentage = hp_value / self.max_hp
            current_time = time.time()
            
            self.debug_log(f"DECISION: HP {hp_value} = {hp_percentage*100:.1f}% (Critical<{self.hp_critical_threshold*100}%, Moderate<{self.hp_threshold*100}%)")
            
            # Check for dramatic HP drops that might be OCR errors
            is_dramatic_drop = False
            if self.last_stable_hp is not None:
                hp_drop_percent = (self.last_stable_hp - hp_value) / self.max_hp
                if hp_drop_percent > self.dramatic_drop_threshold:
                    is_dramatic_drop = True
                    self.debug_log(f"STABILITY: Dramatic HP drop detected: {self.last_stable_hp} → {hp_value} (drop: {hp_drop_percent*100:.1f}%)")
            
            # Critical healing - F6 for HP below 55%
            if hp_percentage < self.hp_critical_threshold:
                # If this is a dramatic drop, require confirmation
                if is_dramatic_drop:
                    if self.pending_critical_hp is None:
                        # First time seeing this low HP after a dramatic drop
                        self.pending_critical_hp = hp_value
                        self.debug_log(f"STABILITY: Critical HP {hp_percentage*100:.1f}% needs confirmation due to dramatic drop")
                    elif abs(hp_value - self.pending_critical_hp) <= 50:  # Similar HP reading
                        # Confirmed low HP - proceed with critical healing
                        self.debug_log(f"STABILITY: Critical HP confirmed ({self.pending_critical_hp} → {hp_value}) - CRITICAL HEAL needed")
                        self.last_f6_press = self.press_key_with_cooldown('f6', self.last_f6_press, "CRITICAL HEAL")
                        self.pending_critical_hp = None
                    else:
                        # Different HP reading - update pending
                        self.pending_critical_hp = hp_value
                        self.debug_log(f"STABILITY: Critical HP reading changed, updating pending: {hp_value}")
                else:
                    # Not a dramatic drop - proceed with critical healing
                    self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% < {self.hp_critical_threshold*100}% - CRITICAL HEAL needed")
                    self.last_f6_press = self.press_key_with_cooldown('f6', self.last_f6_press, "CRITICAL HEAL")
                    self.pending_critical_hp = None
            # Moderate healing - F1 for HP between 55-83%
            elif hp_percentage < self.hp_threshold:
                self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% < {self.hp_threshold*100}% - MODERATE HEAL needed")
                self.last_f1_press = self.press_key_with_cooldown('f1', self.last_f1_press, "HEAL")
                self.pending_critical_hp = None  # Clear any pending critical
            else:
                self.debug_log(f"DECISION: HP {hp_percentage*100:.1f}% is healthy - no healing needed")
                self.pending_critical_hp = None  # Clear any pending critical
            
            # Update stable HP tracking
            if not is_dramatic_drop or hp_percentage > self.hp_critical_threshold:
                # This reading seems stable, update our reference
                self.last_stable_hp = hp_value
                self.last_stable_hp_time = current_time
                self.debug_log(f"STABILITY: Updated stable HP reference to {hp_value}")
            
        else:
            self.debug_log(f"DECISION: HP value invalid or zero - no HP action")
        
        if mana_value is not None and mana_value > 0:
            mana_percentage = mana_value / self.max_mana
            self.debug_log(f"DECISION: Mana {mana_value} = {mana_percentage*100:.1f}% (Threshold<{self.mana_threshold*100}%)")
            
            if mana_percentage < self.mana_threshold:
                self.debug_log(f"DECISION: Mana {mana_percentage*100:.1f}% < {self.mana_threshold*100}% - MANA restoration needed")
                self.last_f4_press = self.press_key_with_cooldown('f4', self.last_f4_press, "MANA")
            else:
                self.debug_log(f"DECISION: Mana {mana_percentage*100:.1f}% is sufficient - no mana action")
        else:
            self.debug_log(f"DECISION: Mana value invalid or zero - no mana action")
    
    def display_status(self, hp_value, mana_value):
        if hp_value is not None and hp_value > 0:
            hp_percent = (hp_value / self.max_hp * 100)
        else:
            hp_percent = 0
            
        if mana_value is not None and mana_value > 0:
            mana_percent = (mana_value / self.max_mana * 100)
        else:
            mana_percent = 0
        
        # Simple status indicators
        hp_status = "✓" if hp_value is not None else "✗"
        mana_status = "✓" if mana_value is not None else "✗"
        
        status = f"HP: {hp_value or 'N/A'} ({hp_percent:.1f}%) [{hp_status}] | Mana: {mana_value or 'N/A'} ({mana_percent:.1f}%) [{mana_status}]"
        print(status)
    
    def setup_regions(self):
        print("=== Region Setup ===")
        print("You'll need to select the regions where HP and Mana values are displayed.")
        print("Make sure your game is visible and the values are clearly shown.")
        print("TIP: Select regions that contain ONLY the numbers, not the bars or labels.")
        print()
        print(f"🎮 Smart Healing Strategy:")
        print(f"   🚨 F6 (Critical): HP below {self.hp_critical_threshold*100}%")
        print(f"   💊 F1 (Moderate): HP below {self.hp_threshold*100}% (but above {self.hp_critical_threshold*100}%)")
        print(f"   💙 F4 (Mana): Mana below {self.mana_threshold*100}%")
        print()
        
        self.hp_region = self.select_region("HP")
        self.debug_log(f"SETUP: HP region selected: {self.hp_region}")
        time.sleep(1)
        self.mana_region = self.select_region("Mana")
        self.debug_log(f"SETUP: Mana region selected: {self.mana_region}")
        
        print("\nRegions configured successfully!")
        print("Testing regions...")
        
        # Test multiple times to ensure reliability
        last_valid_hp = None
        last_valid_mana = None
        
        for i in range(5):
            hp_val = self.extract_number_from_region(self.hp_region, "hp")
            mana_val = self.extract_number_from_region(self.mana_region, "mana")
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
                hp_percent = (last_valid_hp / self.max_hp) * 100
                print(f"   Current HP: {last_valid_hp} ({hp_percent:.1f}%)")
            if last_valid_mana:
                mana_percent = (last_valid_mana / self.max_mana) * 100
                print(f"   Current Mana: {last_valid_mana} ({mana_percent:.1f}%)")
        else:
            print(f"⚠️  Warning: No values detected!")
            print("Consider:")
            print("1. Selecting smaller regions with better contrast")
            print("2. Ensuring numbers are clearly visible and not blurry")
            print("3. Checking that no UI elements overlap the text")
    
    def run(self):
        print("\nStarting region-based game helper... (monitoring every 0.05 seconds - ENHANCED OCR!)")
        print("Detection indicators: ✓ = Detected, ✗ = Using cached value")
        print("🎮 Smart Healing: F6 (<55% HP), F1 (55-83% HP), F4 (<75% Mana)")
        print("🛡️ Enhanced OCR: Multiple methods with intelligent fallback strategies")
        print("🔧 Corrupted OCR Recovery: Fixes common misreadings (S64→864, B72→872)")
        print("🛠️ Stability Protection: Requires confirmation for dramatic HP drops (prevents false F6)")
        print("⚡ Smart failure tracking: Warns after 5 consecutive OCR failures")
        print("📝 Debug logging: Detailed OCR analysis saved to game_helper_debug.log")
        print("Press Ctrl+C to quit")
        print()
        
        self.debug_log("=== MONITORING STARTED ===")
        self.debug_log(f"Monitor frequency: Every 0.05 seconds (20 Hz) - ENHANCED OCR")
        self.debug_log(f"Regions: HP{self.hp_region}, Mana{self.mana_region}")
        
        try:
            while self.running:
                hp_value, mana_value = self.get_hp_mana_values()
                self.display_status(hp_value, mana_value)
                self.check_and_respond(hp_value, mana_value)
                
                # Monitor every 0.05 seconds (20 times per second) - BALANCED SPEED
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nStopped by user")
            self.debug_log("=== MONITORING STOPPED BY USER ===")
        except pyautogui.FailSafeException:
            print("\nFail-safe triggered! Mouse moved to corner.")
            self.debug_log("=== MONITORING STOPPED BY FAILSAFE ===")
        except Exception as e:
            print(f"\nError: {e}")
            self.debug_log(f"=== MONITORING STOPPED BY ERROR: {str(e)} ===")
        
        print("Game helper stopped.")
        self.debug_log("=== SESSION ENDED ===\n")

def main():
    print("=== Game Helper ===")
    print("This tool monitors your game's HP and Mana values and automatically presses hotkeys.")
    print()
    
    # Check if regions file exists
    import os
    if os.path.exists("regions.txt"):
        use_saved = input("Found saved regions from region selector. Use them? (y/n): ").lower().strip()
        if use_saved == 'y':
            try:
                with open("regions.txt", 'r') as f:
                    saved_regions = {}
                    for line in f:
                        if ':' in line:
                            name, region_str = line.strip().split(':', 1)
                            region = eval(region_str.strip())
                            saved_regions[name] = region
                
                if 'HP' in saved_regions and 'Mana' in saved_regions:
                    print("✅ Loaded saved regions!")
                    
                    try:
                        max_hp_input = input(f"Enter max HP (default {1415}): ").strip()
                        max_mana_input = input(f"Enter max mana (default {1224}): ").strip()
                        
                        max_hp = int(max_hp_input) if max_hp_input else 1415
                        max_mana = int(max_mana_input) if max_mana_input else 1224
                        
                    except ValueError:
                        print("Invalid input, using defaults")
                        max_hp = 1415
                        max_mana = 1224
                    
                    helper = RegionGameHelper()
                    helper.max_hp = max_hp
                    helper.max_mana = max_mana
                    helper.hp_region = saved_regions['HP']
                    helper.mana_region = saved_regions['Mana']
                    
                    print(f"\nConfigured with Max HP: {max_hp}, Max Mana: {max_mana}")
                    print(f"🎮 Smart Healing Strategy:")
                    print(f"   🚨 F6 (Critical): HP below {helper.hp_critical_threshold * 100}%")
                    print(f"   💊 F1 (Moderate): HP below {helper.hp_threshold * 100}% (but above {helper.hp_critical_threshold * 100}%)")
                    print(f"   💙 F4 (Mana): Mana below {helper.mana_threshold * 100}%")
                    print(f"⚡ Cooldown: {helper.cooldown}s between key presses")
                    print(f"🔄 Monitor frequency: Every 0.05 seconds (20 Hz) - ENHANCED OCR!")
                    print(f"📍 Using saved regions: HP{helper.hp_region}, Mana{helper.mana_region}")
                    
                    input("\nPress Enter to start monitoring...")
                    helper.run()
                    return
                    
            except Exception as e:
                print(f"❌ Error loading saved regions: {e}")
                print("Falling back to manual region selection...")
    
    # Manual region selection (original flow)
    try:
        max_hp_input = input(f"Enter max HP (default {1415}): ").strip()
        max_mana_input = input(f"Enter max mana (default {1224}): ").strip()
        
        max_hp = int(max_hp_input) if max_hp_input else 1415
        max_mana = int(max_mana_input) if max_mana_input else 1224
        
    except ValueError:
        print("Invalid input, using defaults")
        max_hp = 1415
        max_mana = 1224
    
    helper = RegionGameHelper()
    helper.max_hp = max_hp
    helper.max_mana = max_mana
    
    print(f"\nConfigured with Max HP: {max_hp}, Max Mana: {max_mana}")
    print(f"🎮 Smart Healing Strategy:")
    print(f"   🚨 F6 (Critical): HP below {helper.hp_critical_threshold * 100}%")
    print(f"   💊 F1 (Moderate): HP below {helper.hp_threshold * 100}% (but above {helper.hp_critical_threshold * 100}%)")
    print(f"   💙 F4 (Mana): Mana below {helper.mana_threshold * 100}%")
    print(f"⚡ Cooldown: {helper.cooldown}s between key presses")
    print(f"🔄 Monitor frequency: Every 0.05 seconds (20 Hz) - ENHANCED OCR!")
    
    helper.setup_regions()
    
    input("\nPress Enter to start monitoring...")
    helper.run()

if __name__ == "__main__":
    main() 