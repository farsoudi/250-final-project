#!/bin/bash

# Setup script for Raspberry Pi face recognition project
# This script is idempotent - safe to run multiple times

# Don't use set -e since we handle errors gracefully in functions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "RPi Face Recognition Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if package is installed (Debian/Ubuntu)
package_installed() {
    dpkg -l | grep -q "^ii  $1 " 2>/dev/null
}

# Function to install system package if not installed
install_system_pkg() {
    if package_installed "$1"; then
        echo -e "${GREEN}✓${NC} $1 is already installed"
        return 0
    else
        echo -e "${YELLOW}→${NC} Installing $1..."
        sudo apt install -y "$1" || {
            echo -e "${RED}✗${NC} Failed to install $1"
            return 1
        }
        echo -e "${GREEN}✓${NC} $1 installed successfully"
        return 0
    fi
}

# Function to install system package with fallback
install_system_pkg_with_fallback() {
    local pkg="$1"
    local fallback="$2"
    
    if package_installed "$pkg"; then
        echo -e "${GREEN}✓${NC} $pkg is already installed"
        return 0
    fi
    
    echo -e "${YELLOW}→${NC} Installing $pkg..."
    if sudo apt install -y "$pkg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $pkg installed successfully"
        return 0
    else
        if [ -n "$fallback" ]; then
            echo -e "${YELLOW}→${NC} $pkg not available, trying fallback: $fallback..."
            if sudo apt install -y "$fallback" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $fallback installed successfully (replacement for $pkg)"
                return 0
            fi
        fi
        echo -e "${YELLOW}⚠${NC} $pkg not available (and fallback failed if provided) - continuing anyway"
        return 0  # Don't fail, some packages are optional
    fi
}

# Function to install optional package (won't fail script if missing)
install_optional_pkg() {
    if package_installed "$1"; then
        echo -e "${GREEN}✓${NC} $1 is already installed"
        return 0
    else
        echo -e "${YELLOW}→${NC} Installing $1 (optional)..."
        if sudo apt install -y "$1" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $1 installed successfully"
        else
            echo -e "${YELLOW}⚠${NC} $1 not available - skipping (optional package)"
        fi
        return 0
    fi
}

echo "Step 1: Updating package lists..."
sudo apt update -qq || {
    echo -e "${RED}✗${NC} Failed to update package lists"
    exit 1
}
echo -e "${GREEN}✓${NC} Package lists updated"
echo ""

echo "Step 2: Installing system dependencies..."
echo "----------------------------------------"

# Essential build tools
install_system_pkg "build-essential" || exit 1
install_system_pkg "python3-dev" || exit 1
install_system_pkg "cmake" || exit 1
install_system_pkg "pkg-config" || exit 1
install_system_pkg "git" || exit 1

# BLAS/LAPACK for dlib
install_system_pkg "libopenblas-dev" || exit 1
install_system_pkg "liblapack-dev" || exit 1

# OpenCV dependencies
install_system_pkg "libjpeg-dev" || exit 1
install_system_pkg "libtiff5-dev" || exit 1
install_system_pkg "libjasper-dev" || exit 1
install_system_pkg "libpng-dev" || exit 1
install_system_pkg "libavcodec-dev" || exit 1
install_system_pkg "libavformat-dev" || exit 1
install_system_pkg "libswscale-dev" || exit 1
install_system_pkg "libv4l-dev" || exit 1
install_system_pkg "libxvidcore-dev" || exit 1
install_system_pkg "libx264-dev" || exit 1
install_system_pkg "libfontconfig1-dev" || exit 1
install_system_pkg "libcairo2-dev" || exit 1
install_system_pkg_with_fallback "libgdk-pixbuf2.0-dev" "libgdk-pixbuf-xlib-2.0-dev"
install_system_pkg "libpango1.0-dev" || exit 1
install_optional_pkg "libgtk2.0-dev"
install_optional_pkg "libgtk-3-dev"
install_system_pkg "libatlas-base-dev" || exit 1
install_system_pkg "libgstreamer1.0-dev" || exit 1
install_system_pkg "libgstreamer-plugins-base1.0-dev" || exit 1

echo ""
echo -e "${GREEN}✓${NC} All system dependencies installed"
echo ""

echo "Step 3: Setting up Python virtual environment..."
echo "----------------------------------------"

# Check if venv exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
else
    echo -e "${YELLOW}→${NC} Creating virtual environment..."
    python3 -m venv venv || {
        echo -e "${RED}✗${NC} Failed to create virtual environment"
        exit 1
    }
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate venv
echo -e "${YELLOW}→${NC} Activating virtual environment..."
source venv/bin/activate || {
    echo -e "${RED}✗${NC} Failed to activate virtual environment"
    exit 1
}
echo -e "${GREEN}✓${NC} Virtual environment activated"
echo ""

echo "Step 4: Upgrading pip and setuptools..."
echo "----------------------------------------"
pip install --quiet --upgrade pip setuptools wheel || {
    echo -e "${RED}✗${NC} Failed to upgrade pip"
    exit 1
}
echo -e "${GREEN}✓${NC} pip upgraded"
echo ""

echo "Step 5: Installing Python packages..."
echo "----------------------------------------"
echo -e "${YELLOW}Note:${NC} This may take 30-60 minutes, especially for dlib compilation"
echo ""

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗${NC} requirements.txt not found in current directory"
    exit 1
fi

# Install packages one by one for better error handling
echo "Installing core dependencies..."
pip install --quiet numpy requests || {
    echo -e "${RED}✗${NC} Failed to install numpy/requests"
    exit 1
}
echo -e "${GREEN}✓${NC} numpy, requests installed"

echo "Installing OpenCV..."
pip install --quiet opencv-python || {
    echo -e "${RED}✗${NC} Failed to install opencv-python"
    exit 1
}
echo -e "${GREEN}✓${NC} opencv-python installed"

echo "Installing Hugging Face Hub..."
pip install --quiet huggingface_hub || {
    echo -e "${RED}✗${NC} Failed to install huggingface_hub"
    exit 1
}
echo -e "${GREEN}✓${NC} huggingface_hub installed"

echo "Installing Ultralytics (this may take a few minutes)..."
pip install --quiet ultralytics || {
    echo -e "${RED}✗${NC} Failed to install ultralytics"
    exit 1
}
echo -e "${GREEN}✓${NC} ultralytics installed"

echo "Installing supervision..."
pip install --quiet supervision || {
    echo -e "${RED}✗${NC} Failed to install supervision"
    exit 1
}
echo -e "${GREEN}✓${NC} supervision installed"

echo "Installing cmake (Python package)..."
pip install --quiet cmake || {
    echo -e "${RED}✗${NC} Failed to install cmake"
    exit 1
}
echo -e "${GREEN}✓${NC} cmake installed"

echo "Installing dlib (THIS WILL TAKE 30-60 MINUTES - compiling from source)..."
echo -e "${YELLOW}→${NC} Please be patient, dlib compilation is CPU-intensive..."
pip install --no-cache-dir dlib || {
    echo -e "${RED}✗${NC} Failed to install dlib"
    echo -e "${YELLOW}Tip:${NC} Make sure all system dependencies are installed"
    exit 1
}
echo -e "${GREEN}✓${NC} dlib installed successfully"

echo "Installing face_recognition..."
pip install --quiet face_recognition || {
    echo -e "${RED}✗${NC} Failed to install face_recognition"
    exit 1
}
echo -e "${GREEN}✓${NC} face_recognition installed"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Build face encodings (if not already done):"
echo "   cd encodings"
echo "   python run_build_encodings.py"
echo "   cd .."
echo ""
echo "3. Run the real-time recognition:"
echo "   cd encodings"
echo "   python run_realtime_recognition.py"
echo ""
echo "Note: Make sure your webcam is connected and accessible"
echo ""

