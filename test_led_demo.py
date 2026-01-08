#!/usr/bin/env python3
"""
LED Demo Script - Test LED animations without casting spells

Run this on your Raspberry Pi to test LED strip functionality
and preview all spell animations.

Usage:
    python3 test_led_demo.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.terminal_ui import Colors, print_header


def get_neo():
    """Initialize LED strip from config"""
    try:
        from pi5neo import Pi5Neo
        from config_loader import get_config

        config = get_config()

        # Get LED config with safe defaults
        led_config = config.hardware.get('led', {})
        enabled = led_config.get('enabled', False)
        count = led_config.get('count', 30)
        timing = led_config.get('timing', 800)
        spi_device = led_config.get('spi_device', '/dev/spidev0.0')

        if not enabled:
            print(f"{Colors.YELLOW}Warning: LEDs disabled in config.yaml{Colors.NC}")
            print(f"Set hardware.led.enabled: true to enable")
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response != 'y':
                return None

        neo = Pi5Neo(spi_device, count, timing)
        print(f"{Colors.GREEN}LED strip initialized ({count} LEDs){Colors.NC}")
        return neo

    except ImportError:
        print(f"{Colors.RED}Error: pi5neo not installed{Colors.NC}")
        print("Install with: pip3 install pi5neo")
        return None
    except PermissionError:
        print(f"{Colors.RED}Error: Permission denied for SPI device{Colors.NC}")
        print("Add user to spi group: sudo usermod -a -G spi $USER")
        print("Then reboot")
        return None
    except Exception as e:
        print(f"{Colors.RED}Error initializing LEDs: {e}{Colors.NC}")
        return None


def get_servo():
    """Initialize servo from config (optional)"""
    try:
        from config_loader import get_config
        config = get_config()

        # Get servo config with safe defaults
        servo_config = config.hardware.get('servo', {})
        enabled = servo_config.get('enabled', False)

        if not enabled:
            return None

        gpio_pin = servo_config.get('gpio_pin', 12)
        min_pulse = servo_config.get('min_pulse_width', 0.0005)
        max_pulse = servo_config.get('max_pulse_width', 0.0025)

        from gpiozero import Servo
        from gpiozero.pins.pigpio import PiGPIOFactory

        factory = PiGPIOFactory()
        servo = Servo(
            gpio_pin,
            min_pulse_width=min_pulse,
            max_pulse_width=max_pulse,
            pin_factory=factory
        )
        print(f"{Colors.GREEN}Servo initialized (GPIO {gpio_pin}){Colors.NC}")
        return servo

    except Exception as e:
        print(f"{Colors.YELLOW}Servo not available: {e}{Colors.NC}")
        return None


def test_solid_color(neo, r, g, b, name, duration=2):
    """Display a solid color"""
    print(f"Showing {name}...")
    neo.fill_strip(r, g, b)
    neo.update_strip()
    time.sleep(duration)
    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_color_wipe(neo, r, g, b, name, delay=0.05):
    """Wipe color across strip"""
    print(f"Color wipe: {name}...")
    for i in range(neo.num_leds):
        neo.set_led_color(i, r, g, b)
        neo.update_strip()
        time.sleep(delay)
    time.sleep(0.5)
    for i in range(neo.num_leds):
        neo.set_led_color(i, 0, 0, 0)
        neo.update_strip()
        time.sleep(delay)
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_bounce_wipe(neo, r, g, b, name, delay=0.03):
    """Wipe color back and forth"""
    print(f"Bounce wipe: {name}...")
    # Forward
    for i in range(neo.num_leds):
        neo.fill_strip(0, 0, 0)
        neo.set_led_color(i, r, g, b)
        if i > 0:
            neo.set_led_color(i - 1, r // 3, g // 3, b // 3)
        if i > 1:
            neo.set_led_color(i - 2, r // 6, g // 6, b // 6)
        neo.update_strip()
        time.sleep(delay)
    # Backward
    for i in range(neo.num_leds - 1, -1, -1):
        neo.fill_strip(0, 0, 0)
        neo.set_led_color(i, r, g, b)
        if i < neo.num_leds - 1:
            neo.set_led_color(i + 1, r // 3, g // 3, b // 3)
        if i < neo.num_leds - 2:
            neo.set_led_color(i + 2, r // 6, g // 6, b // 6)
        neo.update_strip()
        time.sleep(delay)
    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_theater_chase(neo, r, g, b, name, cycles=10, delay=0.08):
    """Theater chase animation"""
    import random
    print(f"Theater chase: {name}...")
    for _ in range(cycles):
        for offset in range(3):
            neo.fill_strip(0, 0, 0)
            for i in range(0, neo.num_leds, 3):
                if i + offset < neo.num_leds:
                    neo.set_led_color(i + offset, r, g, b)
            neo.update_strip()
            time.sleep(delay)
    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_sparkle(neo, r, g, b, name, duration=3):
    """Random sparkle effect"""
    import random
    print(f"Sparkle: {name} ({duration}s)...")
    start_time = time.time()

    while time.time() - start_time < duration:
        neo.fill_strip(0, 0, 0)
        # Light up random LEDs
        for _ in range(neo.num_leds // 5):
            idx = random.randint(0, neo.num_leds - 1)
            neo.set_led_color(idx, r, g, b)
        neo.update_strip()
        time.sleep(0.05)

    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_comet(neo, r, g, b, name, delay=0.02):
    """Comet with fading tail"""
    print(f"Comet: {name}...")
    tail_length = 8

    for i in range(neo.num_leds + tail_length):
        neo.fill_strip(0, 0, 0)
        for t in range(tail_length):
            idx = i - t
            if 0 <= idx < neo.num_leds:
                fade = 1.0 - (t / tail_length)
                neo.set_led_color(idx, int(r * fade), int(g * fade), int(b * fade))
        neo.update_strip()
        time.sleep(delay)

    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_rainbow(neo, duration=5):
    """Rainbow cycle animation"""
    import math
    print(f"Rainbow cycle ({duration}s)...")
    start_time = time.time()

    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        for i in range(neo.num_leds):
            # Calculate hue based on position and time
            hue = (elapsed * 50 + i * 10) % 360

            # HSV to RGB conversion (simplified)
            c = 255
            x = int(c * (1 - abs((hue / 60) % 2 - 1)))

            if hue < 60:
                r, g, b = c, x, 0
            elif hue < 120:
                r, g, b = x, c, 0
            elif hue < 180:
                r, g, b = 0, c, x
            elif hue < 240:
                r, g, b = 0, x, c
            elif hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x

            neo.set_led_color(i, r, g, b)
        neo.update_strip()
        time.sleep(0.02)

    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def test_spell_animation(neo, servo, spell_name):
    """Run actual spell animation"""
    from utils.animations import move_servo_smoothly

    print(f"\nCasting {spell_name}...")
    move_servo_smoothly(neo, servo, spell_name)
    print(f"{Colors.GREEN}Spell complete!{Colors.NC}")


def test_brightness_levels(neo):
    """Test different brightness levels"""
    print("Testing brightness levels (white)...")
    levels = [10, 25, 50, 100, 150, 200, 255]

    for level in levels:
        print(f"  Brightness: {level}/255")
        neo.fill_strip(level, level, level)
        neo.update_strip()
        time.sleep(0.8)

    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    print(f"{Colors.GREEN}Done{Colors.NC}")


def show_menu():
    """Display interactive menu"""
    print(f"""
{Colors.BOLD}LED Demo Options:{Colors.NC}

  {Colors.BLUE}Solid Colors:{Colors.NC}
    1. Red            5. Pink
    2. Green          6. Yellow
    3. Blue           7. Purple
    4. White          8. Cyan

  {Colors.BLUE}Animations:{Colors.NC}
    a. Color wipe (RGB)
    b. Bounce wipe
    c. Theater chase
    d. Sparkle
    e. Comet
    f. Rainbow cycle
    g. Brightness test

  {Colors.BLUE}Spell Effects:{Colors.NC}
    s. Alohamora (open) - Purple fire
    t. Colloportus (close) - Blue fire

  {Colors.BLUE}Other:{Colors.NC}
    0. All off
    q. Quit
""")


def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}   Interactive Wand - LED Demo{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.NC}\n")

    # Initialize hardware
    neo = get_neo()
    if neo is None:
        print(f"\n{Colors.RED}Cannot run demo without LED strip{Colors.NC}")
        sys.exit(1)

    servo = get_servo()
    if servo:
        print(f"{Colors.GREEN}Servo available for spell animations{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}Servo not available (LED-only mode){Colors.NC}")

    print(f"\n{Colors.GREEN}Ready!{Colors.NC} Use the menu to test LED effects.\n")

    try:
        while True:
            show_menu()
            choice = input(f"{Colors.BOLD}Select option: {Colors.NC}").strip().lower()

            # Solid colors
            if choice == '1':
                test_solid_color(neo, 255, 0, 0, "Red")
            elif choice == '2':
                test_solid_color(neo, 0, 255, 0, "Green")
            elif choice == '3':
                test_solid_color(neo, 0, 0, 255, "Blue")
            elif choice == '4':
                test_solid_color(neo, 255, 255, 255, "White")
            elif choice == '5':
                test_solid_color(neo, 255, 105, 180, "Pink")
            elif choice == '6':
                test_solid_color(neo, 255, 255, 0, "Yellow")
            elif choice == '7':
                test_solid_color(neo, 148, 0, 211, "Purple")
            elif choice == '8':
                test_solid_color(neo, 0, 255, 255, "Cyan")

            # Animations
            elif choice == 'a':
                test_color_wipe(neo, 255, 0, 0, "Red")
                test_color_wipe(neo, 0, 255, 0, "Green")
                test_color_wipe(neo, 0, 0, 255, "Blue")
            elif choice == 'b':
                test_bounce_wipe(neo, 255, 105, 180, "Pink")
                test_bounce_wipe(neo, 0, 255, 255, "Cyan")
            elif choice == 'c':
                test_theater_chase(neo, 255, 255, 0, "Yellow")
            elif choice == 'd':
                test_sparkle(neo, 255, 255, 255, "White")
            elif choice == 'e':
                test_comet(neo, 0, 150, 255, "Blue")
                test_comet(neo, 255, 50, 150, "Pink")
            elif choice == 'f':
                test_rainbow(neo)
            elif choice == 'g':
                test_brightness_levels(neo)

            # Spell effects
            elif choice == 's':
                test_spell_animation(neo, servo, "open")
            elif choice == 't':
                test_spell_animation(neo, servo, "close")

            # Other
            elif choice == '0':
                neo.fill_strip(0, 0, 0)
                neo.update_strip()
                print(f"{Colors.GREEN}LEDs off{Colors.NC}")
            elif choice == 'q':
                break
            else:
                print(f"{Colors.YELLOW}Invalid option{Colors.NC}")

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.NC}")

    finally:
        # Cleanup
        neo.fill_strip(0, 0, 0)
        neo.update_strip()
        if servo:
            servo.detach()
        print(f"\n{Colors.GREEN}LEDs turned off. Goodbye!{Colors.NC}")


if __name__ == "__main__":
    main()
