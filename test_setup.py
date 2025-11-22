#!/usr/bin/env python3
"""
Setup Validation Script for Interactive Wand Project
Tests hardware, permissions, dependencies, and configuration
"""

import sys
import subprocess
from pathlib import Path
import importlib.util

from utils.terminal_ui import Colors, print_header
from utils.hardware_checks import check_camera_available, check_spi_device, check_system_command

def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        print(f"{Colors.GREEN}✓{Colors.NC} {package_name}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.NC} {package_name} - Not installed")
        return False

def check_system_command_with_desc(command, description):
    """Check if a system command exists (wrapper for utils function)"""
    success, message = check_system_command(command)
    if success:
        print(f"{Colors.GREEN}✓{Colors.NC} {description}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {description} - {message}")
    return success

def test_python_dependencies():
    """Test all required Python packages"""
    print_header("Testing Python Dependencies")

    packages = [
        ("numpy", "numpy"),
        ("opencv-python", "cv2"),
        ("picamera2", "picamera2"),
        ("pygame", "pygame"),
        ("scikit-learn", "sklearn"),
        ("joblib", "joblib"),
        ("pillow", "PIL"),
        ("pandas", "pandas"),
        ("PyYAML", "yaml"),
        ("pi5neo", "pi5neo"),
    ]

    results = []
    for package_name, import_name in packages:
        results.append(check_python_package(package_name, import_name))

    return all(results)

def test_system_tools():
    """Test required system tools"""
    print_header("Testing System Tools")

    tools = [
        ("git", "Git version control"),
        ("rpicam-hello", "Raspberry Pi camera tools"),
    ]

    results = []
    for command, description in tools:
        results.append(check_system_command_with_desc(command, description))

    return all(results)

def test_configuration():
    """Test configuration loading and validation"""
    print_header("Testing Configuration")

    try:
        from config_loader import get_config
        config = get_config()
        print(f"{Colors.GREEN}✓{Colors.NC} Configuration loaded successfully")
        print(f"  Project: {config.project.name} v{config.project.version}")
        print(f"  LED Count: {config.hardware.led.count}")
        print(f"  Camera Resolution: {config.hardware.camera.resolution}")

        # Validate assets
        print(f"\n{Colors.BOLD}Validating Assets:{Colors.NC}")
        missing = config.validate_assets()
        if missing:
            print(f"{Colors.YELLOW}⚠{Colors.NC}  Missing assets:")
            for item in missing:
                print(f"  {Colors.RED}✗{Colors.NC} {item}")
            return False
        else:
            print(f"{Colors.GREEN}✓{Colors.NC} All required assets found")
            return True

    except FileNotFoundError:
        print(f"{Colors.RED}✗{Colors.NC} config.yaml not found")
        print(f"  Run: {Colors.BLUE}python3 setup_wizard.py{Colors.NC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} Configuration error: {e}")
        return False

def test_hardware_permissions():
    """Test hardware access permissions"""
    print_header("Testing Hardware Permissions")

    try:
        from config_loader import get_config
        config = get_config()

        issues = config.validate_hardware_permissions()
        if issues:
            print(f"{Colors.YELLOW}⚠{Colors.NC}  Hardware permission issues:")
            for issue in issues:
                print(f"  {Colors.RED}✗{Colors.NC} {issue}")
            return False
        else:
            print(f"{Colors.GREEN}✓{Colors.NC} All hardware permissions OK")
            return True

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} Hardware check failed: {e}")
        return False

def test_camera():
    """Test camera availability"""
    print_header("Testing Camera")
    success, message = check_camera_available()
    if success:
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {message}")
    return success

def test_spi_device():
    """Test SPI device availability"""
    print_header("Testing SPI Device")

    try:
        from config_loader import get_config
        config = get_config()
        spi_device_path = config.hardware.led.spi_device
    except:
        spi_device_path = '/dev/spidev0.0'

    success, message = check_spi_device(spi_device_path)
    if success:
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {message}")
    return success

def test_led_strip():
    """Test LED strip communication"""
    print_header("Testing LED Strip")

    try:
        from pi5neo import Pi5Neo
        from config_loader import get_config
        config = get_config()

        print(f"Attempting to initialize LED strip...")
        neo = Pi5Neo(
            config.hardware.led.spi_device,
            config.hardware.led.count,
            config.hardware.led.timing
        )

        print(f"{Colors.GREEN}✓{Colors.NC} LED strip initialized ({config.hardware.led.count} LEDs)")

        # Brief test flash
        print(f"Testing LED flash (red for 1 second)...")
        neo.fill_strip(50, 0, 0)  # Dim red
        neo.update_strip()
        import time
        time.sleep(1)
        neo.fill_strip(0, 0, 0)
        neo.update_strip()

        print(f"{Colors.GREEN}✓{Colors.NC} LED test complete")
        return True

    except PermissionError:
        print(f"{Colors.RED}✗{Colors.NC} Permission denied for SPI device")
        print(f"  Add user to spi group and reboot")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} LED strip test failed: {e}")
        return False

def test_audio():
    """Test audio system"""
    print_header("Testing Audio System")

    try:
        import pygame.mixer as mixer
        from config_loader import get_config
        config = get_config()

        mixer.init()
        print(f"{Colors.GREEN}✓{Colors.NC} Audio system initialized")

        # Check if sound files exist
        sounds_dir = config.paths.sounds
        required_sounds = ['Alohamora.mp3', 'Colloportus.mp3', 'loop.mp3']
        all_found = True

        for sound_file in required_sounds:
            sound_path = sounds_dir / sound_file
            if sound_path.exists():
                print(f"{Colors.GREEN}✓{Colors.NC} Found: {sound_file}")
            else:
                print(f"{Colors.RED}✗{Colors.NC} Missing: {sound_file}")
                all_found = False

        mixer.quit()
        return all_found

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} Audio test failed: {e}")
        return False

def test_ml_model():
    """Test ML model loading"""
    print_header("Testing ML Model")

    try:
        from config_loader import get_config
        import joblib

        config = get_config()
        model_path = config.paths.model

        if model_path.exists():
            print(f"{Colors.GREEN}✓{Colors.NC} Model file found: {model_path.name}")

            # Try loading model
            model = joblib.load(str(model_path))
            print(f"{Colors.GREEN}✓{Colors.NC} Model loaded successfully")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.NC} Model file not found: {model_path}")
            print(f"  Train model with:")
            print(f"  {Colors.BLUE}cd DatasetCreation && python3 train_spell_classifier.py{Colors.NC}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.NC} Model test failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.NC}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.NC}")

    print()

    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed! System ready.{Colors.NC}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.NC}")
        print(f"  1. Run wand tracker: {Colors.BOLD}python3 HarryPotterWandcv.py{Colors.NC}")
        print(f"  2. Train custom spells: {Colors.BOLD}cd DatasetCreation{Colors.NC}")
        print(f"\n{Colors.GREEN}Happy spell casting! 🪄✨{Colors.NC}")
        return True
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed{Colors.NC}")
        print(f"\n{Colors.BLUE}Troubleshooting:{Colors.NC}")
        print(f"  • Check error messages above")
        print(f"  • Review: {Colors.BOLD}docs/CONFIGURATION.md{Colors.NC}")
        print(f"  • Re-run installer: {Colors.BOLD}./install.sh{Colors.NC}")
        print(f"  • Reconfigure: {Colors.BOLD}python3 setup_wizard.py{Colors.NC}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}║   Interactive Wand - Setup Validator        ║{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════╝{Colors.NC}")

    # Run all tests
    results = {
        'Python Dependencies': test_python_dependencies(),
        'System Tools': test_system_tools(),
        'Configuration': test_configuration(),
        'Hardware Permissions': test_hardware_permissions(),
        'Camera': test_camera(),
        'SPI Device': test_spi_device(),
        'LED Strip': test_led_strip(),
        'Audio System': test_audio(),
        'ML Model': test_ml_model(),
    }

    # Print summary
    success = print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.NC}")
        sys.exit(1)
