"""
Mock gpiozero components for testing.

Provides drop-in replacements for gpiozero Servo and PWMOutputDevice
that track state without requiring actual GPIO hardware.
"""


class MockServo:
    """
    Mock implementation of gpiozero Servo.

    Tracks servo position changes for verification in tests.
    Matches the interface of gpiozero.Servo.
    """

    def __init__(self, pin: int, min_pulse_width: float = 0.0005,
                 max_pulse_width: float = 0.0025, pin_factory=None):
        """
        Initialize mock servo.

        Args:
            pin: GPIO pin number
            min_pulse_width: Minimum pulse width in seconds
            max_pulse_width: Maximum pulse width in seconds
            pin_factory: Ignored (for compatibility)
        """
        self.pin = pin
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width

        self._value = 0.0
        self.detached = False

        # Track method calls for test verification
        self.value_history = [0.0]
        self.detach_count = 0

    @property
    def value(self) -> float:
        """Get current servo position (-1 to 1)."""
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """
        Set servo position.

        Args:
            val: Position value (-1 to 1, where -1 is min, 0 is mid, 1 is max)
        """
        # Clamp to valid range
        self._value = max(-1.0, min(1.0, float(val)))
        self.value_history.append(self._value)
        self.detached = False

    def detach(self) -> None:
        """Detach servo (stop PWM signal)."""
        self.detached = True
        self.detach_count += 1

    def min(self) -> None:
        """Move to minimum position."""
        self.value = -1.0

    def mid(self) -> None:
        """Move to middle position."""
        self.value = 0.0

    def max(self) -> None:
        """Move to maximum position."""
        self.value = 1.0

    # Test helper methods

    def reset_tracking(self) -> None:
        """Reset call tracking for fresh test."""
        self.value_history = [self._value]
        self.detach_count = 0

    def get_movement_range(self) -> tuple:
        """Get min and max values reached during operation."""
        if not self.value_history:
            return (0.0, 0.0)
        return (min(self.value_history), max(self.value_history))


class MockPWMOutputDevice:
    """
    Mock implementation of gpiozero PWMOutputDevice.

    Used for IR illuminator brightness control testing.
    Matches the interface of gpiozero.PWMOutputDevice.
    """

    def __init__(self, pin: int, frequency: int = 1000,
                 initial_value: float = 0, pin_factory=None):
        """
        Initialize mock PWM device.

        Args:
            pin: GPIO pin number
            frequency: PWM frequency in Hz
            initial_value: Initial duty cycle (0-1)
            pin_factory: Ignored (for compatibility)
        """
        self.pin = pin
        self.frequency = frequency
        self._value = initial_value

        # Track changes for test verification
        self.value_history = [initial_value]
        self.on_count = 0
        self.off_count = 0

    @property
    def value(self) -> float:
        """Get current PWM value (duty cycle 0-1)."""
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """
        Set PWM value (duty cycle).

        Args:
            val: Duty cycle (0-1, where 0 is off, 1 is full brightness)
        """
        self._value = max(0.0, min(1.0, float(val)))
        self.value_history.append(self._value)

    def on(self) -> None:
        """Turn on at full brightness."""
        self.value = 1.0
        self.on_count += 1

    def off(self) -> None:
        """Turn off."""
        self.value = 0.0
        self.off_count += 1

    @property
    def is_active(self) -> bool:
        """Check if device is active (value > 0)."""
        return self._value > 0

    # Test helper methods

    def reset_tracking(self) -> None:
        """Reset call tracking for fresh test."""
        self.value_history = [self._value]
        self.on_count = 0
        self.off_count = 0


class MockPiGPIOFactory:
    """
    Mock PiGPIO pin factory for compatibility.

    The real PiGPIOFactory requires pigpiod daemon.
    This mock does nothing but satisfies import requirements.
    """

    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
