# Python Project Installation and Configuration Management Best Practices
## Research Report for Raspberry Pi Computer Vision Projects

**Target Use Case:** Interactive Wand Gesture Recognition System
**Platform:** Raspberry Pi 5 with Camera Module, LED Strip, Audio Assets, and ML Models
**Date:** 2025-11-22

---

## Executive Summary

This research report provides comprehensive best practices for creating an automated setup script for Python projects on Raspberry Pi, with specific focus on computer vision applications involving ML models, audio assets, and hardware control. Key findings prioritize modern packaging standards (pyproject.toml), robust path management (importlib.resources), and Raspberry Pi-specific considerations (systemd services, GPIO permissions).

**Key Recommendations:**
1. Use **pyproject.toml** as primary packaging configuration (setup.py deprecated for new projects)
2. Leverage **importlib.resources** for asset management (sounds, models, data files)
3. Implement **python-dotenv** for environment-specific configuration
4. Create **systemd service** for auto-start on Raspberry Pi boot
5. Use **dynamic path resolution** with pathlib for cross-platform compatibility

---

## 1. Configuration Management

### 1.1 Configuration File Format Comparison

| Format | Best For | Pros | Cons |
|--------|----------|------|------|
| **YAML** | Complex hierarchies, ML configs | Human-readable, supports comments, nested structures | Requires PyYAML dependency |
| **JSON** | Simple structured data | Native Python support, widely compatible | No comments, less readable |
| **INI** | Simple key-value pairs | Easy to parse (ConfigParser), minimal | Only 1-level hierarchy, no lists/dicts |
| **.env** | Secrets and environment vars | Secure, gitignore-friendly, environment-specific | Limited structure, string-only values |
| **TOML** | Modern Python packaging | Native support (Python 3.11+), clear syntax | Newer format, older systems need tomli |

**Recommendation for Wand Project:** Use **YAML** for application config (LED counts, camera settings, GPIO pins) + **.env** for secrets (API keys, passwords).

### 1.2 YAML Configuration Example

**config.yaml** (committed to version control):
```yaml
# Hardware Configuration
camera:
  resolution: [640, 480]
  exposure_time: 8000
  analogue_gain: 6.0
  framerate: 30

led_strip:
  device: "/dev/spidev0.0"
  num_leds: 30
  timing: 800
  gpio_pin: 10  # GPIO10 (Pin 19) for Pi 5

ir_illuminator:
  enabled: true
  gpio_pin: 18
  pwm_frequency: 1000
  default_brightness: 0.5

servo:
  enabled: false  # Set to true if using servo
  gpio_pin: 12
  min_pulse_width: 0.5
  max_pulse_width: 2.5

# Application Settings
blob_detection:
  min_threshold: 180
  max_threshold: 255
  min_area: 15
  max_area: 500
  min_circularity: 0.75

spell_recognition:
  presence_duration_threshold: 0.6  # seconds
  stillness_duration_threshold: 1.0
  min_trace_points: 10
  max_trace_age: 3.0

audio:
  background_music_volume: 0.3
  spell_sfx_volume: 0.8
  mixer_frequency: 44100
  channels: 2

# Paths (resolved dynamically - see code below)
paths:
  models: "models"
  sounds: "Sounds"
  training_data: "DatasetCreation"
  output: "output"
```

**Reading YAML Configuration:**
```python
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration manager with path resolution."""

    def __init__(self, config_path: Path):
        """Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = config_path
        self.base_dir = config_path.parent
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse YAML configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "camera.resolution")
            default: Default value if key not found

        Example:
            >>> config.get("camera.exposure_time")
            8000
            >>> config.get("led_strip.num_leds")
            30
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_path(self, path_key: str) -> Path:
        """Resolve path from config relative to project root.

        Args:
            path_key: Key in paths section (e.g., "models", "sounds")

        Returns:
            Absolute Path object
        """
        relative_path = self.get(f"paths.{path_key}")
        if relative_path:
            return (self.base_dir / relative_path).resolve()
        return None

    @property
    def camera(self) -> Dict[str, Any]:
        """Get camera configuration."""
        return self._config.get('camera', {})

    @property
    def led_strip(self) -> Dict[str, Any]:
        """Get LED strip configuration."""
        return self._config.get('led_strip', {})

    @property
    def is_servo_enabled(self) -> bool:
        """Check if servo motor is enabled."""
        return self.get('servo.enabled', False)


# Usage in main application
def main():
    # Resolve config path relative to script location
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config.yaml"

    # Load configuration
    config = Config(config_path)

    # Access camera settings
    resolution = config.get("camera.resolution")  # [640, 480]
    exposure = config.get("camera.exposure_time")  # 8000

    # Access paths
    sounds_dir = config.get_path("sounds")  # Absolute path to Sounds/
    models_dir = config.get_path("models")  # Absolute path to models/

    # Check feature flags
    if config.is_servo_enabled:
        print("Servo enabled - initializing...")
    else:
        print("Servo disabled - skipping servo setup")
```

### 1.3 Environment Variables with python-dotenv

**.env** (NEVER commit to version control - add to .gitignore):
```bash
# Development vs Production
ENVIRONMENT=development

# Optional API Keys (if adding cloud features)
OPENAI_API_KEY=sk-...
CLOUD_STORAGE_KEY=...

# Raspberry Pi Specific
GPIO_FACTORY=pigpio  # or rpigpio, lgpio
ENABLE_DEBUG_WINDOWS=true

# Project Paths (override if installed in non-standard location)
# PROJECT_ROOT=/opt/wandproject
```

**Loading Environment Variables:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

class EnvironmentConfig:
    """Manage environment-specific configuration."""

    def __init__(self):
        # Load .env file from project root
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path, override=False)  # Don't override existing env vars

    @property
    def environment(self) -> str:
        """Get current environment (development/production)."""
        return os.getenv('ENVIRONMENT', 'production')

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == 'development'

    @property
    def debug_windows_enabled(self) -> bool:
        """Check if debug windows should be shown."""
        # In production, might not want OpenCV windows on headless Pi
        return os.getenv('ENABLE_DEBUG_WINDOWS', 'false').lower() == 'true'

    @property
    def project_root(self) -> Path:
        """Get project root directory with environment override."""
        # Allow override via environment variable
        env_root = os.getenv('PROJECT_ROOT')
        if env_root:
            return Path(env_root)

        # Default: resolve from script location
        return Path(__file__).parent.resolve()

    @property
    def gpio_factory(self) -> str:
        """Get GPIO factory to use (pigpio/rpigpio/lgpio)."""
        return os.getenv('GPIO_FACTORY', 'pigpio')


# Usage
env = EnvironmentConfig()

if env.is_development:
    print("Running in development mode")
    # Show debug windows
    if env.debug_windows_enabled:
        cv2.imshow("Debug View", frame)

# Use project root for path resolution
models_dir = env.project_root / "models"
```

### 1.4 User-Specific vs System-Wide Configuration

**Best Practice for Raspberry Pi Projects:**

1. **System-Wide Config** (read-only, installed with package):
   - `/opt/wandproject/config.yaml` - Default configuration
   - `/opt/wandproject/models/` - Pre-trained ML models
   - `/opt/wandproject/sounds/` - Audio assets

2. **User-Specific Config** (editable, per-user overrides):
   - `~/.config/wandproject/config.yaml` - User overrides
   - `~/.config/wandproject/.env` - User secrets/environment

3. **System Service Config** (for systemd):
   - `/etc/wandproject/config.yaml` - Production configuration
   - Environment variables in systemd service file

**Configuration Loading Priority (highest to lowest):**
```python
from pathlib import Path
from typing import Optional
import yaml

def find_config_file() -> Path:
    """Find configuration file with priority order.

    Priority:
        1. Environment variable: WAND_CONFIG_PATH
        2. User config: ~/.config/wandproject/config.yaml
        3. System config: /etc/wandproject/config.yaml
        4. Package default: <install_dir>/config.yaml
        5. Development: <script_dir>/config.yaml
    """
    # 1. Check environment variable
    env_config = os.getenv('WAND_CONFIG_PATH')
    if env_config and Path(env_config).exists():
        return Path(env_config)

    # 2. Check user config
    user_config = Path.home() / '.config' / 'wandproject' / 'config.yaml'
    if user_config.exists():
        return user_config

    # 3. Check system config
    system_config = Path('/etc/wandproject/config.yaml')
    if system_config.exists():
        return system_config

    # 4. Check package installation
    try:
        from importlib.resources import files
        package_config = files('wandproject') / 'config.yaml'
        if package_config.exists():
            return Path(str(package_config))
    except (ImportError, Exception):
        pass

    # 5. Fall back to script directory (development)
    script_config = Path(__file__).parent / 'config.yaml'
    if script_config.exists():
        return script_config

    raise FileNotFoundError("No configuration file found!")


def merge_configs(*config_paths: Path) -> dict:
    """Merge multiple YAML configs with priority (later overrides earlier).

    Args:
        *config_paths: Path objects to YAML files (priority order)

    Returns:
        Merged configuration dictionary
    """
    merged = {}

    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Deep merge (recursive dict update)
                _deep_merge(merged, config)

    return merged

def _deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge update into base."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


# Usage: Load with priority
default_config = Path(__file__).parent / 'config.default.yaml'
system_config = Path('/etc/wandproject/config.yaml')
user_config = Path.home() / '.config/wandproject/config.yaml'

config = merge_configs(default_config, system_config, user_config)
```

---

## 2. Installation Scripts and Packaging

### 2.1 Modern Python Packaging: pyproject.toml

**setup.py is deprecated for new projects.** Use **pyproject.toml** as the single source of truth.

**pyproject.toml** for Wand Project:
```toml
[build-system]
requires = ["setuptools>=77.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "wand-gesture-recognition"
version = "1.0.0"
description = "Interactive wand gesture recognition using computer vision and ML on Raspberry Pi"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["raspberry-pi", "computer-vision", "gesture-recognition", "opencv", "machine-learning"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Multimedia :: Sound/Audio",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: POSIX :: Linux",
]

# Core dependencies
dependencies = [
    "numpy>=1.21.0",
    "opencv-python>=4.5.0",
    "pillow>=9.0.0",
    "pygame>=2.1.0",
    "scikit-learn>=1.0.0",
    "joblib>=1.1.0",
    "pyyaml>=6.0",
    "python-dotenv>=0.19.0",
]

# Optional dependencies (installable via: pip install wand-gesture-recognition[rpi])
[project.optional-dependencies]
rpi = [
    "picamera2>=0.3.0",
    "pi5neo>=1.0.0",
    "gpiozero>=1.6.0",
    "pigpio>=1.78",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
]

[project.urls]
Homepage = "https://andrewcongdon14.wixsite.com/andrew-congdon/interactive-wand"
Repository = "https://github.com/yourusername/wand-gesture-recognition"
Documentation = "https://github.com/yourusername/wand-gesture-recognition/blob/main/README.md"
Issues = "https://github.com/yourusername/wand-gesture-recognition/issues"

# Entry points for command-line scripts
[project.scripts]
wand-tracking = "wandproject.main:main"
wand-train = "wandproject.training:train_classifier"
wand-setup = "wandproject.setup:run_setup_wizard"

# Package data inclusion
[tool.setuptools.packages.find]
where = ["src"]  # Look for packages in src/ directory
include = ["wandproject*"]
namespaces = false

[tool.setuptools.package-data]
wandproject = [
    "config.default.yaml",
    "models/*.pkl",
    "Sounds/*.mp3",
    "Sounds/*.wav",
]

# Exclude test files from distribution
[tool.setuptools.exclude-package-data]
wandproject = ["tests/*", "*.pyc", "__pycache__"]
```

### 2.2 Recommended Project Structure

```
wand-gesture-recognition/
├── pyproject.toml           # Modern packaging configuration
├── README.md
├── LICENSE
├── .env.example             # Template for .env (commit this)
├── .gitignore
│
├── src/
│   └── wandproject/         # Main package (note: src layout for testing)
│       ├── __init__.py
│       ├── main.py          # Entry point for wand-tracking command
│       ├── config.py        # Configuration management
│       ├── tracking.py      # Blob detection and tracking
│       ├── classifier.py    # Spell recognition
│       ├── hardware.py      # LED, servo, IR control
│       ├── audio.py         # Sound effects management
│       ├── setup.py         # First-run setup wizard
│       │
│       ├── config.default.yaml   # Default configuration
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   └── classifier.pkl    # Pre-trained model
│       │
│       └── Sounds/
│           ├── __init__.py
│           ├── Alohamora.mp3
│           └── Colloportus.mp3
│
├── training/                # Training scripts (not installed)
│   ├── draw_spell_data.py
│   ├── convert_to_training_data.py
│   └── train_spell_classifier.py
│
├── tests/                   # Unit tests
│   ├── test_tracking.py
│   └── test_classifier.py
│
├── docs/
│   └── TRAINING_CUSTOM_SPELLS.md
│
└── systemd/                 # Systemd service files
    └── wand-tracking.service
```

**Why src/ layout?**
- Prevents accidentally importing from source instead of installed package
- Forces proper installation testing
- Standard in modern Python projects

### 2.3 Installation Script for Raspberry Pi

**install.sh** (automated setup script):
```bash
#!/bin/bash
# Automated installation script for Wand Gesture Recognition on Raspberry Pi
# Usage: curl -sSL https://raw.github.com/yourrepo/install.sh | bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Wand Gesture Recognition Installer ===${NC}"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: Not detected as Raspberry Pi. Proceeding anyway...${NC}"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.9+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}Python version check passed: $PYTHON_VERSION${NC}"

# Update system packages
echo ""
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-pil \
    python3-pygame \
    python3-sklearn \
    python3-joblib \
    python3-yaml \
    git

# Raspberry Pi specific packages (optional)
read -p "Install Raspberry Pi hardware libraries (picamera2, GPIO)? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    sudo apt install -y \
        python3-picamera2 \
        python3-gpiozero \
        pigpio

    # Enable pigpio service
    sudo systemctl enable pigpio
    sudo systemctl start pigpio

    # Install pi5neo for LED control
    pip3 install pi5neo --break-system-packages
fi

# Enable required interfaces
echo ""
echo "Enabling SPI and Camera interfaces..."
sudo raspi-config nonint do_spi 0  # 0 = enable
sudo raspi-config nonint do_camera 0

# Clone repository (or use local directory if already cloned)
INSTALL_DIR="/opt/wandproject"
echo ""
read -p "Installation directory [$INSTALL_DIR]: " USER_DIR
INSTALL_DIR=${USER_DIR:-$INSTALL_DIR}

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory exists. Using existing installation.${NC}"
else
    echo "Cloning repository to $INSTALL_DIR..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    git clone https://github.com/yourusername/wand-gesture-recognition.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Install Python package in editable mode
echo ""
echo "Installing Python package..."
pip3 install -e ".[rpi]" --break-system-packages

# Create user config directory
USER_CONFIG_DIR="$HOME/.config/wandproject"
mkdir -p "$USER_CONFIG_DIR"

# Copy default config if user config doesn't exist
if [ ! -f "$USER_CONFIG_DIR/config.yaml" ]; then
    echo "Creating user configuration..."
    cp src/wandproject/config.default.yaml "$USER_CONFIG_DIR/config.yaml"
    echo -e "${GREEN}Config created at: $USER_CONFIG_DIR/config.yaml${NC}"
fi

# Create .env file from template
if [ ! -f "$USER_CONFIG_DIR/.env" ] && [ -f ".env.example" ]; then
    cp .env.example "$USER_CONFIG_DIR/.env"
    echo -e "${YELLOW}Created .env file at: $USER_CONFIG_DIR/.env${NC}"
    echo -e "${YELLOW}Please edit this file to add any secrets or environment-specific settings.${NC}"
fi

# Add user to required groups for GPIO access
echo ""
echo "Adding user to GPIO groups..."
sudo usermod -a -G gpio,i2c,spi,dialout $USER

# Install systemd service (optional)
echo ""
read -p "Install systemd service for auto-start on boot? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/wand-tracking.service"
    sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Wand Gesture Recognition Tracking
After=multi-user.target network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONUNBUFFERED=1"
Environment="WAND_CONFIG_PATH=$USER_CONFIG_DIR/config.yaml"
ExecStart=$(which python3) -m wandproject.main
Restart=on-failure
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable wand-tracking.service

    echo -e "${GREEN}Systemd service installed!${NC}"
    echo "  Start: sudo systemctl start wand-tracking"
    echo "  Stop:  sudo systemctl stop wand-tracking"
    echo "  Logs:  sudo journalctl -u wand-tracking -f"
fi

# Run interactive setup wizard
echo ""
echo "Running first-time setup wizard..."
python3 -m wandproject.setup

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit config: nano $USER_CONFIG_DIR/config.yaml"
echo "  2. Test hardware: python3 -m wandproject.main --test"
echo "  3. Run tracking: wand-tracking"
echo ""
echo -e "${YELLOW}Note: Reboot required for GPIO group membership to take effect.${NC}"
echo ""
read -p "Reboot now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
```

### 2.4 Python Setup Module (First-Run Wizard)

**src/wandproject/setup.py**:
```python
"""Interactive setup wizard for first-time configuration."""

import subprocess
import sys
from pathlib import Path
from typing import Optional
import shutil

def run_setup_wizard():
    """Run interactive first-time setup."""
    print("=" * 60)
    print("  Wand Gesture Recognition - First-Time Setup")
    print("=" * 60)
    print()

    # 1. Validate Python version
    print("[1/6] Validating Python version...")
    if not validate_python_version():
        print("ERROR: Python 3.9+ required")
        sys.exit(1)
    print("  ✓ Python version OK")
    print()

    # 2. Check system dependencies
    print("[2/6] Checking system dependencies...")
    missing_deps = check_system_dependencies()
    if missing_deps:
        print(f"  Missing dependencies: {', '.join(missing_deps)}")
        print("  Run: sudo apt install " + " ".join(missing_deps))
        sys.exit(1)
    print("  ✓ System dependencies OK")
    print()

    # 3. Detect hardware
    print("[3/6] Detecting hardware...")
    hardware_status = detect_hardware()
    print_hardware_status(hardware_status)
    print()

    # 4. Validate file paths
    print("[4/6] Validating project files...")
    if not validate_project_files():
        print("  ERROR: Missing required files")
        sys.exit(1)
    print("  ✓ Project files OK")
    print()

    # 5. Test camera
    print("[5/6] Testing camera...")
    if hardware_status['camera']:
        if test_camera():
            print("  ✓ Camera test passed")
        else:
            print("  ⚠ Camera test failed - check wiring")
    else:
        print("  ⚠ Camera not detected - install picamera2")
    print()

    # 6. Test LED strip
    print("[6/6] Testing LED strip...")
    if hardware_status['spi']:
        if prompt_yes_no("Test LED strip now? (LEDs will flash red)"):
            if test_led_strip():
                print("  ✓ LED test passed")
            else:
                print("  ⚠ LED test failed - check wiring")
    else:
        print("  ⚠ SPI not enabled - run: sudo raspi-config")
    print()

    print("=" * 60)
    print("Setup complete!")
    print()
    print("Configuration file: ~/.config/wandproject/config.yaml")
    print("Run application: wand-tracking")
    print("View logs: journalctl -u wand-tracking -f")
    print("=" * 60)


def validate_python_version() -> bool:
    """Check if Python version is 3.9+."""
    return sys.version_info >= (3, 9)


def check_system_dependencies() -> list:
    """Check for required system packages."""
    required_packages = [
        'python3-opencv',
        'python3-numpy',
        'python3-pil',
    ]

    missing = []
    for package in required_packages:
        try:
            subprocess.run(
                ['dpkg', '-s', package],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            missing.append(package)

    return missing


def detect_hardware() -> dict:
    """Detect available hardware."""
    status = {}

    # Check SPI
    status['spi'] = Path('/dev/spidev0.0').exists()

    # Check camera
    try:
        result = subprocess.run(
            ['rpicam-hello', '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=5
        )
        status['camera'] = 'IMX708' in result.stdout or 'Camera' in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        status['camera'] = False

    # Check GPIO access
    status['gpio'] = Path('/sys/class/gpio').exists()

    # Check picamera2
    try:
        import picamera2
        status['picamera2'] = True
    except ImportError:
        status['picamera2'] = False

    # Check pi5neo
    try:
        import pi5neo
        status['pi5neo'] = True
    except ImportError:
        status['pi5neo'] = False

    return status


def print_hardware_status(status: dict):
    """Print hardware detection results."""
    items = [
        ('SPI Interface', status.get('spi', False)),
        ('Camera Module', status.get('camera', False)),
        ('GPIO Access', status.get('gpio', False)),
        ('picamera2 Library', status.get('picamera2', False)),
        ('pi5neo Library', status.get('pi5neo', False)),
    ]

    for name, detected in items:
        symbol = "✓" if detected else "✗"
        print(f"  {symbol} {name}")


def validate_project_files() -> bool:
    """Validate required project files exist."""
    try:
        from importlib.resources import files

        # Check config file
        config_file = files('wandproject') / 'config.default.yaml'
        if not config_file.is_file():
            print("  ERROR: Missing config.default.yaml")
            return False

        # Check model file
        model_file = files('wandproject') / 'models' / 'classifier.pkl'
        if not model_file.is_file():
            print("  ERROR: Missing classifier.pkl model")
            return False

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_camera() -> bool:
    """Test camera capture."""
    try:
        from picamera2 import Picamera2
        import time

        print("  Initializing camera...")
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()

        time.sleep(2)

        # Capture test frame
        frame = picam2.capture_array()
        picam2.stop()

        # Validate frame
        if frame is not None and frame.shape == (480, 640, 3):
            return True

        return False

    except Exception as e:
        print(f"  Camera error: {e}")
        return False


def test_led_strip() -> bool:
    """Test LED strip with red flash."""
    try:
        from pi5neo import Pi5Neo
        import time

        print("  Flashing LEDs red...")
        neo = Pi5Neo('/dev/spidev0.0', 30, 800)

        # Flash red 3 times
        for _ in range(3):
            neo.fill_strip(255, 0, 0)
            neo.update_strip()
            time.sleep(0.3)
            neo.fill_strip(0, 0, 0)
            neo.update_strip()
            time.sleep(0.3)

        return True

    except Exception as e:
        print(f"  LED error: {e}")
        return False


def prompt_yes_no(question: str) -> bool:
    """Prompt user for yes/no answer."""
    while True:
        answer = input(f"{question} [Y/n]: ").strip().lower()
        if answer in ['y', 'yes', '']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("Please answer 'y' or 'n'")


if __name__ == '__main__':
    run_setup_wizard()
```

---

## 3. Asset Management (Models, Sounds, Data Files)

### 3.1 Modern Approach: importlib.resources (Python 3.9+)

**Why use importlib.resources instead of __file__?**
- Works with zip-installed packages (eggs, wheels)
- Handles namespace packages correctly
- More robust for installed packages
- Performance optimized (replaces slow pkg_resources)

**Accessing Package Assets:**

**src/wandproject/assets.py**:
```python
"""Asset management for models, sounds, and data files."""

from pathlib import Path
from typing import Optional
import sys

# Python 3.9+ uses importlib.resources
if sys.version_info >= (3, 9):
    from importlib.resources import files, as_file
else:
    # Fallback for older Python
    from importlib_resources import files, as_file


class AssetManager:
    """Manage access to packaged assets (models, sounds, data)."""

    def __init__(self, package_name: str = 'wandproject'):
        """Initialize asset manager.

        Args:
            package_name: Name of the package containing assets
        """
        self.package_name = package_name
        self._package_root = files(package_name)

    def get_model_path(self, model_name: str) -> Path:
        """Get path to ML model file.

        Args:
            model_name: Name of model file (e.g., "classifier.pkl")

        Returns:
            Path object to model file

        Example:
            >>> asset_mgr = AssetManager()
            >>> model_path = asset_mgr.get_model_path("classifier.pkl")
            >>> classifier = joblib.load(model_path)
        """
        model_ref = self._package_root / 'models' / model_name

        # For files that need filesystem paths (e.g., joblib.load)
        with as_file(model_ref) as model_path:
            return model_path

    def get_sound_path(self, sound_name: str) -> Path:
        """Get path to sound file.

        Args:
            sound_name: Name of sound file (e.g., "Alohamora.mp3")

        Returns:
            Path object to sound file

        Example:
            >>> asset_mgr = AssetManager()
            >>> sound_path = asset_mgr.get_sound_path("Alohamora.mp3")
            >>> sound = pygame.mixer.Sound(str(sound_path))
        """
        sound_ref = self._package_root / 'Sounds' / sound_name

        with as_file(sound_ref) as sound_path:
            return sound_path

    def read_model_bytes(self, model_name: str) -> bytes:
        """Read model file as bytes (for in-memory loading).

        Args:
            model_name: Name of model file

        Returns:
            Binary content of model file

        Example:
            >>> asset_mgr = AssetManager()
            >>> model_data = asset_mgr.read_model_bytes("classifier.pkl")
            >>> classifier = pickle.loads(model_data)
        """
        model_ref = self._package_root / 'models' / model_name
        return model_ref.read_bytes()

    def list_sounds(self) -> list:
        """List all available sound files.

        Returns:
            List of sound file names
        """
        sounds_dir = self._package_root / 'Sounds'
        return [f.name for f in sounds_dir.iterdir() if f.suffix in ['.mp3', '.wav']]

    def list_models(self) -> list:
        """List all available model files.

        Returns:
            List of model file names
        """
        models_dir = self._package_root / 'models'
        return [f.name for f in models_dir.iterdir() if f.suffix == '.pkl']

    def get_config_path(self) -> Path:
        """Get path to default configuration file.

        Returns:
            Path to config.default.yaml
        """
        config_ref = self._package_root / 'config.default.yaml'

        with as_file(config_ref) as config_path:
            return config_path


# Usage in main application
def load_classifier():
    """Load spell classifier model."""
    import joblib

    asset_mgr = AssetManager()

    # Method 1: Get filesystem path (for libraries requiring file paths)
    model_path = asset_mgr.get_model_path("classifier.pkl")
    classifier = joblib.load(model_path)

    # Method 2: Load from bytes (faster, works in zip packages)
    # model_bytes = asset_mgr.read_model_bytes("classifier.pkl")
    # classifier = pickle.loads(model_bytes)

    return classifier


def load_spell_sound(spell_name: str):
    """Load sound effect for spell."""
    import pygame

    asset_mgr = AssetManager()
    sound_path = asset_mgr.get_sound_path(f"{spell_name}.mp3")

    return pygame.mixer.Sound(str(sound_path))


# List available assets
def show_available_assets():
    """Print all available assets."""
    asset_mgr = AssetManager()

    print("Available Models:")
    for model in asset_mgr.list_models():
        print(f"  - {model}")

    print("\nAvailable Sounds:")
    for sound in asset_mgr.list_sounds():
        print(f"  - {sound}")
```

### 3.2 Fallback Pattern: __file__ for Development

**When to use __file__:**
- Development/testing (not installed as package)
- Scripts that are never packaged
- Quick prototypes

**Best Practice Pattern:**
```python
"""Path resolution with fallback for development vs installed."""

from pathlib import Path
from typing import Optional
import sys

def get_project_root() -> Path:
    """Get project root directory with fallback logic.

    Priority:
        1. Installed package (importlib.resources)
        2. Environment variable (PROJECT_ROOT)
        3. Script location (__file__)

    Returns:
        Absolute Path to project root
    """
    # Try importlib.resources (installed package)
    try:
        from importlib.resources import files
        package_root = files('wandproject')
        return Path(str(package_root)).resolve()
    except (ImportError, Exception):
        pass

    # Try environment variable
    import os
    env_root = os.getenv('PROJECT_ROOT')
    if env_root:
        return Path(env_root).resolve()

    # Fallback to script location (development)
    script_path = Path(__file__).resolve()

    # If this file is in src/wandproject/, go up 2 levels
    if script_path.parent.name == 'wandproject':
        return script_path.parent.parent.parent

    # Otherwise assume script is in project root
    return script_path.parent


def get_asset_path(asset_type: str, asset_name: str) -> Optional[Path]:
    """Get path to asset with development/production compatibility.

    Args:
        asset_type: Type of asset ('models', 'sounds', 'training_data')
        asset_name: Name of asset file

    Returns:
        Absolute Path to asset, or None if not found

    Example:
        >>> model_path = get_asset_path('models', 'classifier.pkl')
        >>> sound_path = get_asset_path('sounds', 'Alohamora.mp3')
    """
    project_root = get_project_root()

    # Try installed package structure
    asset_path = project_root / 'src' / 'wandproject' / asset_type / asset_name
    if asset_path.exists():
        return asset_path

    # Try development structure (flat)
    asset_path = project_root / asset_type / asset_name
    if asset_path.exists():
        return asset_path

    # Try capitalized (e.g., "Sounds" instead of "sounds")
    asset_path = project_root / asset_type.capitalize() / asset_name
    if asset_path.exists():
        return asset_path

    return None


# Usage
if __name__ == '__main__':
    root = get_project_root()
    print(f"Project root: {root}")

    model = get_asset_path('models', 'classifier.pkl')
    print(f"Model path: {model}")

    sound = get_asset_path('sounds', 'Alohamora.mp3')
    print(f"Sound path: {sound}")
```

### 3.3 Handling Large Assets (ML Models)

**Best Practice:** Don't commit large models to git. Use Git LFS or download on first run.

**src/wandproject/model_downloader.py**:
```python
"""Download large ML models on first run."""

import urllib.request
from pathlib import Path
import hashlib
from typing import Optional

def download_model(
    url: str,
    output_path: Path,
    expected_hash: Optional[str] = None,
    force: bool = False
) -> bool:
    """Download ML model file if not present.

    Args:
        url: URL to download from
        output_path: Where to save model
        expected_hash: SHA256 hash for verification (optional)
        force: Force re-download even if file exists

    Returns:
        True if download successful or file already exists
    """
    if output_path.exists() and not force:
        print(f"Model already exists: {output_path.name}")

        # Verify hash if provided
        if expected_hash and not verify_hash(output_path, expected_hash):
            print("Hash mismatch! Re-downloading...")
        else:
            return True

    print(f"Downloading {output_path.name}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Download with progress
        urllib.request.urlretrieve(url, output_path, reporthook=_download_progress)
        print(f"\nDownload complete: {output_path}")

        # Verify hash
        if expected_hash:
            if verify_hash(output_path, expected_hash):
                print("Hash verification passed!")
            else:
                print("WARNING: Hash verification failed!")
                return False

        return True

    except Exception as e:
        print(f"Download failed: {e}")
        return False


def verify_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify file SHA256 hash."""
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)

    return sha256.hexdigest() == expected_hash


def _download_progress(block_num, block_size, total_size):
    """Print download progress."""
    downloaded = block_num * block_size
    percent = min(downloaded * 100 / total_size, 100)
    print(f'\rProgress: {percent:.1f}%', end='')


# Configuration
MODEL_DOWNLOADS = {
    'classifier.pkl': {
        'url': 'https://github.com/yourrepo/releases/download/v1.0/classifier.pkl',
        'hash': 'abc123...',  # SHA256 hash
    },
    'gesture_model.h5': {
        'url': 'https://github.com/yourrepo/releases/download/v1.0/gesture_model.h5',
        'hash': 'def456...',
    },
}


def ensure_models_downloaded() -> bool:
    """Ensure all required models are downloaded."""
    from importlib.resources import files

    models_dir = files('wandproject') / 'models'

    for model_name, config in MODEL_DOWNLOADS.items():
        model_path = Path(str(models_dir / model_name))

        if not download_model(
            config['url'],
            model_path,
            config.get('hash')
        ):
            return False

    return True


if __name__ == '__main__':
    ensure_models_downloaded()
```

---

## 4. Systemd Service Setup for Raspberry Pi

### 4.1 Service File Structure

**/etc/systemd/system/wand-tracking.service**:
```ini
[Unit]
Description=Wand Gesture Recognition Tracking Service
Documentation=https://github.com/yourrepo/wand-gesture-recognition
After=multi-user.target network.target
Wants=pigpio.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/wandproject

# Environment configuration
Environment="PYTHONUNBUFFERED=1"
Environment="WAND_CONFIG_PATH=/home/pi/.config/wandproject/config.yaml"
Environment="ENVIRONMENT=production"

# Main execution
ExecStart=/usr/bin/python3 -m wandproject.main

# Restart configuration
Restart=on-failure
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wand-tracking

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/pi/.config/wandproject

# Resource limits
LimitNOFILE=4096
MemoryLimit=512M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
```

### 4.2 Service Installation Script

**scripts/install_service.sh**:
```bash
#!/bin/bash
# Install systemd service for wand tracking

set -e

SERVICE_NAME="wand-tracking"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
USER=$(whoami)
INSTALL_DIR=$(pwd)

echo "Installing $SERVICE_NAME systemd service..."

# Create service file
sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Wand Gesture Recognition Tracking Service
After=multi-user.target network.target
Wants=pigpio.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONUNBUFFERED=1"
Environment="WAND_CONFIG_PATH=/home/$USER/.config/wandproject/config.yaml"
ExecStart=$(which python3) -m wandproject.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable $SERVICE_NAME.service

echo "Service installed successfully!"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
```

### 4.3 Graceful Shutdown Handling

**src/wandproject/main.py** (with signal handling):
```python
"""Main entry point with graceful shutdown."""

import signal
import sys
import time
from typing import Optional

class WandTrackingApp:
    """Main application with graceful shutdown."""

    def __init__(self):
        self.running = False
        self.camera = None
        self.led_strip = None

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False

    def start(self):
        """Start the application."""
        print("Starting Wand Gesture Recognition...")
        self.running = True

        try:
            # Initialize hardware
            self._init_hardware()

            # Main loop
            while self.running:
                self._process_frame()
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.cleanup()

    def _init_hardware(self):
        """Initialize camera, LED strip, etc."""
        from picamera2 import Picamera2
        from pi5neo import Pi5Neo

        print("Initializing camera...")
        self.camera = Picamera2()
        # ... camera setup ...

        print("Initializing LED strip...")
        self.led_strip = Pi5Neo('/dev/spidev0.0', 30, 800)
        # ... LED setup ...

        print("Hardware initialized!")

    def _process_frame(self):
        """Process single frame (tracking, recognition, etc.)."""
        # Main application logic here
        pass

    def cleanup(self):
        """Clean up resources before exit."""
        print("Cleaning up resources...")

        if self.camera:
            try:
                self.camera.stop()
                print("  Camera stopped")
            except Exception as e:
                print(f"  Error stopping camera: {e}")

        if self.led_strip:
            try:
                self.led_strip.fill_strip(0, 0, 0)
                self.led_strip.update_strip()
                print("  LEDs turned off")
            except Exception as e:
                print(f"  Error turning off LEDs: {e}")

        print("Shutdown complete")


def main():
    """Entry point for wand-tracking command."""
    app = WandTrackingApp()
    app.start()
    sys.exit(0)


if __name__ == '__main__':
    main()
```

### 4.4 Permission Handling for Raspberry Pi

**GPIO Group Setup:**
```bash
# Add user to required groups
sudo usermod -a -G gpio,i2c,spi,dialout,audio,video $USER

# Create udev rule for GPIO permissions
sudo bash -c 'cat > /etc/udev/rules.d/99-gpio.rules' << EOF
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpiomem", GROUP="gpio", MODE="0660"
SUBSYSTEM=="spidev", GROUP="spi", MODE="0660"
SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0660"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Checking Permissions in Code:**
```python
"""Validate GPIO permissions before hardware access."""

import os
from pathlib import Path

def check_gpio_permissions() -> bool:
    """Check if user has GPIO access."""
    # Check group membership
    groups = os.getgroups()
    gpio_gid = None

    try:
        import grp
        gpio_gid = grp.getgrnam('gpio').gr_gid
    except KeyError:
        print("Warning: 'gpio' group not found")
        return False

    if gpio_gid not in groups:
        print("ERROR: User not in 'gpio' group")
        print("Run: sudo usermod -a -G gpio $USER")
        print("Then log out and back in")
        return False

    # Check device access
    if not Path('/dev/gpiomem').exists():
        print("ERROR: /dev/gpiomem not found")
        return False

    if not os.access('/dev/gpiomem', os.R_OK | os.W_OK):
        print("ERROR: No read/write access to /dev/gpiomem")
        return False

    return True


def check_spi_permissions() -> bool:
    """Check if SPI is enabled and accessible."""
    spi_device = Path('/dev/spidev0.0')

    if not spi_device.exists():
        print("ERROR: SPI not enabled")
        print("Run: sudo raspi-config -> Interface Options -> SPI -> Enable")
        return False

    if not os.access(spi_device, os.R_OK | os.W_OK):
        print("ERROR: No SPI access - check 'spi' group membership")
        return False

    return True


def check_camera_permissions() -> bool:
    """Check if camera is enabled."""
    try:
        import subprocess
        result = subprocess.run(
            ['rpicam-hello', '--list-cameras'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("ERROR: Camera not detected")
        print("Run: sudo raspi-config -> Interface Options -> Camera -> Enable")
        return False


def validate_hardware_access():
    """Validate all hardware permissions before starting."""
    checks = [
        ("GPIO", check_gpio_permissions),
        ("SPI", check_spi_permissions),
        ("Camera", check_camera_permissions),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        if check_func():
            print("✓")
        else:
            print("✗")
            all_passed = False

    return all_passed


if __name__ == '__main__':
    if validate_hardware_access():
        print("\nAll hardware checks passed!")
    else:
        print("\nHardware validation failed - see errors above")
        sys.exit(1)
```

---

## 5. Python Best Practices for Path and Error Handling

### 5.1 Pathlib Patterns

**Modern path handling with pathlib (preferred over os.path):**

```python
"""Path handling best practices with pathlib."""

from pathlib import Path
import os

# GOOD: Use pathlib for all path operations
project_root = Path(__file__).parent.resolve()
models_dir = project_root / 'models'
config_file = project_root / 'config.yaml'

# Cross-platform path joining
sound_path = models_dir / 'sounds' / 'Alohamora.mp3'

# Path existence and type checking
if config_file.exists() and config_file.is_file():
    print(f"Config found: {config_file}")

# Create directories (parents=True equivalent to mkdir -p)
output_dir = project_root / 'output'
output_dir.mkdir(parents=True, exist_ok=True)

# Iterate directory contents
for sound_file in (project_root / 'Sounds').glob('*.mp3'):
    print(f"Found sound: {sound_file.name}")

# Recursive search
for pkl_file in project_root.rglob('*.pkl'):
    print(f"Found model: {pkl_file.relative_to(project_root)}")

# Get file parts
print(f"Stem: {sound_path.stem}")  # 'Alohamora'
print(f"Suffix: {sound_path.suffix}")  # '.mp3'
print(f"Parent: {sound_path.parent}")  # Path to Sounds/

# Convert to string when needed (e.g., for legacy APIs)
config_str = str(config_file)

# BAD: Don't use os.path for new code
# os.path.join(project_root, 'models', 'classifier.pkl')  # Old style
```

### 5.2 Error Handling for Missing Assets

**Robust error handling with graceful fallbacks:**

```python
"""Error handling patterns for asset loading."""

from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_model_with_fallback(model_name: str) -> Optional[object]:
    """Load ML model with fallback to default.

    Args:
        model_name: Primary model filename

    Returns:
        Loaded model or None if all attempts fail
    """
    import joblib

    # Try primary model
    try:
        model_path = get_asset_path('models', model_name)
        if model_path:
            logger.info(f"Loading model: {model_path}")
            return joblib.load(model_path)
    except Exception as e:
        logger.warning(f"Failed to load {model_name}: {e}")

    # Try fallback model
    fallback_name = 'classifier_default.pkl'
    try:
        fallback_path = get_asset_path('models', fallback_name)
        if fallback_path:
            logger.info(f"Using fallback model: {fallback_path}")
            return joblib.load(fallback_path)
    except Exception as e:
        logger.error(f"Fallback model also failed: {e}")

    # No model available
    logger.error("No model could be loaded!")
    return None


def load_sound_with_silence_fallback(sound_name: str):
    """Load sound with silent fallback if file missing.

    Args:
        sound_name: Sound filename

    Returns:
        pygame.mixer.Sound object (silent if file missing)
    """
    import pygame
    import numpy as np

    try:
        sound_path = get_asset_path('sounds', sound_name)
        if sound_path:
            logger.info(f"Loading sound: {sound_path}")
            return pygame.mixer.Sound(str(sound_path))
    except Exception as e:
        logger.warning(f"Failed to load {sound_name}: {e}")

    # Create silent sound (1 second at 44100 Hz)
    logger.info(f"Using silent fallback for {sound_name}")
    silent_array = np.zeros((44100, 2), dtype=np.int16)
    return pygame.sndarray.make_sound(silent_array)


def validate_required_files() -> bool:
    """Validate all required files exist before starting.

    Returns:
        True if all required files present, False otherwise
    """
    required_files = {
        'Config': ('', 'config.yaml'),
        'Model': ('models', 'classifier.pkl'),
        'Sound - Alohamora': ('Sounds', 'Alohamora.mp3'),
        'Sound - Colloportus': ('Sounds', 'Colloportus.mp3'),
    }

    missing = []

    for name, (subdir, filename) in required_files.items():
        path = get_asset_path(subdir, filename) if subdir else get_project_root() / filename

        if not path or not path.exists():
            missing.append(name)
            logger.error(f"Missing: {name} ({filename})")

    if missing:
        logger.error(f"Missing {len(missing)} required file(s)")
        return False

    logger.info("All required files present")
    return True


# Usage in main application
def main():
    # Validate files before starting
    if not validate_required_files():
        print("ERROR: Missing required files - cannot start")
        sys.exit(1)

    # Load with fallbacks
    model = load_model_with_fallback('classifier.pkl')
    if model is None:
        print("ERROR: No model available")
        sys.exit(1)

    alohamora_sound = load_sound_with_silence_fallback('Alohamora.mp3')

    # Continue with application...
```

### 5.3 Configuration Validation

**Validate configuration values with pydantic (optional but recommended):**

```python
"""Configuration validation with type checking."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from pathlib import Path


class CameraConfig(BaseModel):
    """Camera configuration with validation."""
    resolution: List[int] = Field(default=[640, 480])
    exposure_time: int = Field(default=8000, ge=1000, le=100000)
    analogue_gain: float = Field(default=6.0, ge=1.0, le=16.0)
    framerate: int = Field(default=30, ge=1, le=90)

    @validator('resolution')
    def validate_resolution(cls, v):
        if len(v) != 2:
            raise ValueError("Resolution must be [width, height]")
        if v[0] < 320 or v[1] < 240:
            raise ValueError("Resolution too low (min 320x240)")
        return v


class LEDConfig(BaseModel):
    """LED strip configuration."""
    device: str = Field(default="/dev/spidev0.0")
    num_leds: int = Field(default=30, ge=1, le=1000)
    timing: int = Field(default=800)
    gpio_pin: int = Field(default=10, ge=0, le=27)

    @validator('device')
    def validate_device(cls, v):
        if not Path(v).exists():
            raise ValueError(f"SPI device not found: {v}")
        return v


class AppConfig(BaseModel):
    """Complete application configuration."""
    camera: CameraConfig = CameraConfig()
    led_strip: LEDConfig = LEDConfig()
    # ... other sections ...

    class Config:
        # Allow extra fields in YAML (forward compatibility)
        extra = 'allow'


# Usage
def load_validated_config(config_path: Path) -> AppConfig:
    """Load and validate configuration."""
    import yaml

    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    try:
        return AppConfig(**config_dict)
    except Exception as e:
        print(f"Configuration validation error: {e}")
        raise
```

---

## 6. Complete Example: Integrated Setup System

### 6.1 Main Entry Point with All Best Practices

**src/wandproject/__main__.py** (allows `python -m wandproject`):
```python
"""Main entry point for wand tracking application."""

import sys
import logging
from pathlib import Path

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with comprehensive error handling."""

    # 1. Load environment configuration
    try:
        from .config import EnvironmentConfig, Config, find_config_file

        env = EnvironmentConfig()
        logger.info(f"Running in {env.environment} mode")

        # Find and load configuration
        config_path = find_config_file()
        logger.info(f"Using config: {config_path}")
        config = Config(config_path)

    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # 2. Validate hardware permissions (Raspberry Pi)
    try:
        from .hardware import validate_hardware_access

        if not validate_hardware_access():
            logger.error("Hardware validation failed")
            sys.exit(1)

    except ImportError:
        logger.warning("Hardware validation skipped (not on Raspberry Pi)")

    # 3. Validate required files
    try:
        from .assets import validate_required_files

        if not validate_required_files():
            logger.error("Missing required files")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Asset validation error: {e}")
        sys.exit(1)

    # 4. Start main application
    try:
        from .main import WandTrackingApp

        app = WandTrackingApp(config, env)
        app.start()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### 6.2 Quick Start Guide for Users

**README_INSTALLATION.md**:
```markdown
# Quick Installation Guide

## Option 1: Automated Installation (Recommended)

```bash
curl -sSL https://raw.github.com/yourrepo/install.sh | bash
```

This will:
- Install system dependencies
- Enable SPI and Camera interfaces
- Install Python package
- Create systemd service
- Run first-time setup wizard

## Option 2: Manual Installation

### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv python3-picamera2 \
                     python3-numpy python3-pil python3-pygame \
                     python3-sklearn python3-yaml git

# Raspberry Pi specific
sudo apt install -y python3-gpiozero pigpio
sudo systemctl enable pigpio
```

### 2. Enable Interfaces
```bash
sudo raspi-config
# Enable: SPI, Camera
```

### 3. Install Package
```bash
git clone https://github.com/yourrepo/wand-gesture-recognition.git
cd wand-gesture-recognition
pip3 install -e ".[rpi]" --break-system-packages
```

### 4. Run Setup Wizard
```bash
wand-setup
```

### 5. Test
```bash
wand-tracking --test
```

## Configuration

Edit: `~/.config/wandproject/config.yaml`

Key settings:
- `led_strip.num_leds`: Number of LEDs in your strip
- `camera.exposure_time`: Adjust for IR brightness
- `blob_detection.min_threshold`: Wand detection sensitivity

## Troubleshooting

### Camera Not Detected
```bash
rpicam-hello --list-cameras
# If not found: sudo raspi-config -> Enable Camera
```

### LEDs Not Working
```bash
ls /dev/spidev0.0
# If not found: sudo raspi-config -> Enable SPI
```

### Permission Errors
```bash
sudo usermod -a -G gpio,spi,dialout $USER
# Log out and back in
```

### View Logs
```bash
journalctl -u wand-tracking -f
```
```

---

## 7. Key Recommendations Summary

### For Your Wand Project Specifically:

1. **Packaging:**
   - Create `pyproject.toml` with setuptools backend
   - Use src/ layout: `src/wandproject/`
   - Package ML models and sounds with `package-data`

2. **Configuration:**
   - Use YAML for application config (camera, LED, GPIO settings)
   - Use .env for environment variables (development vs production)
   - Implement config priority: env var → user config → system config → default

3. **Asset Management:**
   - Use `importlib.resources.files()` for accessing packaged assets
   - Provide fallback to __file__ for development
   - Download large models on first run (don't commit to git)

4. **Installation:**
   - Create install.sh script for one-command setup
   - Implement interactive setup wizard (wand-setup command)
   - Validate hardware access before starting

5. **Raspberry Pi Specific:**
   - Create systemd service for auto-start
   - Handle GPIO permissions (gpio, spi groups)
   - Graceful shutdown with signal handlers
   - Validate SPI/Camera enabled before hardware access

6. **Paths:**
   - Use pathlib everywhere (not os.path)
   - Resolve paths dynamically (never hardcode)
   - Support both development (script location) and installed (package) modes

7. **Error Handling:**
   - Validate all files before starting
   - Provide graceful fallbacks (silent sounds, default models)
   - Log errors clearly with actionable messages

---

## Sources

### Modern Python Packaging:
- [Writing pyproject.toml - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [pyproject.toml specification - Python Packaging User Guide](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [How to modernize a setup.py based project - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/modernize-setup-py-project/)
- [How to Manage Python Projects With pyproject.toml - Real Python](https://realpython.com/python-pyproject-toml/)
- [Modern Packaging with pyproject.toml - Billy Poon](https://billypoon.com/insights/modern-packaging-with-pyproject.toml-a-clear-guide-to-building-and-publishing-python-projects)

### Configuration Management:
- [Configuring Python Projects with INI, TOML, YAML, and ENV files - Hackers and Slackers](https://hackersandslackers.com/simplify-your-python-projects-configuration/)
- [Configuration files in Python - Martin Thoma](https://martin-thoma.com/configuration-files-in-python/)
- [INI vs. YAML: working with configuration files in Python - Honeybadger](https://www.honeybadger.io/blog/python-ini-vs-yaml/)
- [Working with Python Configuration Files - Configu](https://configu.com/blog/working-with-python-configuration-files-tutorial-best-practices/)

### Environment Variables:
- [Using Python Environment Variables with Python Dotenv - GeeksforGeeks](https://www.geeksforgeeks.org/python/using-python-environment-variables-with-python-dotenv/)
- [python-dotenv GitHub](https://github.com/theskumar/python-dotenv)
- [Using .env Files for Environment Variables - DEV Community](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1)
- [How to use dotenv package - Python Engineer](https://www.python-engineer.com/posts/dotenv-python/)

### Raspberry Pi Systemd Services:
- [Making a Python Script Run on Startup (systemd) - Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=343733)
- [Run python script as systemd service - Raspberry Pi Stack Exchange](https://raspberrypi.stackexchange.com/questions/147133/run-python-script-as-systemd-service)
- [The ultimate guide on using systemd to autostart scripts - TheDigitalPictureFrame.com](https://www.thedigitalpictureframe.com/ultimate-guide-systemd-autostart-scripts-raspberry-pi/)
- [How to run a python script as a service in Raspberry Pi - GitHub Gist](https://gist.github.com/emxsys/a507f3cad928e66f6410e7ac28e2990f)
- [How To Autorun A Python Script On Boot Using systemd - Raspberry Pi Spy](https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/)

### Path Management and Asset Loading:
- [Relative paths in Python - Stack Overflow](https://stackoverflow.com/questions/918154/relative-paths-in-python)
- [How to get an absolute file path in Python - Stack Overflow](https://stackoverflow.com/questions/51520/how-to-get-an-absolute-file-path-in-python)
- [pathlib — Object-oriented filesystem paths - Python Docs](https://docs.python.org/3/library/pathlib.html)
- [How to refer to relative paths of resources - Stack Overflow](https://stackoverflow.com/questions/1270951/how-to-refer-to-relative-paths-of-resources-when-working-with-a-code-repository)

### importlib.resources:
- [importlib.resources – Package resource reading - Python Docs](https://docs.python.org/3/library/importlib.resources.html)
- [Using importlib_resources - importlib_resources Documentation](https://importlib-resources.readthedocs.io/en/latest/using.html)
- [Why use importlib.resources over __file__? - Stack Overflow](https://stackoverflow.com/questions/72886257/why-use-importlib-resources-over-file)
- [Migration guide - importlib_resources](https://importlib-resources.readthedocs.io/en/latest/migration.html)

### ML Model Packaging:
- [ML Model Packaging - Neptune.ai](https://neptune.ai/blog/ml-model-packaging)
- [Packaging Libraries with ML models in Python - Stack Overflow](https://stackoverflow.com/questions/63342686/packaging-libraries-with-ml-models-in-python)
- [Building a Python Package for your ML model - Medium](https://ashukumar27.medium.com/building-a-python-package-for-your-ml-model-28ad8c7030e0)
- [Packaging data and machine learning models for sharing - DVC](https://dvc.org/blog/scipy-2020-dvc-poster/)

### Raspberry Pi Permissions:
- [Fixing Cannot Access GPIO Permission Errors in Raspberry Pi](https://38-3d.co.uk/blogs/blog/fixing-cannot-access-gpio-permission-errors-in-raspberry-pi)
- [Playing sounds with Python on a Raspberry Pi - Jeff Geerling](https://www.jeffgeerling.com/blog/2022/playing-sounds-python-on-raspberry-pi)
- [Access GPIO as non-root - Stack Overflow](https://stackoverflow.com/questions/30938991/access-gpio-sys-class-gpio-as-non-root)

---

**Report Prepared:** 2025-11-22
**Total Sources:** 40+ curated documentation references
**Next Steps:** Implement pyproject.toml, create install.sh script, add importlib.resources for asset management
