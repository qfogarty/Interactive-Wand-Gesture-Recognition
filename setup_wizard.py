#!/usr/bin/env python3
"""
Interactive Setup Wizard for Interactive Wand Project
Guides users through hardware configuration and testing
"""

import yaml
import subprocess
from pathlib import Path
import sys

from utils.terminal_ui import Colors, print_banner
from utils.hardware_checks import check_camera_available, check_spi_device
from utils.config_builder import build_final_config, show_completion_message

def ask_yes_no(question, default=True):
    """Ask a yes/no question"""
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        response = input(f"{Colors.YELLOW}{question}{Colors.NC}{suffix}").strip().lower()
        if response == "":
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print(f"{Colors.RED}Please answer 'y' or 'n'{Colors.NC}")

def ask_number(question, default, min_val=None, max_val=None):
    """Ask for a number with validation"""
    while True:
        response = input(f"{Colors.YELLOW}{question}{Colors.NC} [{default}]: ").strip()
        if response == "":
            return default
        try:
            value = int(response) if isinstance(default, int) else float(response)
            if min_val is not None and value < min_val:
                print(f"{Colors.RED}Value must be >= {min_val}{Colors.NC}")
                continue
            if max_val is not None and value > max_val:
                print(f"{Colors.RED}Value must be <= {max_val}{Colors.NC}")
                continue
            return value
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.NC}")

def configure_led_strip() -> dict:
    """Configure LED strip parameters"""
    print(f"{Colors.BOLD}LED Strip (WS2812B):{Colors.NC}")
    return {
        'led_count': ask_number("Number of LEDs in strip", 30, min_val=1, max_val=300),
        'led_timing': ask_number("LED timing (800 for WS2812B)", 800),
        'led_spi': input(f"{Colors.YELLOW}SPI device path{Colors.NC} [/dev/spidev0.0]: ").strip() or "/dev/spidev0.0"
    }


def configure_camera_settings(ir_adjustments: dict = None) -> dict:
    """Configure camera with optional IR adjustments"""
    print(f"\n{Colors.BOLD}Camera Configuration:{Colors.NC}")

    config = {
        'camera_width': ask_number("Camera width (pixels)", 640, min_val=320),
        'camera_height': ask_number("Camera height (pixels)", 480, min_val=240),
        'camera_exposure': ask_number("Camera exposure time (microseconds)", 8000, min_val=100),
        'camera_gain': ask_number("Camera analogue gain", 6.0, min_val=1.0),
        'camera_brightness': ask_number("Camera brightness adjustment", -0.3)
    }

    # Apply IR adjustments if provided
    if ir_adjustments:
        config.update(ir_adjustments)

    return config


def configure_servo_motor() -> dict:
    """Configure servo motor if enabled"""
    print(f"\n{Colors.BOLD}Servo Motor (Optional):{Colors.NC}")
    print("Note: Servo is optional - system works without it.")

    enabled = ask_yes_no("Enable servo motor support?", default=False)

    config = {'servo_enabled': enabled}

    if enabled:
        config['servo_gpio'] = ask_number("Servo GPIO pin", 12, min_val=0, max_val=27)
        config['servo_min_pulse'] = ask_number("Minimum pulse width", 0.0005)
        config['servo_max_pulse'] = ask_number("Maximum pulse width", 0.0025)

    return config


def configure_ir_illuminator() -> tuple:
    """
    Configure IR illuminator with type selection.

    Returns:
        Tuple of (ir_config, camera_adjustments)
    """
    print(f"\n{Colors.BOLD}IR Illuminator:{Colors.NC}")
    print("Choose your IR illuminator type:")
    print("  1. Camera-mounted IR ring (5W, mounts on camera - SIMPLE)")
    print("  2. External IR board (12V, separate board - MORE POWERFUL)")

    ir_choice = input(f"{Colors.YELLOW}Select option [1/2]{Colors.NC}: ").strip()

    if ir_choice == "1":
        print(f"{Colors.GREEN}✓ Camera-mounted IR selected{Colors.NC}")
        print(f"  Camera settings will be adjusted for dimmer IR source")
        return (
            {'ir_type': 'camera-mounted', 'ir_enabled': False},
            {'camera_exposure': 12000, 'camera_gain': 8.0}
        )
    elif ir_choice == "2":
        enabled = ask_yes_no("Enable GPIO control (PWM brightness)?", default=True)
        config = {'ir_type': 'external', 'ir_enabled': enabled}

        if enabled:
            config['ir_gpio'] = ask_number("IR illuminator GPIO pin", 18, min_val=0, max_val=27)
            config['ir_pwm_freq'] = ask_number("PWM frequency (Hz)", 1000, min_val=100)

        print(f"{Colors.GREEN}✓ External IR board selected{Colors.NC}")
        return (config, None)
    else:
        print(f"{Colors.YELLOW}Invalid choice, defaulting to camera-mounted IR{Colors.NC}")
        return (
            {'ir_type': 'camera-mounted', 'ir_enabled': False},
            {'camera_exposure': 12000, 'camera_gain': 8.0}
        )


def test_camera():
    """Test camera availability"""
    print(f"\n{Colors.BLUE}Testing camera...{Colors.NC}")
    success, message = check_camera_available()
    if success:
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {message}")
    return success

def test_spi():
    """Test SPI interface availability"""
    print(f"\n{Colors.BLUE}Testing SPI interface...{Colors.NC}")
    success, message = check_spi_device()
    if success:
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")
    else:
        print(f"{Colors.RED}✗{Colors.NC} {message}")
    return success

def configure_hardware():
    """Interactive hardware configuration"""
    print(f"\n{Colors.BOLD}=== Hardware Configuration ==={Colors.NC}\n")

    # Gather configurations
    led_config = configure_led_strip()
    ir_config, camera_adjustments = configure_ir_illuminator()
    camera_config = configure_camera_settings(camera_adjustments)
    servo_config = configure_servo_motor()

    # Merge all configs
    return {
        **led_config,
        **camera_config,
        **servo_config,
        **ir_config
    }

def configure_detection():
    """Configure detection parameters"""
    print(f"\n{Colors.BOLD}=== Detection Configuration ==={Colors.NC}\n")

    config = {}

    print(f"{Colors.BOLD}Blob Detector:{Colors.NC}")
    print("These settings control how the wand tip is detected.")
    config['min_threshold'] = ask_number("Minimum threshold", 180, min_val=0, max_val=255)
    config['max_threshold'] = ask_number("Maximum threshold", 255, min_val=0, max_val=255)
    config['min_area'] = ask_number("Minimum blob area (pixels)", 15, min_val=1)
    config['max_area'] = ask_number("Maximum blob area (pixels)", 500, min_val=1)
    config['min_circularity'] = ask_number("Minimum circularity (0-1)", 0.75)
    config['min_inertia'] = ask_number("Minimum inertia ratio (0-1)", 0.3)

    print(f"\n{Colors.BOLD}Gesture Detection:{Colors.NC}")
    config['presence_duration'] = ask_number("Wand presence duration (seconds)", 0.6)
    config['stillness_duration'] = ask_number("Stillness duration for spell completion (seconds)", 1.0)
    config['movement_threshold'] = ask_number("Movement threshold (pixels)", 6, min_val=1)

    return config

def configure_audio():
    """Configure audio settings"""
    print(f"\n{Colors.BOLD}=== Audio Configuration ==={Colors.NC}\n")

    config = {}
    config['background_volume'] = ask_number("Background music volume (0.0-1.0)", 0.6, min_val=0.0, max_val=1.0)
    config['spell_volume'] = ask_number("Spell sound effect volume (0.0-1.0)", 1.0, min_val=0.0, max_val=1.0)

    return config

def save_config(config_data, output_path):
    """Save configuration to YAML file"""
    try:
        with open(output_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        print(f"\n{Colors.GREEN}✓ Configuration saved to: {output_path}{Colors.NC}")
        return True
    except Exception as e:
        print(f"\n{Colors.RED}✗ Failed to save configuration: {e}{Colors.NC}")
        return False

def main():
    """Main wizard flow"""
    print_banner()

    # Get project root
    project_root = Path(__file__).parent.resolve()
    config_path = project_root / "config.yaml"

    # Check if config already exists
    if config_path.exists():
        print(f"{Colors.YELLOW}⚠️  Configuration file already exists{Colors.NC}")
        if not ask_yes_no("Overwrite existing configuration?", default=False):
            print("Setup cancelled.")
            sys.exit(0)
        print()

    # Run hardware tests
    print(f"\n{Colors.BOLD}=== Hardware Test ==={Colors.NC}")
    camera_ok = test_camera()
    spi_ok = test_spi()

    if not camera_ok or not spi_ok:
        print(f"\n{Colors.YELLOW}⚠️  Some hardware tests failed{Colors.NC}")
        if not ask_yes_no("Continue with configuration anyway?", default=True):
            print("Setup cancelled.")
            sys.exit(1)

    # Gather all configuration
    hw_config = configure_hardware()
    detect_config = configure_detection()
    audio_config = configure_audio()

    # Build final config structure
    final_config = build_final_config(hw_config, detect_config, audio_config)

    # Preview configuration
    print(f"\n{Colors.BOLD}=== Configuration Preview ==={Colors.NC}")
    print(yaml.dump(final_config, default_flow_style=False, sort_keys=False))

    # Confirm and save
    if ask_yes_no("\nSave this configuration?", default=True):
        if save_config(final_config, config_path):
            show_completion_message()
        else:
            sys.exit(1)
    else:
        print("Setup cancelled.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {e}{Colors.NC}")
        sys.exit(1)
