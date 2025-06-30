# Game Helper

An automated game helper that monitors your HP and Mana values and automatically presses hotkeys when they drop below specified thresholds.

## Features

- **HP Monitoring**: Automatically presses F1 when HP drops below 80%
- **Mana Monitoring**: Automatically presses F4 when Mana drops below 70%
- **Customizable Thresholds**: Set your own max HP/Mana values
- **Cooldown Protection**: Prevents spam-clicking with 2-second cooldown
- **Manual Region Selection**: Precise monitoring by selecting exact screen regions
- **Safety Features**: Emergency stop and fail-safe mechanisms
- **macOS Compatible**: No root permissions required

## Prerequisites

### System Requirements
- Python 3.7+
- Tesseract OCR installed on your system

### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Game Helper:**
   - `game_helper_region.py` - Manual region selection for precise monitoring

## Usage

### Starting the Game Helper

**Important**: You must activate the virtual environment first, then run the helper:

```bash
# For perfect OCR accuracy (recommended first time):
source venv/bin/activate && python3 region_selector.py

# Then run the main helper:
source venv/bin/activate && python3 game_helper_region.py
```

### Setup Steps:
1. Enter your max HP and Mana values (defaults to 1415 HP, 1224 Mana)
2. For each region (HP, then Mana):
   - Position mouse at TOP-LEFT corner of the number
   - Press ENTER
   - Position mouse at BOTTOM-RIGHT corner of the number
   - Press ENTER
3. Press Enter to start monitoring
4. Press Ctrl+C to quit

### Detection Status:
- **[✓]** = Value detected successfully in real-time
- **[✗]** = Using cached value (detection failed)

## 🔧 Region Selector Tool (Recommended!)

If OCR readings are inaccurate (wrong numbers), use the advanced region selector:

```bash
source venv/bin/activate && python3 region_selector.py
```

### Features:
- **Visual testing** of OCR on selected regions
- **Fine-tuning** with smaller/larger/moved regions  
- **Multiple preprocessing methods** to find what works best
- **Saves processed images** so you can see what OCR sees
- **Saves perfect regions** to `regions.txt` for reuse
- **Interactive adjustment** until OCR reads correctly

### After using region selector:
The main game helper will automatically detect and offer to use the saved regions!

## Configuration

### Default Settings
- **HP Threshold**: 80% (presses F1)
- **Mana Threshold**: 70% (presses F4)
- **Cooldown**: 2 seconds between key presses
- **Monitor Frequency**: Every 0.5 seconds

### Customizing Thresholds

You can modify the thresholds in the code:

```python
self.hp_threshold = 0.8    # 80%
self.mana_threshold = 0.7  # 70%
self.cooldown = 2          # seconds
```

## Safety Features

- **Fail-safe**: Move mouse to top-left corner of screen to emergency stop
- **Keyboard Interrupt**: Press Ctrl+C to stop
- **Cooldown**: Prevents spam-clicking with configurable delay
- **No Root Permissions**: Works without administrator privileges on macOS

## Troubleshooting

### OCR Reading Wrong Values (7, 109 instead of 1224)
1. **Use the region selector tool**: `python3 region_selector.py`
2. **Select smaller regions** containing only the number digits
3. **Check generated PNG files** to see what OCR is actually reading
4. **Avoid including**: UI decorations, labels, or nearby numbers
5. **Ensure good contrast** between text and background

### Keys Not Being Pressed
1. Ensure the script has focus (try running as administrator on Windows)
2. Check that F1/F4 are the correct keys for your game
3. Verify the game is accepting input

### Region Selection Issues
1. Make sure the selected regions contain only the numeric values
2. Ensure there's good contrast between text and background
3. Try selecting a slightly larger region if numbers aren't being detected

## Advanced Usage

### Custom Key Bindings

To change the keys pressed, modify these lines:

```python
# In check_and_respond method
self.last_f1_press = self.press_key_with_cooldown('f1', self.last_f1_press)  # Change 'f1'
self.last_f4_press = self.press_key_with_cooldown('f4', self.last_f4_press)  # Change 'f4'
```

### Multiple Thresholds

You can add additional thresholds by modifying the `check_and_respond` method:

```python
if hp_percentage < 0.5:  # 50% HP - emergency healing
    self.press_key_with_cooldown('f2', self.last_f2_press)
```

## Files

- `game_helper_region.py` - Main game helper with manual region selection
- `region_selector.py` - **NEW!** Advanced region selection tool with OCR testing
- `requirements.txt` - Python dependencies
- `setup_macos.sh` - Automated setup script for macOS
- `README.md` - This documentation

## Legal Notice

This tool is for educational purposes. Make sure using automation tools complies with your game's Terms of Service. 


## Start with
source venv/bin/activate && python3 main.py