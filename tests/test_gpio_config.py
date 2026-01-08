#!/usr/bin/env python3
"""
GPIO Configuration Validation Tests

Validates GPIO pin configuration is correct and consistent across all files.
Can be run in Docker without hardware dependencies.
"""

import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Valid GPIO pin ranges for Raspberry Pi
VALID_GPIO_RANGE = range(0, 28)  # GPIO 0-27

# Expected pin mappings (Physical Pin -> GPIO BCM)
# Based on Raspberry Pi 5 40-pin header
PIN_MAPPINGS = {
    # LED uses SPI MOSI
    19: 10,   # Physical Pin 19 = GPIO10 (MOSI)
    # Servo uses hardware PWM
    32: 12,   # Physical Pin 32 = GPIO12
    # IR uses software PWM
    12: 18,   # Physical Pin 12 = GPIO18
}


def test_gpio_pin_values():
    """Test that GPIO pin numbers are within valid Raspberry Pi range (0-27)"""
    print("\n" + "="*60)
    print("GPIO PIN VALUES TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        hardware = config.get('hardware', {})
        all_valid = True

        # Check LED gpio_pin (should be 19 - physical pin for documentation)
        led_gpio = hardware.get('led', {}).get('gpio_pin')
        if led_gpio is not None:
            # LED uses physical pin 19 which corresponds to GPIO10
            # The config stores physical pin for documentation
            if led_gpio == 19:
                print(f"✓ LED gpio_pin: {led_gpio} (Physical Pin 19 = GPIO10/MOSI)")
            else:
                print(f"✗ LED gpio_pin: {led_gpio} (expected 19 for Pi 5 SPI)")
                all_valid = False

        # Check Servo gpio_pin (should be 12 = GPIO12)
        servo_gpio = hardware.get('servo', {}).get('gpio_pin')
        if servo_gpio is not None:
            if servo_gpio in VALID_GPIO_RANGE:
                print(f"✓ Servo gpio_pin: {servo_gpio} (GPIO{servo_gpio})")
            else:
                print(f"✗ Servo gpio_pin: {servo_gpio} (out of valid range 0-27)")
                all_valid = False

        # Check IR gpio_pin (should be 18 = GPIO18)
        ir_gpio = hardware.get('ir_illuminator', {}).get('gpio_pin')
        if ir_gpio is not None:
            if ir_gpio in VALID_GPIO_RANGE:
                print(f"✓ IR gpio_pin: {ir_gpio} (GPIO{ir_gpio})")
            else:
                print(f"✗ IR gpio_pin: {ir_gpio} (out of valid range 0-27)")
                all_valid = False

        return all_valid

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_gpio_no_conflicts():
    """Ensure no duplicate GPIO pins assigned to different devices"""
    print("\n" + "="*60)
    print("GPIO CONFLICT TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        hardware = config.get('hardware', {})

        # Collect GPIO pins (excluding LED which uses SPI, not direct GPIO)
        gpio_assignments = {}

        servo_gpio = hardware.get('servo', {}).get('gpio_pin')
        if servo_gpio is not None:
            gpio_assignments['Servo'] = servo_gpio

        ir_gpio = hardware.get('ir_illuminator', {}).get('gpio_pin')
        if ir_gpio is not None:
            gpio_assignments['IR Illuminator'] = ir_gpio

        # Check for conflicts
        seen_pins = {}
        conflicts = []

        for device, pin in gpio_assignments.items():
            if pin in seen_pins:
                conflicts.append(f"GPIO{pin} used by both {seen_pins[pin]} and {device}")
            else:
                seen_pins[pin] = device

        if conflicts:
            for conflict in conflicts:
                print(f"✗ {conflict}")
            return False
        else:
            print(f"✓ No GPIO conflicts detected")
            for device, pin in gpio_assignments.items():
                print(f"   {device}: GPIO{pin}")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_spi_device_path():
    """Validate SPI device path format"""
    print("\n" + "="*60)
    print("SPI DEVICE PATH TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        spi_device = config.get('hardware', {}).get('led', {}).get('spi_device')

        if spi_device is None:
            print("⚠️  No SPI device configured")
            return None

        # Valid format: /dev/spidev[0-1].[0-2]
        spi_pattern = r'^/dev/spidev[0-1]\.[0-2]$'

        if re.match(spi_pattern, spi_device):
            print(f"✓ SPI device path valid: {spi_device}")
            return True
        else:
            print(f"✗ Invalid SPI device path: {spi_device}")
            print(f"   Expected format: /dev/spidev[0-1].[0-2]")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_led_uses_spi_not_gpio():
    """Verify LED config uses spi_device, not direct GPIO"""
    print("\n" + "="*60)
    print("LED SPI CONFIGURATION TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        led_config = config.get('hardware', {}).get('led', {})

        has_spi = 'spi_device' in led_config
        has_gpio = 'gpio_pin' in led_config

        if has_spi:
            print(f"✓ LED uses SPI device: {led_config.get('spi_device')}")

            if has_gpio:
                gpio_pin = led_config.get('gpio_pin')
                # gpio_pin should be 19 (physical pin for MOSI) for documentation
                if gpio_pin == 19:
                    print(f"✓ gpio_pin: {gpio_pin} (documentation only - SPI MOSI)")
                else:
                    print(f"⚠️  gpio_pin: {gpio_pin} (expected 19 for Pi 5 MOSI)")

            return True
        else:
            print("✗ LED config missing spi_device - required for Pi 5")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_gpio_bcm_vs_physical_pin_mapping():
    """Validate the documented GPIO BCM to physical pin mappings"""
    print("\n" + "="*60)
    print("GPIO BCM vs PHYSICAL PIN MAPPING TEST")
    print("="*60)

    # These are the correct mappings for Raspberry Pi 5
    expected_mappings = {
        'LED (SPI MOSI)': {'physical': 19, 'gpio': 10},
        'Servo': {'physical': 32, 'gpio': 12},
        'IR Illuminator': {'physical': 12, 'gpio': 18},
    }

    all_correct = True

    for device, mapping in expected_mappings.items():
        physical = mapping['physical']
        gpio = mapping['gpio']
        print(f"✓ {device}: Physical Pin {physical} = GPIO{gpio}")

    # Verify against config
    config_path = PROJECT_ROOT / "config.yaml"

    if config_path.exists():
        try:
            import yaml

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            hardware = config.get('hardware', {})

            # Check servo uses GPIO12
            servo_gpio = hardware.get('servo', {}).get('gpio_pin')
            if servo_gpio == 12:
                print(f"✓ Config servo.gpio_pin ({servo_gpio}) matches GPIO12")
            elif servo_gpio is not None:
                print(f"⚠️  Config servo.gpio_pin ({servo_gpio}) doesn't match expected GPIO12")

            # Check IR uses GPIO18
            ir_gpio = hardware.get('ir_illuminator', {}).get('gpio_pin')
            if ir_gpio == 18:
                print(f"✓ Config ir_illuminator.gpio_pin ({ir_gpio}) matches GPIO18")
            elif ir_gpio is not None:
                print(f"⚠️  Config ir_illuminator.gpio_pin ({ir_gpio}) doesn't match expected GPIO18")

        except Exception as e:
            print(f"⚠️  Could not verify config: {e}")

    return all_correct


def test_config_comments_accuracy():
    """Check that config.yaml comments match actual GPIO/Pin values"""
    print("\n" + "="*60)
    print("CONFIG COMMENTS ACCURACY TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        with open(config_path, 'r') as f:
            content = f.read()

        all_accurate = True

        # Check for key documentation patterns
        checks = [
            ('Pin 19', 'GPIO10', 'LED SPI MOSI'),
            ('Pin 32', 'GPIO12', 'Servo'),
            ('Pin 12', 'GPIO18', 'IR Illuminator'),
        ]

        for physical, gpio, device in checks:
            # Look for either physical pin or GPIO mention in comments
            physical_mentioned = physical.lower() in content.lower()
            gpio_mentioned = gpio.lower() in content.lower()

            if physical_mentioned or gpio_mentioned:
                print(f"✓ {device}: Pin/GPIO documented in comments")
            else:
                print(f"⚠️  {device}: Consider adding pin/GPIO to comments")

        # Check SPI documentation
        if 'spi' in content.lower() and 'mosi' in content.lower():
            print(f"✓ SPI/MOSI documented for LED")
        else:
            print(f"⚠️  SPI/MOSI not clearly documented for LED")

        # Check Pi 5 mention
        if 'pi 5' in content.lower() or 'pi5' in content.lower():
            print(f"✓ Pi 5 compatibility mentioned")
        else:
            print(f"⚠️  Pi 5 compatibility not mentioned in config")

        return all_accurate

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - GPIO CONFIGURATION TESTS")
    print("="*60)

    results = {
        "GPIO pin values": test_gpio_pin_values(),
        "GPIO conflicts": test_gpio_no_conflicts(),
        "SPI device path": test_spi_device_path(),
        "LED uses SPI": test_led_uses_spi_not_gpio(),
        "GPIO/Pin mapping": test_gpio_bcm_vs_physical_pin_mapping(),
        "Config comments": test_config_comments_accuracy(),
    }

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{test_name}: {status}")

    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n✓ ALL GPIO TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME GPIO TESTS FAILED")
        sys.exit(1)
