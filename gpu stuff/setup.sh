#!/bin/bash

# Setup script for GPU Server Face Recognition Service (Fedora)
# This script is idempotent - safe to run multiple times

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "GPU Server Face Recognition Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if package is installed (Fedora/RHEL)
package_installed() {
    rpm -q "$1" >/dev/null 2>&1
}

# Function to install system package if not installed
install_system_pkg() {
    if package_installed "$1"; then
        echo -e "${GREEN}✓${NC} $1 is already installed"
        return 0
    else
        echo -e "${YELLOW}→${NC} Installing $1..."
        sudo dnf install -y "$1" || {
            echo -e "${RED}✗${NC} Failed to install $1"
            return 1
        }
        echo -e "${GREEN}✓${NC} $1 installed successfully"
        return 0
    fi
}

echo "Step 1: Updating package lists..."
sudo dnf check-update -q || true  # Don't fail if updates available
echo -e "${GREEN}✓${NC} Package lists checked"
echo ""

echo "Step 2: Installing system dependencies..."
echo "----------------------------------------"

# Essential build tools
install_system_pkg "python3-devel" || exit 1
install_system_pkg "gcc" || exit 1
install_system_pkg "gcc-c++" || exit 1
install_system_pkg "cmake" || exit 1
install_system_pkg "pkgconfig" || exit 1
install_system_pkg "git" || exit 1

# OpenCV dependencies
install_system_pkg "libjpeg-turbo-devel" || exit 1
install_system_pkg "libtiff-devel" || exit 1
install_system_pkg "libpng-devel" || exit 1
install_system_pkg "openblas-devel" || exit 1
install_system_pkg "lapack-devel" || exit 1

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
echo -e "${YELLOW}Note:${NC} This should be fast on x86_64 (pre-built wheels available)"
echo ""

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗${NC} requirements.txt not found in current directory"
    exit 1
fi

# Install packages
echo "Installing all packages from requirements.txt..."
pip install -r requirements.txt || {
    echo -e "${RED}✗${NC} Failed to install Python packages"
    exit 1
}
echo -e "${GREEN}✓${NC} All Python packages installed"
echo ""

echo "Step 6: Creating encodings directory..."
mkdir -p encodings
echo -e "${GREEN}✓${NC} Encodings directory created"
echo ""

echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy the dataset from RPi or ensure it's accessible"
echo "2. Build face encodings:"
echo "   source venv/bin/activate"
echo "   python build_encodings.py"
echo ""
echo "3. Run the face recognition service:"
echo "   source venv/bin/activate"
echo "   python face_recognition_service.py"
echo ""
echo "The service will run on 0.0.0.0:3005"
echo ""

