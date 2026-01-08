#!/usr/bin/env python3
"""
Hardware Mock Unit Tests

Tests that our mock implementations work correctly and can be used
to test animation logic without real hardware.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_mock_pi5neo_initialization():
    """Test MockPi5Neo initializes correctly"""
    print("\n" + "="*60)
    print("MOCK PI5NEO INITIALIZATION TEST")
    print("="*60)

    try:
        from tests.mocks import MockPi5Neo

        neo = MockPi5Neo(num_leds=30, spi_path='/dev/spidev0.0', timing=800)

        assert neo.num_leds == 30, "num_leds should be 30"
        assert neo.spi_path == '/dev/spidev0.0', "spi_path should match"
        assert neo.timing == 800, "timing should be 800"
        assert len(neo.leds) == 30, "should have 30 LEDs"
        assert all(led == (0, 0, 0) for led in neo.leds), "all LEDs should be off initially"

        print("✓ MockPi5Neo initializes with correct values")
        print(f"  num_leds: {neo.num_leds}")
        print(f"  spi_path: {neo.spi_path}")
        print(f"  timing: {neo.timing}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_pi5neo_set_led_color():
    """Test MockPi5Neo.set_led_color()"""
    print("\n" + "="*60)
    print("MOCK PI5NEO SET LED COLOR TEST")
    print("="*60)

    try:
        from tests.mocks import MockPi5Neo

        neo = MockPi5Neo(num_leds=10)

        # Set a specific LED
        neo.set_led_color(5, 255, 128, 64)

        assert neo.leds[5] == (255, 128, 64), "LED 5 should have correct color"
        assert neo.leds[0] == (0, 0, 0), "LED 0 should still be off"

        print("✓ set_led_color sets correct LED")

        # Test value clamping
        neo.set_led_color(0, 300, -50, 128)
        assert neo.leds[0] == (255, 0, 128), "Values should be clamped to 0-255"

        print("✓ Values clamped to 0-255 range")

        # Test out of bounds (should be ignored)
        neo.set_led_color(100, 255, 255, 255)  # Index out of range

        print("✓ Out of bounds index handled safely")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_pi5neo_fill_strip():
    """Test MockPi5Neo.fill_strip()"""
    print("\n" + "="*60)
    print("MOCK PI5NEO FILL STRIP TEST")
    print("="*60)

    try:
        from tests.mocks import MockPi5Neo

        neo = MockPi5Neo(num_leds=10)

        # Fill with a color
        neo.fill_strip(100, 150, 200)

        assert all(led == (100, 150, 200) for led in neo.leds), "All LEDs should have same color"

        print("✓ fill_strip sets all LEDs to same color")

        # Fill with black
        neo.fill_strip(0, 0, 0)
        assert neo.is_all_off(), "All LEDs should be off"

        print("✓ fill_strip(0,0,0) turns off all LEDs")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_pi5neo_update_tracking():
    """Test MockPi5Neo.update_strip() tracking"""
    print("\n" + "="*60)
    print("MOCK PI5NEO UPDATE TRACKING TEST")
    print("="*60)

    try:
        from tests.mocks import MockPi5Neo

        neo = MockPi5Neo(num_leds=10)

        assert neo.update_count == 0, "Update count should start at 0"

        neo.update_strip()
        neo.update_strip()
        neo.update_strip()

        assert neo.update_count == 3, "Update count should be 3"

        print(f"✓ update_strip() tracked correctly: {neo.update_count} calls")

        # Test reset
        neo.reset_tracking()
        assert neo.update_count == 0, "Reset should clear update count"

        print("✓ reset_tracking() clears counters")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_servo_movement():
    """Test MockServo position changes"""
    print("\n" + "="*60)
    print("MOCK SERVO MOVEMENT TEST")
    print("="*60)

    try:
        from tests.mocks import MockServo

        servo = MockServo(pin=12)

        assert servo.value == 0, "Initial value should be 0"

        # Move servo
        servo.value = 0.5
        assert servo.value == 0.5, "Value should be 0.5"

        servo.value = -0.75
        assert servo.value == -0.75, "Value should be -0.75"

        print("✓ Servo movement tracked correctly")

        # Test helper methods
        servo.min()
        assert servo.value == -1.0, "min() should set to -1"

        servo.max()
        assert servo.value == 1.0, "max() should set to 1"

        servo.mid()
        assert servo.value == 0.0, "mid() should set to 0"

        print("✓ Helper methods (min/mid/max) work correctly")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_servo_value_clamping():
    """Test MockServo value clamping to -1 to 1 range"""
    print("\n" + "="*60)
    print("MOCK SERVO VALUE CLAMPING TEST")
    print("="*60)

    try:
        from tests.mocks import MockServo

        servo = MockServo(pin=12)

        # Test clamping
        servo.value = 5.0
        assert servo.value == 1.0, "Value should be clamped to 1.0"

        servo.value = -10.0
        assert servo.value == -1.0, "Value should be clamped to -1.0"

        print("✓ Values clamped to -1 to 1 range")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_servo_detach():
    """Test MockServo.detach()"""
    print("\n" + "="*60)
    print("MOCK SERVO DETACH TEST")
    print("="*60)

    try:
        from tests.mocks import MockServo

        servo = MockServo(pin=12)

        assert not servo.detached, "Should not be detached initially"

        servo.detach()
        assert servo.detached, "Should be detached after detach()"
        assert servo.detach_count == 1, "Detach count should be 1"

        # Setting value should clear detached flag
        servo.value = 0.5
        assert not servo.detached, "Setting value should clear detached"

        print("✓ detach() tracked correctly")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_pwm_device():
    """Test MockPWMOutputDevice"""
    print("\n" + "="*60)
    print("MOCK PWM OUTPUT DEVICE TEST")
    print("="*60)

    try:
        from tests.mocks.mock_gpiozero import MockPWMOutputDevice

        pwm = MockPWMOutputDevice(pin=18, frequency=1000)

        assert pwm.value == 0, "Initial value should be 0"
        assert not pwm.is_active, "Should not be active initially"

        pwm.on()
        assert pwm.value == 1.0, "on() should set to 1.0"
        assert pwm.is_active, "Should be active after on()"

        pwm.off()
        assert pwm.value == 0.0, "off() should set to 0.0"
        assert not pwm.is_active, "Should not be active after off()"

        print("✓ PWMOutputDevice on/off works correctly")

        # Test value clamping
        pwm.value = 1.5
        assert pwm.value == 1.0, "Value should be clamped to 1.0"

        pwm.value = -0.5
        assert pwm.value == 0.0, "Value should be clamped to 0.0"

        print("✓ Values clamped to 0-1 range")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - HARDWARE MOCK TESTS")
    print("="*60)

    results = {
        "MockPi5Neo init": test_mock_pi5neo_initialization(),
        "MockPi5Neo set_led_color": test_mock_pi5neo_set_led_color(),
        "MockPi5Neo fill_strip": test_mock_pi5neo_fill_strip(),
        "MockPi5Neo update tracking": test_mock_pi5neo_update_tracking(),
        "MockServo movement": test_mock_servo_movement(),
        "MockServo clamping": test_mock_servo_value_clamping(),
        "MockServo detach": test_mock_servo_detach(),
        "MockPWMOutputDevice": test_mock_pwm_device(),
    }

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")

    print(f"\nSummary: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n✓ ALL MOCK TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME MOCK TESTS FAILED")
        sys.exit(1)
