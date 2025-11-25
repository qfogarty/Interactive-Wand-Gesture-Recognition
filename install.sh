#!/bin/bash

# Interactive Wand Project - Automated Installation Script
# This script sets up the project environment on Raspberry Pi 5

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${PROJECT_DIR}/config.yaml"

# Banner
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Interactive Wand Project - Installer      ║${NC}"
echo -e "${BLUE}║   Raspberry Pi 5 Setup                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: This script is designed for Raspberry Pi 5${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}✗ Please run this script as a regular user (not root or sudo)${NC}"
    echo -e "  The script will prompt for sudo when needed."
    exit 1
fi

echo -e "${GREEN}✓ Running from: ${PROJECT_DIR}${NC}"
echo ""

# ============================================================================
# STEP 1: System Update
# ============================================================================
echo -e "${BLUE}[1/7] Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✓ System updated${NC}"
echo ""

# ============================================================================
# STEP 2: Install System Dependencies
# ============================================================================
echo -e "${BLUE}[2/7] Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-picamera2 \
    python3-pygame \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libopenblas-dev \
    gfortran \
    python3-yaml

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

# ============================================================================
# STEP 3: Install Python Packages
# ============================================================================
echo -e "${BLUE}[3/7] Installing Python packages...${NC}"
pip3 install --upgrade pip
pip3 install \
    numpy \
    opencv-python \
    "scikit-learn>=1.6.0" \
    joblib \
    pillow \
    pandas \
    pyyaml \
    pi5neo

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# ============================================================================
# STEP 4: Enable Hardware Interfaces
# ============================================================================
echo -e "${BLUE}[4/7] Configuring hardware interfaces...${NC}"

# Check and enable SPI
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt; then
    echo -e "${YELLOW}  Enabling SPI interface...${NC}"
    echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo -e "${GREEN}  ✓ SPI enabled (reboot required)${NC}"
else
    echo -e "${GREEN}  ✓ SPI already enabled${NC}"
fi

# Check and enable Camera
if ! grep -q "^camera_auto_detect=1" /boot/firmware/config.txt; then
    echo -e "${YELLOW}  Enabling Camera...${NC}"
    echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo -e "${GREEN}  ✓ Camera enabled (reboot required)${NC}"
else
    echo -e "${GREEN}  ✓ Camera already enabled${NC}"
fi

# Add user to required groups
echo -e "${YELLOW}  Adding user to hardware groups...${NC}"
sudo usermod -a -G spi,gpio,video "$USER"
echo -e "${GREEN}  ✓ User added to spi, gpio, video groups${NC}"

echo ""

# ============================================================================
# STEP 5: Verify Configuration File
# ============================================================================
echo -e "${BLUE}[5/7] Verifying configuration...${NC}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ config.yaml not found!${NC}"
    echo -e "  Expected at: ${CONFIG_FILE}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration file found${NC}"

# Test config loading
python3 << EOF
try:
    from config_loader import get_config
    config = get_config()
    print("  ✓ Configuration loaded successfully")
    print(f"  Project: {config.project.name} v{config.project.version}")
    print(f"  LED Count: {config.hardware.led.count}")
except Exception as e:
    print(f"  ✗ Configuration error: {e}")
    exit(1)
EOF

echo ""

# ============================================================================
# STEP 6: Validate Assets
# ============================================================================
echo -e "${BLUE}[6/7] Validating project assets...${NC}"

python3 << EOF
import sys
from pathlib import Path
from config_loader import get_config

config = get_config()
missing = config.validate_assets()

if missing:
    print("${YELLOW}⚠️  Missing assets:${NC}")
    for item in missing:
        print(f"  - {item}")
    print()
    print("${YELLOW}Note: You may need to:${NC}")
    print("  1. Train your model: cd DatasetCreation && python3 train_spell_classifier.py")
    print("  2. Ensure sound files are in the Sounds/ directory")
else:
    print("${GREEN}✓ All required assets found${NC}")
EOF

echo ""

# ============================================================================
# STEP 7: Final Setup
# ============================================================================
echo -e "${BLUE}[7/7] Final setup steps...${NC}"

# Create necessary directories
mkdir -p "${PROJECT_DIR}/DatasetCreation/spells_dataset"
echo -e "${GREEN}✓ Created dataset directory${NC}"

# Set executable permissions
chmod +x "${PROJECT_DIR}/harry_potter_wand_cv.py"
chmod +x "${PROJECT_DIR}/harry_potter_wand_sklearn.py"
echo -e "${GREEN}✓ Set executable permissions${NC}"

echo ""

# ============================================================================
# Installation Complete
# ============================================================================
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Installation Complete! ✓            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Check if reboot is needed
REBOOT_NEEDED=false
if ! groups | grep -q spi; then
    REBOOT_NEEDED=true
fi

if [ "$REBOOT_NEEDED" = true ]; then
    echo -e "${YELLOW}⚠️  REBOOT REQUIRED${NC}"
    echo -e "  Hardware permissions and interfaces require a reboot to take effect."
    echo ""
    read -p "Reboot now? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo -e "${BLUE}Rebooting...${NC}"
        sudo reboot
    else
        echo -e "${YELLOW}Please reboot manually before running the wand tracking system.${NC}"
    fi
else
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. ${BLUE}Configure your setup:${NC} python3 setup_wizard.py"
    echo -e "  2. ${BLUE}Train your model (optional):${NC} cd DatasetCreation && python3 train_spell_classifier.py"
    echo -e "  3. ${BLUE}Test the setup:${NC} python3 test_setup.py"
    echo -e "  4. ${BLUE}Run the wand tracker:${NC} python3 harry_potter_wand_cv.py"
    echo ""
    echo -e "For help: ${BLUE}./install.sh --help${NC} or check ${BLUE}docs/CONFIGURATION.md${NC}"
fi

echo ""
echo -e "${GREEN}Happy spell casting! 🪄✨${NC}"
