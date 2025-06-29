#!/bin/bash

echo "=== Game Helper Setup for macOS ==="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew is already installed"
fi

# Install Tesseract OCR
echo ""
echo "Installing Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    brew install tesseract
else
    echo "✓ Tesseract is already installed"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To run the game helper:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the helper: python3 game_helper_region.py"
echo ""
echo "Or use the quick command:"
echo "  source venv/bin/activate && python3 game_helper_region.py"
echo ""
echo "Make sure your game is running and visible before starting the helper." 