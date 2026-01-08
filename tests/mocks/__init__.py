"""
Hardware mock implementations for Docker testing.

These mocks allow testing of animation and hardware control logic
without requiring actual Raspberry Pi hardware or GPIO access.
"""

from .mock_pi5neo import MockPi5Neo
from .mock_gpiozero import MockServo, MockPWMOutputDevice

__all__ = ['MockPi5Neo', 'MockServo', 'MockPWMOutputDevice']
