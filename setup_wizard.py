#!/usr/bin/env python3
"""
Interactive Setup Wizard for Interactive Wand Project
Guides users through hardware configuration and testing
"""

import yaml
import subprocess
from pathlib import Path
import sys

# ANSI color codes
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

def print_banner():
    """Display welcome banner"""
    print(f"{Colors.BLUE}╔══════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║   Interactive Wand Setup Wizard             ║{Colors.NC}")
    print(f"{Colors.BLUE}║   Configure Your Hardware                    ║{Colors.NC}")
    print(f"{Colors.BLUE}╚══════════════════════════════════════════════╝{Colors.NC}")
    print()

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

def test_camera():
    """Test camera availability"""
    print(f"\n{Colors.BLUE}Testing camera...{Colors.NC}")
    try:
        result = subprocess.run(
            ['rpicam-hello', '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0 and 'No cameras available' not in result.stderr:
            print(f"{Colors.GREEN}✓ Camera detected{Colors.NC}")
            return True
        else:
            print(f"{Colors.RED}✗ No camera detected{Colors.NC}")
            print("  Enable camera with: sudo raspi-config")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{Colors.RED}✗ Camera tools not available{Colors.NC}")
        return False

def test_spi():
    """Test SPI device availability"""
    print(f"\n{Colors.BLUE}Testing SPI interface...{Colors.NC}")
    spi_device = Path('/dev/spidev0.0')
    if spi_device.exists():
        print(f"{Colors.GREEN}✓ SPI device found{Colors.NC}")
        return True
    else:
        print(f"{Colors.RED}✗ SPI device not found{Colors.NC}")
        print("  Enable SPI with: sudo raspi-config")
        return False

def configure_hardware():
    """Interactive hardware configuration"""
    print(f"\n{Colors.BOLD}=== Hardware Configuration ==={Colors.NC}\n")

    config = {}

    # LED Strip
    print(f"{Colors.BOLD}LED Strip (WS2812B):{Colors.NC}")
    config['led_count'] = ask_number("Number of LEDs in strip", 30, min_val=1, max_val=300)
    config['led_timing'] = ask_number("LED timing (800 for WS2812B)", 800)
    config['led_spi'] = input(f"{Colors.YELLOW}SPI device path{Colors.NC} [/dev/spidev0.0]: ").strip() or "/dev/spidev0.0"

    # Camera
    print(f"\n{Colors.BOLD}Camera Configuration:{Colors.NC}")
    config['camera_width'] = ask_number("Camera width (pixels)", 640, min_val=320)
    config['camera_height'] = ask_number("Camera height (pixels)", 480, min_val=240)
    config['camera_exposure'] = ask_number("Camera exposure time (microseconds)", 8000, min_val=100)
    config['camera_gain'] = ask_number("Camera analogue gain", 6.0, min_val=1.0)
    config['camera_brightness'] = ask_number("Camera brightness adjustment", -0.3)

    # Servo (Optional)
    print(f"\n{Colors.BOLD}Servo Motor (Optional):{Colors.NC}")
    print("Note: You indicated you don't have a servo, but you can enable it later if needed.")
    config['servo_enabled'] = ask_yes_no("Enable servo motor support?", default=False)
    if config['servo_enabled']:
        config['servo_gpio'] = ask_number("Servo GPIO pin", 12, min_val=0, max_val=27)
        config['servo_min_pulse'] = ask_number("Minimum pulse width", 0.0005)
        config['servo_max_pulse'] = ask_number("Maximum pulse width", 0.0025)

    # IR Illuminator (Optional)
    print(f"\n{Colors.BOLD}IR Illuminator:{Colors.NC}")
    print("Choose your IR illuminator type:")
    print("  1. Camera-mounted IR ring (5W, mounts on camera - SIMPLE)")
    print("  2. External IR board (12V, separate board - MORE POWERFUL)")

    ir_choice = input(f"{Colors.YELLOW}Select option [1/2]{Colors.NC}: ").strip()

    if ir_choice == "1":
        # Camera-mounted IR
        config['ir_type'] = 'camera-mounted'
        config['ir_enabled'] = False  # No GPIO control
        print(f"{Colors.GREEN}✓ Camera-mounted IR selected - no GPIO control needed{Colors.NC}")
        print(f"  Note: Camera settings will be adjusted for dimmer IR source")
        # Adjust camera settings for camera-mounted IR
        config['camera_exposure'] = 12000  # Increase exposure
        config['camera_gain'] = 8.0        # Increase gain
    elif ir_choice == "2":
        # External IR board
        config['ir_type'] = 'external'
        config['ir_enabled'] = ask_yes_no("Enable GPIO control (PWM brightness)?", default=True)
        if config['ir_enabled']:
            config['ir_gpio'] = ask_number("IR illuminator GPIO pin", 18, min_val=0, max_val=27)
            config['ir_pwm_freq'] = ask_number("PWM frequency (Hz)", 1000, min_val=100)
        print(f"{Colors.GREEN}✓ External IR board selected{Colors.NC}")
    else:
        # Default to camera-mounted (simplest)
        print(f"{Colors.YELLOW}Invalid choice, defaulting to camera-mounted IR{Colors.NC}")
        config['ir_type'] = 'camera-mounted'
        config['ir_enabled'] = False

    return config

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
    final_config = {
        'project': {
            'name': 'Interactive Wand',
            'version': '1.0.0'
        },
        'hardware': {
            'led': {
                'count': hw_config['led_count'],
                'timing': hw_config['led_timing'],
                'spi_device': hw_config['led_spi'],
                'gpio_pin': 19
            },
            'camera': {
                'resolution': [hw_config['camera_width'], hw_config['camera_height']],
                'exposure_time': hw_config['camera_exposure'],
                'analogue_gain': hw_config['camera_gain'],
                'brightness': hw_config['camera_brightness']
            },
            'servo': {
                'enabled': hw_config['servo_enabled'],
                'gpio_pin': hw_config.get('servo_gpio', 12),
                'min_pulse_width': hw_config.get('servo_min_pulse', 0.0005),
                'max_pulse_width': hw_config.get('servo_max_pulse', 0.0025)
            },
            'ir_illuminator': {
                'enabled': hw_config['ir_enabled'],
                'gpio_pin': hw_config.get('ir_gpio', 18),
                'pwm_frequency': hw_config.get('ir_pwm_freq', 1000)
            }
        },
        'detection': {
            'blob_detector': {
                'min_threshold': detect_config['min_threshold'],
                'max_threshold': detect_config['max_threshold'],
                'min_area': detect_config['min_area'],
                'max_area': detect_config['max_area'],
                'min_circularity': detect_config['min_circularity'],
                'min_inertia_ratio': detect_config['min_inertia']
            },
            'gesture': {
                'presence_duration': detect_config['presence_duration'],
                'stillness_duration': detect_config['stillness_duration'],
                'movement_threshold': detect_config['movement_threshold']
            }
        },
        'audio': {
            'background_volume': audio_config['background_volume'],
            'spell_volume': audio_config['spell_volume']
        },
        'paths': {
            'sounds_dir': 'Sounds',
            'model_file': 'new_custom_classifier.pkl',
            'lastframe_file': 'lastframe.jpg',
            'dataset_dir': 'DatasetCreation'
        }
    }

    # Preview configuration
    print(f"\n{Colors.BOLD}=== Configuration Preview ==={Colors.NC}")
    print(yaml.dump(final_config, default_flow_style=False, sort_keys=False))

    # Confirm and save
    if ask_yes_no("\nSave this configuration?", default=True):
        if save_config(final_config, config_path):
            print(f"\n{Colors.GREEN}╔══════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.GREEN}║       Setup Complete! ✓                      ║{Colors.NC}")
            print(f"{Colors.GREEN}╚══════════════════════════════════════════════╝{Colors.NC}")
            print(f"\n{Colors.BOLD}Next steps:{Colors.NC}")
            print(f"  1. {Colors.BLUE}Test your setup:{Colors.NC} python3 test_setup.py")
            print(f"  2. {Colors.BLUE}Train your model:{Colors.NC} cd DatasetCreation && python3 train_spell_classifier.py")
            print(f"  3. {Colors.BLUE}Run the wand tracker:{Colors.NC} python3 HarryPotterWandcv.py")
            print(f"\n{Colors.GREEN}Happy spell casting! 🪄✨{Colors.NC}\n")
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
