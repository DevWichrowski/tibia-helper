# Game Helper - Refactored Modular Version

The original `game_helper_region.py` file has been refactored into multiple, well-organized classes with a clean folder structure for better maintainability and separation of concerns.

## 📁 Organized File Structure

```
auto-h/
├── main.py                          # 🚀 Main entry point
├── requirements.txt                 # 📦 Dependencies  
├── regions.txt                      # 💾 Saved regions (auto-generated)
│
├── src/                            # 📂 Source code
│   ├── __init__.py
│   ├── core/                       # 🎯 Core components
│   │   ├── __init__.py
│   │   ├── config.py               # ⚙️ Configuration management
│   │   ├── debug_logger.py         # 📝 Debug logging functionality
│   │   └── game_helper.py          # 🎮 Main orchestrator class
│   │
│   ├── monitors/                   # 👁️ Monitoring components
│   │   ├── __init__.py
│   │   ├── health_monitor.py       # ❤️ HP monitoring and healing logic
│   │   └── mana_monitor.py         # 💙 Mana monitoring and restoration
│   │
│   └── processing/                 # 🔧 Processing components
│       ├── __init__.py
│       ├── ocr_processor.py        # 👀 OCR and image processing
│       └── region_manager.py       # 📐 Screen region management
│
├── debug/                          # 🐛 Debug files (auto-generated)
│   ├── README.md                   # 📖 Debug folder documentation
│   ├── images/                     # 📸 OCR debug images
│   │   ├── HP_original.png         # 🖼️ Original HP screenshots
│   │   ├── HP_OTSU.png            # 🖼️ OCR preprocessing results
│   │   └── Mana_*.png             # 🖼️ Mana OCR debug images
│   └── logs/                       # 📝 Application logs
│       └── game_helper_debug.log   # 📄 Detailed debug information
│
├── docs/                           # 📚 Documentation
│   └── README_REFACTORED.md        # 📖 This file
│
└── legacy/                         # 🗂️ Original files (preserved)
    ├── game_helper_region.py       # 📜 Original monolithic version
    └── region_selector.py          # 🔍 Region selection utility
```

## 🏗️ Architecture Overview

```
main.py
└── src/
    └── core/
        └── GameHelper (Main Orchestrator)
            ├── GameConfig (core/config.py)
            ├── DebugLogger (core/debug_logger.py)
            ├── OCRProcessor (processing/ocr_processor.py)
            ├── RegionManager (processing/region_manager.py)  
            ├── HealthMonitor (monitors/health_monitor.py)
            └── ManaMonitor (monitors/mana_monitor.py)
```

## 🎯 Package Responsibilities

### 📂 `src/core/` - Core Components
- **`config.py`** (`GameConfig`) - Centralized configuration management
- **`debug_logger.py`** (`DebugLogger`) - Timestamped debug logging
- **`game_helper.py`** (`GameHelper`) - Main orchestrator and UI

### 👁️ `src/monitors/` - Monitoring Components  
- **`health_monitor.py`** (`HealthMonitor`) - HP monitoring, healing logic, stability protection
- **`mana_monitor.py`** (`ManaMonitor`) - Mana monitoring, restoration logic, failure tracking

### 🔧 `src/processing/` - Processing Components
- **`ocr_processor.py`** (`OCRProcessor`) - OCR methods, image processing, text recovery
- **`region_manager.py`** (`RegionManager`) - Region selection, testing, save/load

### 📚 `docs/` - Documentation
- **`README_REFACTORED.md`** - This documentation file

### 🗂️ `legacy/` - Original Files (Preserved)
- **`game_helper_region.py`** - Original monolithic version (still functional)
- **`region_selector.py`** - Original region selection utility

## 🚀 Usage

### New Organized Version:
```bash
python main.py
```

### Original Legacy Version:
```bash
python legacy/game_helper_region.py
```

## ✨ Benefits of Organized Structure

1. **🗂️ Clear Organization** - Logical grouping of related functionality
2. **🔍 Easy Navigation** - Find components quickly by purpose
3. **📦 Proper Packaging** - Python packages with `__init__.py` files
4. **🧪 Better Testing** - Each package can be tested independently  
5. **📈 Scalability** - Easy to add new monitors or processors
6. **👥 Team Development** - Multiple developers can work on different packages
7. **🔧 Maintainability** - Clear separation makes updates easier

## 🎮 All Features Preserved

✅ **Enhanced OCR** - Multiple methods with intelligent fallback strategies  
✅ **Corrupted Recovery** - Fixes common misreadings (S64→864, B72→872)  
✅ **Stability Protection** - Requires confirmation for dramatic HP drops  
✅ **Smart Healing** - F6 critical, F1 moderate, F4 mana restoration  
✅ **Debug Logging** - Detailed OCR analysis and decision tracking  
✅ **Region Management** - Interactive selection, testing, save/load  
✅ **Failure Tracking** - Warns after consecutive OCR failures  
✅ **Backward Compatibility** - Works with existing `regions.txt` files

## 🔧 Easy Configuration

Modify settings in `src/core/config.py`:

```python
class GameConfig:
    def __init__(self):
        # Healing thresholds
        self.hp_threshold = 0.83          # 83% - moderate healing
        self.hp_critical_threshold = 0.55  # 55% - critical healing  
        self.mana_threshold = 0.55         # 55% - mana restoration
        
        # Key mappings  
        self.heal_key = 'f1'              # Moderate healing
        self.critical_heal_key = 'f6'     # Critical healing
        self.mana_key = 'f4'              # Mana restoration
        
        # Timing
        self.cooldown = 0.2               # Seconds between key presses
        self.monitor_frequency = 0.05      # Monitor every 0.05s (20 Hz)
```

## 🤝 Contributing Made Easy

The organized structure makes contributions straightforward:

- **Add OCR methods** → `src/processing/ocr_processor.py`
- **New healing strategies** → `src/monitors/health_monitor.py`  
- **Additional monitors** → Create new file in `src/monitors/`
- **Configuration options** → `src/core/config.py`
- **Enhanced logging** → `src/core/debug_logger.py`
- **New processors** → Create new file in `src/processing/`

## 📊 Migration Notes

- ✅ Original `legacy/game_helper_region.py` remains fully functional
- ✅ All saved regions (`regions.txt`) work with both versions
- ✅ Debug logs maintain the same format and location
- ✅ No changes to user interface or workflow
- ✅ Same dependencies in `requirements.txt`

## 🎯 Import Examples

```python
# Import the main class
from src.core import GameHelper

# Import specific components
from src.core import GameConfig, DebugLogger
from src.monitors import HealthMonitor, ManaMonitor  
from src.processing import OCRProcessor, RegionManager

# Use the organized structure
game_helper = GameHelper()
game_helper.run()
```

The organized folder structure makes the codebase much more professional, maintainable, and easier to navigate! 