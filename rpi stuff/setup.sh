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

# Note: BLAS/LAPACK no longer needed (dlib removed)

# OpenCV dependencies
install_system_pkg "libjpeg-dev"
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
# Note: libatlas-base-dev no longer needed (dlib removed)
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
echo -e "${YELLOW}Note:${NC} This should be much faster now (no dlib compilation needed!)"
echo ""

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗${NC} requirements.txt not found in current directory"
    exit 1
fi

# Install packages from requirements.txt
echo "Installing all packages from requirements.txt..."
pip install -r requirements.txt || {
    echo -e "${RED}✗${NC} Failed to install Python packages"
    exit 1
}
echo -e "${GREEN}✓${NC} All Python packages installed"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Make sure the GPU server is running at 76.175.119.31:3005"
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the real-time recognition:"
echo "   cd encodings"
echo "   python run_realtime_recognition.py"
echo ""
echo "Note:"
echo "  - Make sure your webcam is connected and accessible"
echo "  - Face recognition is now handled by the GPU server"
echo "  - Dataset and encodings have been moved to GPU server"
echo ""

