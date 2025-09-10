#!/bin/bash

# Installation script for Carnatic Music Detection standalone
echo "🎵 Installing Carnatic Music Detection System"
echo "============================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 first: https://python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install system dependencies on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS - checking for Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "📦 Installing audio dependencies..."
    brew install portaudio || echo "⚠️  PortAudio may already be installed"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux - installing audio dependencies..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-dev python3-pip
fi

# Install Python packages
echo "🐍 Installing Python dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📁 Creating virtual environment..."
    python3 -m venv .venv
fi

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages
echo "📦 Installing Python packages..."
pip install sounddevice numpy scipy

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎵 To run the Carnatic Music Detection System:"
echo "   1. Activate virtual environment: source .venv/bin/activate"
echo "   2. Run the detector: python3 standalone_carnatic.py"
echo ""
echo "🎼 Features:"
echo "   • Real-time 22-shruti detection"
echo "   • Raga context analysis"
echo "   • Professional terminal interface"
echo "   • Session recording and export"
echo ""
echo "🔧 If you encounter microphone issues:"
echo "   • Grant microphone access in System Preferences > Security & Privacy"
echo "   • Make sure your microphone is connected and working"
echo ""