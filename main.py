#!/usr/bin/env python3
"""
Game Helper - Modular Version

This is the main entry point for the refactored game helper tool.
The original monolithic file has been split into multiple classes for better organization:

- config.py: Configuration management
- debug_logger.py: Debug logging functionality  
- ocr_processor.py: OCR and image processing
- region_manager.py: Region selection and management
- health_monitor.py: HP monitoring and healing logic
- mana_monitor.py: Mana monitoring and restoration logic
- game_helper.py: Main orchestrator class

Usage:
    python main.py

The tool will guide you through setup and then monitor your game's HP/Mana values,
automatically pressing hotkeys when healing or mana restoration is needed.
"""

from src.core.game_helper import main

if __name__ == "__main__":
    main() 