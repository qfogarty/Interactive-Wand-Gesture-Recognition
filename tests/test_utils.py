#!/usr/bin/env python3
"""
Utils Module Tests

Tests utility modules that don't require hardware.
Can be run in Docker without hardware dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_terminal_ui():
    """Test terminal_ui module"""
    print("\n" + "="*60)
    print("TERMINAL UI TEST")
    print("="*60)

    try:
        from utils.terminal_ui import Colors, print_header, print_banner

        # Test Colors class
        assert hasattr(Colors, 'GREEN'), "Colors.GREEN missing"
        assert hasattr(Colors, 'RED'), "Colors.RED missing"
        assert hasattr(Colors, 'BLUE'), "Colors.BLUE missing"
        assert hasattr(Colors, 'NC'), "Colors.NC missing"
        print("✓ Colors class attributes present")

        # Test print_header (just check it runs)
        print("\nTesting print_header output:")
        print_header("Test Header")
        print("✓ print_header runs without errors")

        # Test print_banner
        print("\nTesting print_banner output:")
        print_banner()
        print("✓ print_banner runs without errors")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_config_builder():
    """Test config_builder module"""
    print("\n" + "="*60)
    print("CONFIG BUILDER TEST")
    print("="*60)

    try:
        from utils.config_builder import build_final_config, show_completion_message

        # Test build_final_config with sample data
        hw_config = {
            'led_count': 30,
            'led_timing': 800,
            'led_spi': '/dev/spidev0.0',
            'camera_width': 640,
            'camera_height': 480,
            'camera_exposure': 8000,
            'camera_gain': 6.0,
            'camera_brightness': -0.3,
            'servo_enabled': False,
            'servo_gpio': 12,
            'servo_min_pulse': 0.0005,
            'servo_max_pulse': 0.0025,
            'ir_enabled': False,
            'ir_gpio': 18,
            'ir_pwm_freq': 1000,
        }

        detect_config = {
            'min_threshold': 180,
            'max_threshold': 255,
            'min_area': 15,
            'max_area': 500,
            'min_circularity': 0.75,
            'min_inertia': 0.3,
            'presence_duration': 0.6,
            'stillness_duration': 1.0,
            'movement_threshold': 6,
        }

        audio_config = {
            'background_volume': 0.6,
            'spell_volume': 1.0,
        }

        config = build_final_config(hw_config, detect_config, audio_config)

        # Validate structure
        assert 'project' in config, "project section missing"
        assert 'hardware' in config, "hardware section missing"
        assert 'detection' in config, "detection section missing"
        assert 'audio' in config, "audio section missing"
        assert 'paths' in config, "paths section missing"

        print("✓ build_final_config generates valid structure")

        # Test show_completion_message (just check it runs)
        print("\nTesting show_completion_message output:")
        show_completion_message()
        print("✓ show_completion_message runs without errors")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_hardware_checks():
    """Test hardware_checks module (functions exist, won't actually check hardware)"""
    print("\n" + "="*60)
    print("HARDWARE CHECKS TEST")
    print("="*60)

    try:
        from utils.hardware_checks import (
            check_camera_available,
            check_spi_device,
            check_gpio_access,
            check_system_command
        )

        print("✓ check_camera_available imported")
        print("✓ check_spi_device imported")
        print("✓ check_gpio_access imported")
        print("✓ check_system_command imported")

        # Test that functions return tuple (bool, str)
        result = check_system_command("echo")
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should return (bool, str)"
        print("✓ check_system_command returns correct format")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - UTILS MODULE TESTS")
    print("="*60)

    results = {
        "terminal_ui": test_terminal_ui(),
        "config_builder": test_config_builder(),
        "hardware_checks": test_hardware_checks(),
    }

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    print(f"\nSummary: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
