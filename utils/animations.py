"""
LED and servo animation utilities for spell effects.

Provides smooth animations for LED strips and servo motors
synchronized with spell casting gestures.
"""

import math
import random
import time


def lerp(a, b, t):
    """Linear interpolation between two values"""
    return a + (b - a) * t


def spell_fade_out(neo, spell):
    """
    Fade out LED animation after spell completion.

    Args:
        neo: Pi5Neo LED strip instance
        spell: Spell type ("open" or "close")
    """
    num_leds = neo.num_leds
    steps = 20

    for s in range(steps):
        fade = 1 - (s / steps)
        for i in range(num_leds):
            flicker = 0.9 + 0.2 * random.random()
            if spell == "open":
                r = int(100 * fade * flicker)
                g = int(20 * fade * flicker)
                b = int(160 * fade * flicker)
            elif spell == "close":
                r = int(30 * fade * flicker)
                g = int(100 * fade * flicker)
                b = int(255 * fade * flicker)
            else:
                r = g = b = 0
            neo.set_led_color(i, r, g, b)
        neo.update_strip()
        time.sleep(0.02)

    neo.fill_strip(0, 0, 0)
    neo.update_strip()


def move_servo_smoothly(neo, servo, target_func):
    """
    Smooth servo animation with synchronized LED effects.

    Args:
        neo: Pi5Neo LED strip instance
        servo: Servo motor instance (or None if disabled)
        target_func: Target spell ("open" or "close")
    """
    num_leds = neo.num_leds
    duration = 1.2
    servo_steps = 30
    led_refresh_delay = 0.005
    start_time = time.time()
    last_servo_step = -1

    while True:
        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1)
        fade_in = min(progress * 1.5, 1)
        beat_phase = math.sin(time.time() * 2 * math.pi * 1.2)
        brightness_scale = 0.7 + 0.3 * (0.5 + 0.5 * beat_phase)

        current_step = int(progress * servo_steps)
        if servo and current_step != last_servo_step:
            val = -1 + progress * 2 if target_func == "open" else 1 - progress * 2
            servo.value = val
            last_servo_step = current_step

        for j in range(num_leds):
            wave_phase = elapsed * 25 + j * 0.3
            wave = 0.5 + 0.5 * math.sin(wave_phase)
            flicker = 0.95 + 0.1 * math.sin(elapsed * 60 + j)

            if target_func == "open":
                r = int(lerp(100, 180, wave) * flicker * fade_in * brightness_scale)
                g = int(lerp(30, 60, wave) * flicker * fade_in * brightness_scale)
                b = int(lerp(180, 255, wave) * flicker * fade_in * brightness_scale)
            else:
                r = int(lerp(30, 70, wave) * flicker * fade_in * brightness_scale)
                g = int(lerp(100, 200, wave) * flicker * fade_in * brightness_scale)
                b = int(lerp(200, 255, wave) * flicker * fade_in * brightness_scale)

            if random.random() < 0.02:
                r, g, b = 255, 255, 255

            neo.set_led_color(j, r, g, b)

        neo.update_strip()
        time.sleep(led_refresh_delay)

        if progress >= 1:
            break

    spell_fade_out(neo, target_func)
    time.sleep(0.2)

    if servo:
        servo.detach()
