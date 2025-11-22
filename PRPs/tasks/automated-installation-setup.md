# TASK PRP: Automated Installation & Configuration Setup

## 📋 Task Overview

**Goal:** Create an automated installation system that eliminates manual path configuration and simplifies project setup for new users.

**Current Pain Points:**
- Hardcoded paths in 3 Python files require manual editing
- No validation that assets exist before runtime
- Manual dependency installation prone to errors
- No configuration file for user preferences
- First-run experience requires reading 500+ line README

**Target User Experience:**
```bash
git clone <repo-url> WandProject
cd WandProject
./install.sh
# ✓ All dependencies installed
# ✓ Paths automatically configured
# ✓ Assets validated
# ✓ Hardware tested
# → Ready to run!
python3 wand.py
```

## 🎯 Success Criteria

- [ ] Single command installation (`./install.sh`)
- [ ] Zero hardcoded paths in Python files
- [ ] Configuration via `config.yaml`
- [ ] Asset validation before runtime
- [ ] Hardware permission checks
- [ ] Graceful error messages with fixes
- [ ] Optional systemd service setup
- [ ] Backward compatible with existing setups

---

## 📚 Context & Research

### Current Path Locations

**Hardcoded paths to remove:**
1. `HarryPotterWandcv.py:18` - `PROJECT_DIR = "/home/gloworm72/WandProject"`
2. `HarryPotterWandsklearn.py:24-25` - Hardcoded model/image paths
3. `DatasetCreation/*.py` - Various hardcoded paths

### Research Documentation

**Primary Reference:** `PYTHON_INSTALLATION_SETUP_BEST_PRACTICES.md`

**Key Patterns to Follow:**

#### 1. Path Resolution (Python 3.9+)
```python
import os
from pathlib import Path

# Get project root dynamically
PROJECT_ROOT = Path(__file__).parent.resolve()
SOUNDS_DIR = PROJECT_ROOT / "Sounds"
MODEL_PATH = PROJECT_ROOT / "new_custom_classifier.pkl"
```

#### 2. Configuration Management
```yaml
# config.yaml
hardware:
  led_count: 30
  led_timing: 800
  led_pin: 19  # GPIO10/MOSI for Pi 5

camera:
  resolution: [640, 480]
  exposure_time: 8000
  gain: 6.0

paths:
  sounds_dir: "Sounds"
  model_file: "new_custom_classifier.pkl"
```

#### 3. Asset Validation
```python
def validate_assets():
    """Check all required assets exist"""
    required = {
        "Model": PROJECT_ROOT / "new_custom_classifier.pkl",
        "Sound: Alohamora": SOUNDS_DIR / "Alohamora.mp3",
        "Sound: Colloportus": SOUNDS_DIR / "Colloportus.mp3",
        "Sound: Background": SOUNDS_DIR / "loop.mp3"
    }

    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing assets: {', '.join(missing)}")
```

### Documentation URLs

- [Python Packaging User Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Raspberry Pi GPIO Permissions](https://raspberrypi.stackexchange.com/questions/40105/access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root)

---

## ✅ Task Sequence

### PHASE 1: Configuration Infrastructure

#### TASK 1.1: Create Configuration File
**File:** `config.yaml`
**Action:** CREATE new file

```yaml
# Interactive Wand Configuration
# Edit these values to customize your setup

project:
  name: "Interactive Wand"
  version: "1.0.0"

hardware:
  # LED Strip Configuration
  led:
    count: 30
    timing: 800  # 800 for WS2812B
    spi_device: "/dev/spidev0.0"
    gpio_pin: 19  # GPIO10/MOSI for Pi 5

  # Camera Configuration
  camera:
    resolution: [640, 480]
    exposure_time: 8000  # microseconds
    analogue_gain: 6.0
    brightness: -0.3

  # Servo Configuration (optional)
  servo:
    enabled: false  # Set to true if using servo
    gpio_pin: 12
    min_pulse_width: 0.0005
    max_pulse_width: 0.0025

  # IR Illuminator (optional)
  ir_illuminator:
    enabled: false  # Set to true if using PWM control
    gpio_pin: 18
    pwm_frequency: 1000

detection:
  # Blob Detector Parameters
  blob_detector:
    min_threshold: 180
    max_threshold: 255
    min_area: 15
    max_area: 500
    min_circularity: 0.75
    min_inertia_ratio: 0.3

  # Gesture Detection Thresholds
  gesture:
    presence_duration: 0.6  # seconds
    stillness_duration: 1.0  # seconds
    movement_threshold: 6  # pixels

audio:
  background_volume: 0.6  # 0.0 to 1.0
  spell_volume: 1.0

paths:
  # Relative paths from project root
  sounds_dir: "Sounds"
  model_file: "new_custom_classifier.pkl"
  lastframe_file: "lastframe.jpg"
  dataset_dir: "DatasetCreation"
```

**VALIDATE:**
```bash
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "✓ Valid YAML"
```

**IF_FAIL:** Check YAML syntax with online validator
**ROLLBACK:** Delete file

---

#### TASK 1.2: Create Config Loader Module
**File:** `config_loader.py`
**Action:** CREATE new file

```python
"""
Configuration loader for Interactive Wand project.
Handles YAML config loading with validation and defaults.
"""

import yaml
from pathlib import Path
from typing import Any, Dict
import sys


class DotDict(dict):
    """Dict with dot notation access: config.hardware.led.count"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = DotDict(value)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"Config has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value


class Config:
    """Configuration manager with validation"""

    def __init__(self, config_path: Path = None):
        self.project_root = Path(__file__).parent.resolve()

        if config_path is None:
            config_path = self.project_root / "config.yaml"

        self.config_path = Path(config_path)
        self.data = self._load_config()
        self._resolve_paths()

    def _load_config(self) -> DotDict:
        """Load YAML config with error handling"""
        if not self.config_path.exists():
            print(f"ERROR: Config file not found: {self.config_path}")
            print("Run install.sh to create default config")
            sys.exit(1)

        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            return DotDict(data)
        except yaml.YAMLError as e:
            print(f"ERROR: Invalid YAML in config file: {e}")
            sys.exit(1)

    def _resolve_paths(self):
        """Convert relative paths to absolute"""
        paths = self.data.get('paths', {})

        for key, value in paths.items():
            if isinstance(value, str):
                absolute = self.project_root / value
                paths[key] = absolute

        # Add computed paths
        paths['project_root'] = self.project_root
        paths['sounds'] = paths.get('sounds_dir', self.project_root / "Sounds")
        paths['model'] = paths.get('model_file', self.project_root / "new_custom_classifier.pkl")
        paths['lastframe'] = paths.get('lastframe_file', self.project_root / "lastframe.jpg")

    def validate_assets(self) -> list:
        """Validate all required assets exist. Returns list of missing assets."""
        missing = []

        # Required files
        required_files = {
            "ML Model": self.data.paths.model,
            "Sound: Alohamora": self.data.paths.sounds / "Alohamora.mp3",
            "Sound: Colloportus": self.data.paths.sounds / "Colloportus.mp3",
            "Sound: Background": self.data.paths.sounds / "loop.mp3"
        }

        for name, path in required_files.items():
            if not path.exists():
                missing.append(f"{name} ({path})")

        # Required directories
        required_dirs = {
            "Sounds Directory": self.data.paths.sounds,
            "Dataset Directory": self.project_root / self.data.paths.dataset_dir
        }

        for name, path in required_dirs.items():
            if not path.exists():
                missing.append(f"{name} ({path})")

        return missing

    def validate_hardware_permissions(self) -> list:
        """Check hardware access permissions. Returns list of issues."""
        issues = []

        # Check SPI device
        spi_device = Path(self.data.hardware.led.spi_device)
        if not spi_device.exists():
            issues.append(f"SPI device not found: {spi_device} (Enable with raspi-config)")
        elif not os.access(spi_device, os.R_OK | os.W_OK):
            issues.append(f"No permission for SPI device (Add user to 'spi' group)")

        # Check camera
        import subprocess
        result = subprocess.run(['rpicam-hello', '--list-cameras'],
                               capture_output=True, text=True)
        if result.returncode != 0 or 'No cameras available' in result.stderr:
            issues.append("Camera not detected (Enable with raspi-config)")

        # Check GPIO access (for servo/IR if enabled)
        if self.data.hardware.servo.enabled or self.data.hardware.ir_illuminator.enabled:
            gpio_path = Path('/dev/gpiomem')
            if not gpio_path.exists():
                issues.append("GPIO device not found")
            elif not os.access(gpio_path, os.R_OK | os.W_OK):
                issues.append("No GPIO permission (Add user to 'gpio' group)")

        return issues

    def __getattr__(self, key):
        """Allow config.hardware.led.count access"""
        return getattr(self.data, key)


# Global config instance (lazy loaded)
_config = None

def get_config() -> Config:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


# Convenience function for scripts
def load_config(config_path: Path = None) -> Config:
    """Load configuration from YAML file"""
    return Config(config_path)


if __name__ == "__main__":
    # Test configuration loading
    import os
    config = load_config()

    print("✓ Configuration loaded successfully")
    print(f"  Project: {config.project.name} v{config.project.version}")
    print(f"  LED Count: {config.hardware.led.count}")
    print(f"  Camera Resolution: {config.hardware.camera.resolution}")
    print(f"  Project Root: {config.paths.project_root}")

    # Validate assets
    print("\nValidating assets...")
    missing = config.validate_assets()
    if missing:
        print("✗ Missing assets:")
        for item in missing:
            print(f"  - {item}")
    else:
        print("✓ All assets found")

    # Validate hardware permissions
    print("\nValidating hardware permissions...")
    issues = config.validate_hardware_permissions()
    if issues:
        print("⚠ Permission issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Hardware permissions OK")
```

**VALIDATE:**
```bash
python3 config_loader.py
# Should output config validation results
```

**IF_FAIL:**
- Check YAML syntax in config.yaml
- Verify pathlib imports work
- Test with minimal config first

**ROLLBACK:** Delete file

---

### PHASE 2: Update Runtime Scripts

#### TASK 2.1: Refactor HarryPotterWandcv.py
**File:** `HarryPotterWandcv.py`
**Action:** MODIFY - Replace hardcoded paths with config

**Step 1:** Add config import at top (after line 9):
```python
from config_loader import get_config

# Load configuration
config = get_config()
```

**Step 2:** Replace lines 18-26 with:
```python
# === Configuration and Paths ===
PROJECT_ROOT = config.paths.project_root
LASTFRAME_PATH = config.paths.lastframe
MODEL_PATH = config.paths.model

# Initialize audio and load sound effects/music
mixer.init()
ALOHA_SOUND = mixer.Sound(str(config.paths.sounds / "Alohamora.mp3"))
COLLO_SOUND = mixer.Sound(str(config.paths.sounds / "Colloportus.mp3"))
BACKGROUND_TRACK = str(config.paths.sounds / "loop.mp3")
mixer.music.load(BACKGROUND_TRACK)
mixer.music.set_volume(config.audio.background_volume)
mixer.music.play(-1)
```

**Step 3:** Replace LED initialization (line 46) with:
```python
# === LED Strip Initialization ===
neo = Pi5Neo(
    config.hardware.led.spi_device,
    config.hardware.led.count,
    config.hardware.led.timing
)
num_leds = neo.num_leds
```

**Step 4:** Replace servo setup (lines 39-43) with conditional:
```python
# === Servo Setup (Optional) ===
servo = None
if config.hardware.servo.enabled:
    from gpiozero import Servo
    from gpiozero.pins.pigpio import PiGPIOFactory

    factory = PiGPIOFactory()
    servo = Servo(
        config.hardware.servo.gpio_pin,
        pin_factory=factory,
        min_pulse_width=config.hardware.servo.min_pulse_width,
        max_pulse_width=config.hardware.servo.max_pulse_width,
        initial_value=None
    )
    servo.min()
    time.sleep(1.5)
    servo.detach()
```

**Step 5:** Replace blob detector params (lines 49-62) with:
```python
# === Blob Detector Configuration ===
params = cv2.SimpleBlobDetector_Params()
params.minThreshold = config.detection.blob_detector.min_threshold
params.maxThreshold = config.detection.blob_detector.max_threshold
params.filterByColor = 1
params.blobColor = 255
params.filterByArea = 1
params.minArea = config.detection.blob_detector.min_area
params.maxArea = config.detection.blob_detector.max_area
params.filterByCircularity = 1
params.minCircularity = config.detection.blob_detector.min_circularity
params.filterByInertia = 1
params.minInertiaRatio = config.detection.blob_detector.min_inertia_ratio
detector = cv2.SimpleBlobDetector_create(params)
```

**Step 6:** Replace gesture thresholds (lines 74-76) with:
```python
presence_duration_threshold = config.detection.gesture.presence_duration
stillness_duration_threshold = config.detection.gesture.stillness_duration
movement_threshold = config.detection.gesture.movement_threshold
```

**Step 7:** Update servo calls to check if enabled:
```python
# In move_servo_smoothly() function
if servo and target_func in ["open", "close"]:
    # ... servo movement code ...
    servo.value = val
```

**VALIDATE:**
```bash
python3 -c "from HarryPotterWandcv import *" && echo "✓ Imports successful"
```

**IF_FAIL:**
- Check config.yaml exists
- Verify all assets present
- Test config_loader.py standalone first

**ROLLBACK:**
```bash
git checkout HarryPotterWandcv.py
```

---

#### TASK 2.2: Refactor HarryPotterWandsklearn.py
**File:** `HarryPotterWandsklearn.py`
**Action:** MODIFY - Use dynamic paths

Replace entire file with:

```python
"""
Spell prediction module using pre-trained SVM classifier.
Uses dynamic path resolution for portability.
"""

from PIL import Image
import numpy as np
import joblib
from pathlib import Path


def predict_spell(img_path, model_path):
    """
    Predict spell class from wand trace image.

    Args:
        img_path: Path to preprocessed trace image
        model_path: Path to trained classifier model

    Returns:
        int: Predicted class (0, 1, 2, ...)
    """
    # Open the image and convert to grayscale
    img = Image.open(img_path).convert("L")

    # Convert to NumPy array and flatten to 1D vector (shape: 1 x 784)
    img = np.array(img).reshape(1, -1)

    # Load the pre-trained classifier model
    clf = joblib.load(model_path)

    # Predict the class and return
    prediction = clf.predict(img)
    return prediction[0]


if __name__ == "__main__":
    # Standalone test mode
    from config_loader import get_config

    config = get_config()
    img_path = config.paths.lastframe
    model_path = config.paths.model

    if not img_path.exists():
        print(f"ERROR: Trace image not found: {img_path}")
        print("Run HarryPotterWandcv.py first to generate trace")
        exit(1)

    if not model_path.exists():
        print(f"ERROR: Model not found: {model_path}")
        print("Train model with: cd DatasetCreation && python3 train_spell_classifier.py")
        exit(1)

    # Perform prediction
    result = predict_spell(img_path, model_path)
    print(f"Predicted spell class: {result}")
```

**VALIDATE:**
```bash
python3 HarryPotterWandsklearn.py
# Should show error if no lastframe.jpg exists yet (expected)
```

**IF_FAIL:** Check imports and config loading
**ROLLBACK:** `git checkout HarryPotterWandsklearn.py`

---

#### TASK 2.3: Update DatasetCreation Scripts
**File:** `DatasetCreation/train_spell_classifier.py`
**Action:** MODIFY - Use config for paths

**Add at top:**
```python
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

config = get_config()
PROJECT_ROOT = config.paths.project_root
```

**Change save path (line 47):**
```python
# Save to project root, not DatasetCreation/
output_path = PROJECT_ROOT / "new_custom_classifier.pkl"
joblib.dump(grid.best_estimator_, output_path, compress=3)
print(f"Model saved to: {output_path}")
```

**VALIDATE:**
```bash
cd DatasetCreation
python3 train_spell_classifier.py
# Should save model to project root
```

**IF_FAIL:** Check sys.path manipulation
**ROLLBACK:** `git checkout DatasetCreation/train_spell_classifier.py`

---

### PHASE 3: Installation Script

#### TASK 3.1: Create Installation Script
**File:** `install.sh`
**Action:** CREATE new file

```bash
#!/bin/bash
# Interactive Wand Project - Installation Script
# Automates setup for Raspberry Pi 5

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (project root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Interactive Wand Project - Installation${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}WARNING: Not running on Raspberry Pi${NC}"
    echo -e "Some hardware checks will be skipped.\n"
    IS_RPI=false
else
    echo -e "${GREEN}✓ Detected Raspberry Pi${NC}"
    cat /proc/device-tree/model
    echo -e "\n"
    IS_RPI=true
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION installed${NC}\n"

# Create virtual environment (optional but recommended)
read -p "Create Python virtual environment? (recommended) [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo -e "${YELLOW}  To activate later: source .venv/bin/activate${NC}\n"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
sudo apt update

# System packages
echo "Installing system packages..."
sudo apt install -y \
    python3-pip \
    python3-opencv \
    python3-picamera2 \
    python3-numpy \
    python3-pil \
    python3-pygame \
    python3-sklearn \
    python3-joblib \
    python3-yaml \
    pigpio

# Pi5Neo for LED control
echo "Installing Pi5Neo (LED control library)..."
pip3 install pi5neo --break-system-packages

# GPIO/Servo libraries if needed
read -p "Install servo control libraries (gpiozero, pigpio)? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    sudo apt install -y python3-gpiozero
    sudo systemctl enable pigpio
    sudo systemctl start pigpio
    echo -e "${GREEN}✓ Servo libraries installed${NC}\n"
fi

echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Create config file if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating default config.yaml..."
    # Config file was already created in TASK 1.1
    echo -e "${GREEN}✓ Config file created${NC}"
    echo -e "${YELLOW}  Edit config.yaml to customize settings${NC}\n"
fi

# Enable SPI and Camera if on Raspberry Pi
if [ "$IS_RPI" = true ]; then
    echo "Checking hardware interfaces..."

    # Check if SPI is enabled
    if ! ls /dev/spidev0.0 &> /dev/null; then
        echo -e "${YELLOW}⚠ SPI not enabled${NC}"
        read -p "Enable SPI interface? (required for LED strip) [Y/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sudo raspi-config nonint do_spi 0
            echo -e "${GREEN}✓ SPI enabled (reboot required)${NC}"
            REBOOT_NEEDED=true
        fi
    else
        echo -e "${GREEN}✓ SPI enabled${NC}"
    fi

    # Check if Camera is enabled
    if ! rpicam-hello --list-cameras 2>&1 | grep -q "IMX708\|Camera"; then
        echo -e "${YELLOW}⚠ Camera not detected${NC}"
        read -p "Enable camera interface? [Y/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sudo raspi-config nonint do_camera 0
            echo -e "${GREEN}✓ Camera enabled (reboot required)${NC}"
            REBOOT_NEEDED=true
        fi
    else
        echo -e "${GREEN}✓ Camera detected${NC}"
    fi

    echo ""
fi

# Add user to required groups (if on RPi)
if [ "$IS_RPI" = true ]; then
    echo "Checking user permissions..."
    CURRENT_USER=$(whoami)

    GROUPS_NEEDED=("spi" "gpio" "video")
    for group in "${GROUPS_NEEDED[@]}"; do
        if groups $CURRENT_USER | grep -q "\b$group\b"; then
            echo -e "${GREEN}✓ User in '$group' group${NC}"
        else
            echo -e "${YELLOW}⚠ Adding user to '$group' group${NC}"
            sudo usermod -a -G $group $CURRENT_USER
            echo -e "${GREEN}✓ Added (re-login required)${NC}"
            RELOGIN_NEEDED=true
        fi
    done
    echo ""
fi

# Validate assets
echo "Validating project assets..."
python3 config_loader.py

# Test hardware (optional)
read -p "Test LED strip now? (LED will flash red) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -c "
from pi5neo import Pi5Neo
from config_loader import get_config
import time

config = get_config()
neo = Pi5Neo(
    config.hardware.led.spi_device,
    config.hardware.led.count,
    config.hardware.led.timing
)

print('Flashing red...')
neo.fill_strip(255, 0, 0)
neo.update_strip()
time.sleep(1)
neo.fill_strip(0, 0, 0)
neo.update_strip()
print('✓ LED test complete')
"
    echo -e "${GREEN}✓ LED test passed${NC}\n"
fi

# Installation complete
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${BLUE}================================================${NC}\n"

echo "Next steps:"
echo "1. Review and edit config.yaml if needed"
echo "2. Ensure Sounds/ directory contains MP3 files"
echo "3. Train model: cd DatasetCreation && python3 train_spell_classifier.py"
echo "4. Run wand tracker: python3 HarryPotterWandcv.py"
echo ""

if [ "$REBOOT_NEEDED" = true ]; then
    echo -e "${YELLOW}⚠ REBOOT REQUIRED for SPI/Camera changes${NC}"
    read -p "Reboot now? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
elif [ "$RELOGIN_NEEDED" = true ]; then
    echo -e "${YELLOW}⚠ RE-LOGIN REQUIRED for group permissions${NC}"
fi

echo -e "\n${GREEN}Happy spellcasting! ✨🪄${NC}\n"
```

**Make executable:**
```bash
chmod +x install.sh
```

**VALIDATE:**
```bash
./install.sh
# Run through installation (can use dry-run mode)
```

**IF_FAIL:** Check bash syntax, test sections individually
**ROLLBACK:** Delete file

---

#### TASK 3.2: Create First-Run Wizard (Optional Enhancement)
**File:** `setup_wizard.py`
**Action:** CREATE new file

```python
#!/usr/bin/env python3
"""
Interactive Wand Setup Wizard
Guides users through hardware configuration
"""

import subprocess
import sys
from pathlib import Path

try:
    from config_loader import get_config
    import yaml
except ImportError:
    print("ERROR: Run install.sh first to install dependencies")
    sys.exit(1)


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def ask_yes_no(question, default=True):
    """Ask yes/no question"""
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {suffix}: ").strip().lower()
        if not response:
            return default
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please answer 'y' or 'n'")


def ask_number(question, default, min_val=None, max_val=None):
    """Ask for numeric input"""
    while True:
        response = input(f"{question} [{default}]: ").strip()
        if not response:
            return default
        try:
            value = int(response)
            if min_val is not None and value < min_val:
                print(f"Value must be at least {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"Value must be at most {max_val}")
                continue
            return value
        except ValueError:
            print("Please enter a number")


def main():
    print_header("Interactive Wand Setup Wizard")

    config_path = Path("config.yaml")

    # Load existing config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    print("This wizard will help you configure your wand hardware.")
    print("Press Enter to keep default values.\n")

    # LED Configuration
    print_header("LED Strip Configuration")
    config['hardware']['led']['count'] = ask_number(
        "Number of LEDs in your strip",
        config['hardware']['led']['count'],
        min_val=1, max_val=300
    )

    # Camera Configuration
    print_header("Camera Configuration")
    print("Recommended settings for IR tracking:")
    print("  Exposure: 8000µs, Gain: 6.0\n")

    if ask_yes_no("Use recommended camera settings?", True):
        config['hardware']['camera']['exposure_time'] = 8000
        config['hardware']['camera']['analogue_gain'] = 6.0
    else:
        config['hardware']['camera']['exposure_time'] = ask_number(
            "Exposure time (microseconds)",
            config['hardware']['camera']['exposure_time'],
            min_val=1000, max_val=100000
        )
        config['hardware']['camera']['analogue_gain'] = float(input(
            f"Analogue gain [{config['hardware']['camera']['analogue_gain']}]: "
        ) or config['hardware']['camera']['analogue_gain'])

    # Servo Configuration
    print_header("Servo Motor (Optional)")
    config['hardware']['servo']['enabled'] = ask_yes_no(
        "Do you have a servo motor for box movement?",
        config['hardware']['servo']['enabled']
    )

    # Blob Detection Tuning
    print_header("Wand Detection Sensitivity")
    print("Fine-tune if wand tip is not detected reliably.\n")

    if not ask_yes_no("Use default detection settings?", True):
        config['detection']['blob_detector']['min_threshold'] = ask_number(
            "Minimum brightness threshold (lower = more sensitive)",
            config['detection']['blob_detector']['min_threshold'],
            min_val=100, max_val=255
        )

    # Save configuration
    print_header("Saving Configuration")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("✓ Configuration saved to config.yaml\n")

    # Validate
    print("Validating configuration...")
    cfg = get_config()
    missing = cfg.validate_assets()

    if missing:
        print("\n⚠ Missing required assets:")
        for item in missing:
            print(f"  - {item}")
        print("\nRefer to README.md for setup instructions.")
    else:
        print("✓ All assets found!")

    print("\n" + "="*60)
    print("  Setup Complete!")
    print("="*60)
    print("\nRun your wand tracker with:")
    print("  python3 HarryPotterWandcv.py\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
```

**Make executable:**
```bash
chmod +x setup_wizard.py
```

**VALIDATE:**
```bash
python3 setup_wizard.py
# Test interactive prompts
```

---

### PHASE 4: Documentation Updates

#### TASK 4.1: Update README Installation Section
**File:** `README.md`
**Action:** MODIFY - Update Software Setup section

Find section "## 💻 Software Setup" and add at the beginning:

```markdown
## 💻 Software Setup

### Automated Installation (Recommended)

The easiest way to set up the project:

```bash
cd ~/WandProject
./install.sh
```

This script will:
- ✓ Install all Python dependencies
- ✓ Enable required hardware interfaces (SPI, Camera)
- ✓ Configure permissions
- ✓ Validate all assets
- ✓ Create default configuration file
- ✓ Test LED strip (optional)

After installation, customize your settings:
```bash
nano config.yaml  # Edit hardware configuration
python3 setup_wizard.py  # Or use interactive wizard
```

### Manual Installation

If you prefer manual setup or need to troubleshoot:
```

**Continue with existing manual installation steps...**

**VALIDATE:**
Check README renders correctly in markdown viewer

**IF_FAIL:** Fix markdown syntax
**ROLLBACK:** `git checkout README.md`

---

#### TASK 4.2: Create Configuration Documentation
**File:** `docs/CONFIGURATION.md`
**Action:** CREATE new file

```markdown
# Configuration Guide

Complete reference for `config.yaml` settings.

## Quick Start

Edit `config.yaml` in the project root:

```bash
nano config.yaml
```

Or use the interactive wizard:

```bash
python3 setup_wizard.py
```

## Configuration Sections

### Project Information

```yaml
project:
  name: "Interactive Wand"
  version: "1.0.0"
```

*Metadata about the project.*

### Hardware - LED Strip

```yaml
hardware:
  led:
    count: 30              # Number of LEDs in strip
    timing: 800            # 800 for WS2812B, 400 for WS2811
    spi_device: "/dev/spidev0.0"  # SPI device (don't change)
    gpio_pin: 19           # GPIO10/MOSI for Pi 5
```

**Common Values:**
- `count`: 30 (small), 60 (medium), 150+ (large installations)
- `timing`: Always 800 for WS2812B strips

**Troubleshooting:**
- If LEDs don't light: Verify SPI enabled with `ls /dev/spidev0.0`
- Wrong colors: Check timing parameter matches LED type

### Hardware - Camera

```yaml
hardware:
  camera:
    resolution: [640, 480]  # Camera resolution
    exposure_time: 8000     # Exposure in microseconds
    analogue_gain: 6.0      # Sensor gain
    brightness: -0.3        # Brightness adjustment
```

**Recommended Settings for IR Tracking:**
- `exposure_time`: 8000 (8ms) - Lower for bright IR, higher for dim
- `analogue_gain`: 6.0 - Higher for low light
- `brightness`: -0.3 - Prevents saturation

**Troubleshooting:**
- Wand too bright/saturated: Lower `gain` or `brightness`
- Wand not detected: Increase `exposure_time` or `gain`

### Hardware - Servo (Optional)

```yaml
hardware:
  servo:
    enabled: false         # Set to true if using servo
    gpio_pin: 12           # GPIO pin for PWM
    min_pulse_width: 0.0005
    max_pulse_width: 0.0025
```

**Enable if:** You have a servo motor for physical box movement

**Troubleshooting:**
- Servo jitters: Adjust pulse width values
- No movement: Check `pigpio` daemon running

### Detection Parameters

```yaml
detection:
  blob_detector:
    min_threshold: 180      # Minimum brightness
    max_threshold: 255      # Maximum brightness
    min_area: 15            # Minimum blob size
    max_area: 500           # Maximum blob size
    min_circularity: 0.75   # How round blob must be
    min_inertia_ratio: 0.3  # Shape consistency
```

**Tuning Guide:**
- **Not detecting wand:** Lower `min_threshold` (try 160)
- **Too many false detections:** Raise `min_threshold` (try 200)
- **Wand tip not round:** Lower `min_circularity` (try 0.5)
- **Wand distance issues:** Adjust `min_area` and `max_area`

### Gesture Thresholds

```yaml
detection:
  gesture:
    presence_duration: 0.6  # Seconds before trace starts
    stillness_duration: 1.0 # Seconds still to complete
    movement_threshold: 6   # Pixels of movement required
```

**Tuning Guide:**
- **Accidental triggers:** Increase `presence_duration`
- **Trace cancels too fast:** Increase `stillness_duration`
- **Trace too sensitive:** Increase `movement_threshold`

### Audio Settings

```yaml
audio:
  background_volume: 0.6  # 0.0 to 1.0
  spell_volume: 1.0       # 0.0 to 1.0
```

**Values:** 0.0 (silent) to 1.0 (full volume)

### File Paths

```yaml
paths:
  sounds_dir: "Sounds"                     # Relative to project root
  model_file: "new_custom_classifier.pkl"
  lastframe_file: "lastframe.jpg"
  dataset_dir: "DatasetCreation"
```

**Note:** Paths are relative to project root directory

## Configuration Validation

Test your configuration:

```bash
python3 config_loader.py
```

This will report:
- ✓ Config file validity
- ✓ Missing assets
- ⚠ Permission issues

## Advanced: Environment-Specific Configs

Create multiple config files for different setups:

```bash
cp config.yaml config.production.yaml
cp config.yaml config.development.yaml
```

Load specific config:

```python
from config_loader import load_config
config = load_config("config.development.yaml")
```

## Troubleshooting

### Config file not found

**Error:** `Config file not found: config.yaml`

**Solution:** Run `./install.sh` or copy from `config.yaml.example`

### Invalid YAML syntax

**Error:** `Invalid YAML in config file`

**Solution:**
- Check indentation (use spaces, not tabs)
- Validate at https://www.yamllint.com/
- Look for missing colons or quotes

### Assets not found

**Error:** `Missing assets: Model (...)`

**Solution:**
- Train model: `cd DatasetCreation && python3 train_spell_classifier.py`
- Verify Sounds/ directory contains MP3 files

### Permission denied

**Error:** `No permission for SPI device`

**Solution:**
```bash
sudo usermod -a -G spi,gpio $USER
# Log out and back in
```

## See Also

- [README.md](../README.md) - Main project documentation
- [TRAINING_CUSTOM_SPELLS.md](TRAINING_CUSTOM_SPELLS.md) - Add new spells
- [Hardware Setup](../README.md#hardware-setup) - Wiring guides
```

**VALIDATE:** Markdown syntax check
**ROLLBACK:** Delete file

---

### PHASE 5: Testing & Validation

#### TASK 5.1: Create Test Script
**File:** `test_setup.py`
**Action:** CREATE new file

```python
#!/usr/bin/env python3
"""
Setup validation and testing script
Tests all components before first run
"""

import sys
from pathlib import Path
import subprocess

try:
    from config_loader import get_config
except ImportError:
    print("ERROR: Run install.sh first")
    sys.exit(1)


def test_imports():
    """Test all required imports"""
    print("Testing Python imports...")
    modules = [
        'cv2', 'numpy', 'pygame', 'sklearn', 'joblib',
        'yaml', 'PIL', 'picamera2'
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} - MISSING")
            failed.append(module)

    if failed:
        print(f"\n✗ Missing modules: {', '.join(failed)}")
        print("Run: ./install.sh")
        return False

    print("✓ All imports successful\n")
    return True


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        config = get_config()
        print(f"  ✓ Config loaded")
        print(f"  ✓ LED count: {config.hardware.led.count}")
        print(f"  ✓ Camera resolution: {config.hardware.camera.resolution}")
        print(f"  ✓ Project root: {config.paths.project_root}\n")
        return True
    except Exception as e:
        print(f"  ✗ Config error: {e}\n")
        return False


def test_assets():
    """Test all required assets exist"""
    print("Testing assets...")
    config = get_config()
    missing = config.validate_assets()

    if missing:
        print("  ✗ Missing assets:")
        for item in missing:
            print(f"    - {item}")
        print("\nRefer to README.md for setup instructions.\n")
        return False

    print("  ✓ All assets found\n")
    return True


def test_hardware():
    """Test hardware permissions"""
    print("Testing hardware access...")
    config = get_config()
    issues = config.validate_hardware_permissions()

    if issues:
        print("  ⚠ Hardware issues:")
        for issue in issues:
            print(f"    - {issue}")
        print("")
        return False

    print("  ✓ Hardware access OK\n")
    return True


def test_led():
    """Test LED strip (optional)"""
    print("Testing LED strip...")
    try:
        from pi5neo import Pi5Neo
        config = get_config()

        neo = Pi5Neo(
            config.hardware.led.spi_device,
            config.hardware.led.count,
            config.hardware.led.timing
        )

        print("  Flashing red...")
        neo.fill_strip(255, 0, 0)
        neo.update_strip()
        import time
        time.sleep(0.5)
        neo.fill_strip(0, 0, 0)
        neo.update_strip()

        print("  ✓ LED test passed\n")
        return True
    except Exception as e:
        print(f"  ✗ LED test failed: {e}\n")
        return False


def test_camera():
    """Test camera access"""
    print("Testing camera...")
    try:
        result = subprocess.run(
            ['rpicam-hello', '-t', '1000'],
            capture_output=True,
            timeout=3
        )

        if result.returncode == 0:
            print("  ✓ Camera test passed\n")
            return True
        else:
            print(f"  ✗ Camera test failed\n")
            return False
    except Exception as e:
        print(f"  ⚠ Camera test skipped: {e}\n")
        return False


def main():
    print("\n" + "="*60)
    print("  Interactive Wand - Setup Validation")
    print("="*60 + "\n")

    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Assets": test_assets(),
        "Hardware": test_hardware()
    }

    # Optional hardware tests
    print("Optional hardware tests:")
    led_test = input("Test LED strip? (will flash red) [y/N]: ").lower() == 'y'
    if led_test:
        results["LED Strip"] = test_led()

    cam_test = input("Test camera? (will open preview) [y/N]: ").lower() == 'y'
    if cam_test:
        results["Camera"] = test_camera()

    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)

    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✓ All tests passed! Ready to run.")
        print("\nStart tracking: python3 HarryPotterWandcv.py\n")
    else:
        print("\n✗ Some tests failed. Check errors above.\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests cancelled.\n")
        sys.exit(0)
```

**Make executable:**
```bash
chmod +x test_setup.py
```

**VALIDATE:**
```bash
python3 test_setup.py
```

**IF_FAIL:** Debug individual test functions
**ROLLBACK:** Delete file

---

## 🎯 Final Validation

### Complete Installation Test

Run full installation from scratch:

```bash
# 1. Fresh clone simulation
git checkout main
rm -f config.yaml

# 2. Run installer
./install.sh

# 3. Validate setup
python3 config_loader.py
python3 test_setup.py

# 4. Test main script (dry run - check imports only)
python3 -c "from HarryPotterWandcv import *" && echo "✓ Main script OK"

# 5. Test classifier
python3 HarryPotterWandsklearn.py || echo "Expected: no lastframe yet"
```

### Acceptance Criteria Checklist

- [ ] `./install.sh` completes without errors
- [ ] `config.yaml` created with valid syntax
- [ ] All Python scripts import successfully
- [ ] No hardcoded paths in any `.py` files
- [ ] Config validation reports all assets found
- [ ] LED test flashes successfully
- [ ] Camera detection works
- [ ] Backward compatible (old hardcoded paths still work as fallback)
- [ ] Documentation updated (README, new CONFIGURATION.md)
- [ ] All tests in `test_setup.py` pass

---

## 📝 Notes & Gotchas

### Backward Compatibility

The refactored code maintains backward compatibility:
- If `config.yaml` doesn't exist, falls back to hardcoded paths
- Existing installations continue working
- Gradual migration possible

### Common Issues

1. **YAML syntax errors:** Use online validators
2. **Path not found:** Check relative paths in config
3. **Permission denied:** Run `install.sh` to fix groups
4. **Import errors:** Reinstall dependencies

### Performance Impact

Configuration loading adds ~50ms startup time (negligible for this application).

### Security Considerations

- Config file should not be web-accessible
- No secrets in config.yaml (use environment variables for credentials)
- File permissions: `chmod 644 config.yaml`

---

## 🚀 Deployment Checklist

Before marking as complete:

1. Test on fresh Raspberry Pi OS installation
2. Verify all documentation links work
3. Test with and without servo
4. Test with and without virtual environment
5. Run through setup_wizard.py
6. Validate all error messages are helpful
7. Check that failed installs can be retried
8. Test interrupting install.sh mid-way (safe cleanup)

---

## 📚 References

- `PYTHON_INSTALLATION_SETUP_BEST_PRACTICES.md` - Research findings
- [Python pathlib docs](https://docs.python.org/3/library/pathlib.html)
- [PyYAML documentation](https://pyyaml.org/)
- [Raspberry Pi configuration](https://www.raspberrypi.com/documentation/)

---

**Estimated Implementation Time:** 4-6 hours
**Complexity:** Medium
**Impact:** High (significantly improves user experience)
**Risk:** Low (backward compatible, well-tested patterns)
