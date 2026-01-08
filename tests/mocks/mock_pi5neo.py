"""
Mock Pi5Neo LED strip for testing.

Provides a drop-in replacement for the pi5neo.Pi5Neo class
that tracks LED state without requiring actual hardware.
"""


class MockPi5Neo:
    """
    Mock implementation of Pi5Neo LED strip controller.

    Tracks all LED state changes for verification in tests.
    Matches the interface of the real pi5neo.Pi5Neo class.
    """

    def __init__(self, num_leds: int, spi_path: str = '/dev/spidev0.0', timing: int = 800):
        """
        Initialize mock LED strip.

        Args:
            num_leds: Number of LEDs in the strip
            spi_path: SPI device path (stored but not used)
            timing: LED timing in kHz (stored but not used)
        """
        self.num_leds = num_leds
        self.spi_path = spi_path
        self.timing = timing

        # Track LED state as list of (R, G, B) tuples
        self.leds = [(0, 0, 0)] * num_leds

        # Track method calls for test verification
        self.update_count = 0
        self.set_color_calls = []
        self.fill_calls = []

    def set_led_color(self, index: int, r: int, g: int, b: int) -> None:
        """
        Set the color of a specific LED.

        Args:
            index: LED index (0-based)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if 0 <= index < self.num_leds:
            # Clamp values to valid range
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))

            self.leds[index] = (r, g, b)
            self.set_color_calls.append((index, r, g, b))

    def fill_strip(self, r: int, g: int, b: int) -> None:
        """
        Fill entire strip with a single color.

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        # Clamp values to valid range
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        self.leds = [(r, g, b)] * self.num_leds
        self.fill_calls.append((r, g, b))

    def update_strip(self) -> None:
        """
        Update the LED strip (push state to hardware).

        In the mock, this just increments the update counter.
        """
        self.update_count += 1

    # Test helper methods

    def get_state(self) -> list:
        """Get a copy of current LED state."""
        return self.leds.copy()

    def get_led(self, index: int) -> tuple:
        """Get the color of a specific LED."""
        if 0 <= index < self.num_leds:
            return self.leds[index]
        return (0, 0, 0)

    def is_all_off(self) -> bool:
        """Check if all LEDs are off (black)."""
        return all(led == (0, 0, 0) for led in self.leds)

    def reset_tracking(self) -> None:
        """Reset call tracking for fresh test."""
        self.update_count = 0
        self.set_color_calls = []
        self.fill_calls = []
