#!/bin/bash

# Cleanup script for Raspberry Pi setup
# Run this before setup.sh to ensure a clean installation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "RPi Face Recognition Cleanup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "This script will clean up:"
echo "  - Old virtual environment (if exists)"
echo "  - Python cache files (__pycache__, *.pyc)"
echo "  - pip cache"
echo "  - Old build artifacts"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Step 1: Removing virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}→${NC} Removing venv directory..."
    rm -rf venv
    echo -e "${GREEN}✓${NC} Virtual environment removed"
else
    echo -e "${GREEN}✓${NC} No virtual environment found"
fi

echo ""
echo "Step 2: Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
echo -e "${GREEN}✓${NC} Python cache files cleaned"

echo ""
echo "Step 3: Cleaning pip cache..."
if command -v pip3 &> /dev/null; then
    pip3 cache purge 2>/dev/null || true
    echo -e "${GREEN}✓${NC} pip cache cleaned"
else
    echo -e "${YELLOW}⚠${NC} pip3 not found, skipping cache cleanup"
fi

echo ""
echo "Step 4: Removing build artifacts..."
rm -rf build/ dist/ *.egg-info 2>/dev/null || true
echo -e "${GREEN}✓${NC} Build artifacts removed"

echo ""
echo "Step 5: Cleaning temporary files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true
echo -e "${GREEN}✓${NC} Temporary files cleaned"

echo ""
echo "Step 6: Checking for old encodings (if any)..."
if [ -f "encodings/face_encodings.npz" ]; then
    echo -e "${YELLOW}⚠${NC} Found old encodings file (encodings/face_encodings.npz)"
    echo -e "${YELLOW}   ${NC} Note: Encodings are now handled by GPU server, this file is not needed on RPi"
    read -p "   Remove it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f encodings/face_encodings.npz
        echo -e "${GREEN}✓${NC} Old encodings file removed"
    else
        echo -e "${YELLOW}⚠${NC} Keeping old encodings file"
    fi
else
    echo -e "${GREEN}✓${NC} No old encodings found"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Cleanup Complete!${NC}"
echo "=========================================="
echo ""
echo "You can now run ./setup.sh for a fresh installation"
echo ""

