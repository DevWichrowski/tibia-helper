import cv2
import numpy as np
import pytesseract
import pyautogui
import re
import datetime
from collections import Counter


class OCRProcessor:
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        
    def debug_log(self, message):
        """Write debug message through the logger"""
        if self.debug_logger:
            self.debug_logger.log(message)
    
    def parse_health_value(self, text, value_type="unknown"):
        """Parse health value from OCR text - handles corrupted OCR readings"""
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
        corrupted_patterns = [
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
                    digit_match = re.search(r'(\d{3,4})', fixed_text)
                    if digit_match:
                        result = int(digit_match.group(1))
                        max_value = self.config.max_hp
                        if 1 <= result <= max_value:
                            self.debug_log(f"PARSE {value_type.upper()}: Fixed corrupted text to: {result}")
                            return result
            except:
                continue
        
        # Pattern 4: Any digits (last resort - take the largest)
        all_numbers = re.findall(r'\d+', text)
        if all_numbers:
            numbers = [int(num) for num in all_numbers if 100 <= int(num) <= self.config.max_hp]
            if numbers:
                result = max(numbers)
                self.debug_log(f"PARSE {value_type.upper()}: Found largest valid number: {result}")
                return result
            
        self.debug_log(f"PARSE {value_type.upper()}: No valid patterns found")
        return None
    
    def extract_number_from_region(self, region, value_type="unknown"):
        """Extract number from screen region using OCR"""
        if not region:
            self.debug_log(f"OCR {value_type.upper()}: No region defined")
            return None
            
        self.debug_log(f"OCR {value_type.upper()}: Starting extraction from region {region}")
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            methods = [
                ("OTSU", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                ("InvOTSU", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
                ("LowContrast", cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]),
                ("HighContrast", cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]),
                ("Adaptive", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
            ]
            
            valid_results = []
            all_results = []
            
            for method_name, thresh in methods:
                result = self._ocr_from_image(thresh, fast_mode=True, value_type=value_type)
                
                max_value = self.config.max_hp
                if result is not None and 1 <= result <= max_value:
                    valid_results.append(result)
                    self.debug_log(f"OCR {value_type.upper()}: {method_name} method SUCCESS: {result}")
                    
                    if len(valid_results) >= 2:
                        counts = Counter(valid_results)
                        most_common = counts.most_common(1)[0][0]
                        self.debug_log(f"OCR {value_type.upper()}: Multiple valid results, returning most common: {most_common}")
                        return most_common
                elif result is not None:
                    all_results.append(result)
                    
            if valid_results:
                result = valid_results[0]
                self.debug_log(f"OCR {value_type.upper()}: Single valid result: {result}")
                return result
            
            if all_results:
                if value_type == "hp":
                    valid_results = [r for r in all_results if 100 <= r <= self.config.max_hp]
                    if valid_results:
                        counts = Counter(valid_results)
                        final_result = counts.most_common(1)[0][0]
                        self.debug_log(f"OCR {value_type.upper()}: Final result selected: {final_result}")
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
                scale_factors = [3, 5, 8]
                configs = [
                    '--psm 8 -c tesseract_char_whitelist=0123456789',
                    '--psm 7 -c tesseract_char_whitelist=0123456789',
                    '--psm 6 -c tesseract_char_whitelist=0123456789'
                ]
            else:
                scale_factors = [5, 8, 10]
                configs = [
                    '--psm 8 -c tesseract_char_whitelist=0123456789',
                    '--psm 7 -c tesseract_char_whitelist=0123456789',
                    '--psm 6 -c tesseract_char_whitelist=0123456789',
                    '--psm 13 -c tesseract_char_whitelist=0123456789'
                ]
            
            height, width = thresh.shape
            
            for scale_factor in scale_factors:
                scaled = cv2.resize(thresh, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
                
                if not fast_mode:
                    kernel = np.ones((2,2), np.uint8)
                    cleaned = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
                    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
                    cleaned = cv2.GaussianBlur(cleaned, (3, 3), 0)
                else:
                    cleaned = scaled
                
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(cleaned, config=config).strip()
                        if text and len(text) > 0:
                            all_texts.append(text)
                            self.debug_log(f"OCR {value_type.upper()}: Scale {scale_factor}, Config {config.split()[0]}: '{text}'")
                            
                            parsed_value = self.parse_health_value(text, value_type)
                            if parsed_value and 100 <= parsed_value <= self.config.max_hp:
                                self.debug_log(f"OCR {value_type.upper()}: SUCCESS - Found valid value {parsed_value}")
                                return parsed_value
                    except Exception as e:
                        self.debug_log(f"OCR {value_type.upper()}: Config {config} failed: {str(e)}")
                        continue
            
            self.debug_log(f"OCR {value_type.upper()}: Trying to parse from all texts: {all_texts}")
            for text in all_texts:
                parsed_value = self.parse_health_value(text, value_type)
                if parsed_value and 100 <= parsed_value <= self.config.max_hp:
                    self.debug_log(f"OCR {value_type.upper()}: FALLBACK SUCCESS - Found valid value {parsed_value}")
                    return parsed_value
                    
        except Exception as e:
            self.debug_log(f"OCR {value_type.upper()}: Exception in _ocr_from_image: {str(e)}")
        
        self.debug_log(f"OCR {value_type.upper()}: No valid values found from any method")
        return None
    
    def extract_number_with_fallback(self, region, value_type="unknown"):
        """Enhanced OCR with fallback strategies for better reliability"""
        if not region:
            self.debug_log(f"FALLBACK {value_type.upper()}: No region defined")
            return None
            
        result = self.extract_number_from_region(region, value_type)
        if result is not None:
            self.debug_log(f"FALLBACK {value_type.upper()}: Normal OCR succeeded: {result}")
            return result
        
        self.debug_log(f"FALLBACK {value_type.upper()}: Normal OCR failed, trying fallback strategies")
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            fallback_methods = [
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1],
                gray
            ]
            
            for i, processed_img in enumerate(fallback_methods):
                try:
                    text = pytesseract.image_to_string(processed_img, config='--psm 8 -c tesseract_char_whitelist=0123456789').strip()
                    if text:
                        self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} raw text: '{text}'")
                        parsed = self.parse_health_value(text, value_type)
                        max_value = self.config.max_hp
                        if parsed and 1 <= parsed <= max_value:
                            self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} SUCCESS: {parsed}")
                            return parsed
                except Exception as e:
                    self.debug_log(f"FALLBACK {value_type.upper()}: Method {i+1} failed: {str(e)}")
                    continue
            
            self.debug_log(f"FALLBACK {value_type.upper()}: Trying number extraction from corrupted readings")
            
            for processed_img in fallback_methods:
                try:
                    text = pytesseract.image_to_string(processed_img, config='--psm 7').strip()
                    if text:
                        self.debug_log(f"FALLBACK {value_type.upper()}: Corrupted text analysis: '{text}'")
                        digit_sequences = re.findall(r'\d+', text)
                        if digit_sequences:
                            for seq in digit_sequences:
                                if len(seq) >= 3:
                                    num = int(seq)
                                    max_value = self.config.max_hp
                                    if 1 <= num <= max_value:
                                        self.debug_log(f"FALLBACK {value_type.upper()}: Extracted number from corrupted text: {num}")
                                        return num
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.debug_log(f"FALLBACK {value_type.upper()}: Exception in fallback: {str(e)}")
        
        self.debug_log(f"FALLBACK {value_type.upper()}: All strategies failed")
        return None 