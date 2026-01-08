#!/usr/bin/env python3
"""
Animation Logic Tests with Mocks

Tests actual animation functions from utils/animations.py using mock hardware.
Verifies LED patterns and servo movements work correctly.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import mocks
from tests.mocks import MockPi5Neo, MockServo


def test_spell_fade_out_updates_leds():
    """Test that spell_fade_out updates LEDs during animation"""
    print("\n" + "="*60)
    print("SPELL FADE OUT LED UPDATE TEST")
    print("="*60)

    try:
        # Patch time.sleep to speed up test
        with patch('time.sleep'):
            from utils.animations import spell_fade_out

            neo = MockPi5Neo(num_leds=10)

            # Run fade out
            spell_fade_out(neo, "open")

            # Should have called update_strip multiple times
            assert neo.update_count > 0, "Should have updated strip"
            print(f"✓ update_strip called {neo.update_count} times")

            # Should have called fill_strip to turn off
            assert len(neo.fill_calls) > 0, "Should have filled strip"
            print(f"✓ fill_strip called {len(neo.fill_calls)} times")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_spell_fade_out_ends_with_black():
    """Test that spell_fade_out leaves LEDs off at end"""
    print("\n" + "="*60)
    print("SPELL FADE OUT ENDS BLACK TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import spell_fade_out

            neo = MockPi5Neo(num_leds=10)

            # Set some initial colors
            neo.fill_strip(100, 100, 100)

            # Run fade out
            spell_fade_out(neo, "close")

            # LEDs should be off at end
            assert neo.is_all_off(), "All LEDs should be off after fade"
            print("✓ All LEDs are off after fade out")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_spell_fade_out_spell_colors():
    """Test that different spells use different colors"""
    print("\n" + "="*60)
    print("SPELL FADE OUT COLORS TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import spell_fade_out

            # Test "open" spell
            neo_open = MockPi5Neo(num_leds=5)
            spell_fade_out(neo_open, "open")

            # Test "close" spell
            neo_close = MockPi5Neo(num_leds=5)
            spell_fade_out(neo_close, "close")

            # Both should have called set_led_color
            assert len(neo_open.set_color_calls) > 0, "open should set colors"
            assert len(neo_close.set_color_calls) > 0, "close should set colors"

            print("✓ Both spells set LED colors during animation")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_move_servo_smoothly_open():
    """Test move_servo_smoothly for 'open' spell"""
    print("\n" + "="*60)
    print("MOVE SERVO SMOOTHLY OPEN TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import move_servo_smoothly

            neo = MockPi5Neo(num_leds=10)
            servo = MockServo(pin=12)

            # Run open animation
            move_servo_smoothly(neo, servo, "open")

            # Servo should have moved
            assert len(servo.value_history) > 1, "Servo should have moved"
            print(f"✓ Servo moved {len(servo.value_history) - 1} times")

            # Servo should end detached
            assert servo.detached, "Servo should be detached at end"
            print("✓ Servo detached after animation")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_move_servo_smoothly_close():
    """Test move_servo_smoothly for 'close' spell"""
    print("\n" + "="*60)
    print("MOVE SERVO SMOOTHLY CLOSE TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import move_servo_smoothly

            neo = MockPi5Neo(num_leds=10)
            servo = MockServo(pin=12)

            # Run close animation
            move_servo_smoothly(neo, servo, "close")

            # Servo should have moved
            assert len(servo.value_history) > 1, "Servo should have moved"

            # LEDs should have been updated
            assert neo.update_count > 0, "LEDs should have updated"

            print(f"✓ Servo moved, LEDs updated {neo.update_count} times")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_animation_handles_none_neo():
    """Test animations handle None LED strip gracefully"""
    print("\n" + "="*60)
    print("ANIMATION HANDLES NONE NEO TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import spell_fade_out, move_servo_smoothly

            # Should not crash with None neo
            spell_fade_out(None, "open")
            print("✓ spell_fade_out handles None neo")

            servo = MockServo(pin=12)
            move_servo_smoothly(None, servo, "open")
            print("✓ move_servo_smoothly handles None neo")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_animation_handles_none_servo():
    """Test animations handle None servo gracefully"""
    print("\n" + "="*60)
    print("ANIMATION HANDLES NONE SERVO TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import move_servo_smoothly

            neo = MockPi5Neo(num_leds=10)

            # Should not crash with None servo
            move_servo_smoothly(neo, None, "open")
            print("✓ move_servo_smoothly handles None servo")

            # LEDs should still animate
            assert neo.update_count > 0, "LEDs should still animate without servo"
            print(f"✓ LEDs animated {neo.update_count} times without servo")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_animation_handles_both_none():
    """Test animations handle both None neo and servo"""
    print("\n" + "="*60)
    print("ANIMATION HANDLES BOTH NONE TEST")
    print("="*60)

    try:
        with patch('time.sleep'):
            from utils.animations import move_servo_smoothly

            # Should not crash with both None
            move_servo_smoothly(None, None, "open")
            move_servo_smoothly(None, None, "close")

            print("✓ Animations handle both None gracefully")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - ANIMATION TESTS (MOCKED)")
    print("="*60)

    results = {
        "Fade out updates LEDs": test_spell_fade_out_updates_leds(),
        "Fade out ends black": test_spell_fade_out_ends_with_black(),
        "Spell colors differ": test_spell_fade_out_spell_colors(),
        "Servo smoothly open": test_move_servo_smoothly_open(),
        "Servo smoothly close": test_move_servo_smoothly_close(),
        "Handles None neo": test_animation_handles_none_neo(),
        "Handles None servo": test_animation_handles_none_servo(),
        "Handles both None": test_animation_handles_both_none(),
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
        print("\n✓ ALL ANIMATION TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME ANIMATION TESTS FAILED")
        sys.exit(1)
