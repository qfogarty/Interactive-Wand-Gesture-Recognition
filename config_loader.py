"""
Configuration loader for Interactive Wand project.
Handles YAML config loading with validation and defaults.
"""

import yaml
from pathlib import Path
import sys
import os

from utils.hardware_checks import check_camera_available, check_spi_device, check_gpio_access


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
        success, message = check_spi_device(self.data.hardware.led.spi_device)
        if not success:
            issues.append(message)

        # Check camera
        success, message = check_camera_available()
        if not success:
            issues.append(message)

        # Check GPIO access (for servo/IR if enabled)
        if self.data.hardware.servo.enabled or self.data.hardware.ir_illuminator.enabled:
            success, message = check_gpio_access()
            if not success:
                issues.append(message)

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
