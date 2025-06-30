"""
Processing Components

This package contains the processing components:
- OCRProcessor: OCR and image processing logic
- RegionManager: Screen region selection and management
"""

from .ocr_processor import OCRProcessor
from .region_manager import RegionManager

__all__ = ['OCRProcessor', 'RegionManager'] 