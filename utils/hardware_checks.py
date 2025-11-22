"""
Hardware testing and validation utilities.

Functions for checking camera, SPI, GPIO availability and permissions.
Used by test_setup.py, setup_wizard.py, and config_loader.py.
"""

import subprocess
import os
from pathlib import Path
from typing import Tuple


def check_camera_available() -> Tuple[bool, str]:
    """
    Test if rpicam-hello can detect a camera.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['rpicam-hello', '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0 and 'No cameras available' not in result.stderr:
            output = result.stdout + result.stderr
            if 'Camera Module 3' in output or 'imx708' in output:
                return True, "Camera Module 3 NoIR detected"
            return True, "Camera detected"
        else:
            return False, "No camera detected - enable with sudo raspi-config"

    except subprocess.TimeoutExpired:
        return False, "Camera test timed out"
    except FileNotFoundError:
        return False, "rpicam-hello not found - install rpicam-apps"


def check_spi_device(device_path: str = '/dev/spidev0.0') -> Tuple[bool, str]:
    """
    Test SPI device existence and permissions.

    Args:
        device_path: Path to SPI device (default: /dev/spidev0.0)

    Returns:
        Tuple of (success: bool, message: str)
    """
    spi_device = Path(device_path)

    if not spi_device.exists():
        return False, f"SPI device not found: {device_path} - enable with sudo raspi-config"

    if not os.access(spi_device, os.R_OK | os.W_OK):
        return False, f"No permission for {device_path} - add user to 'spi' group and reboot"

    return True, f"SPI device accessible: {device_path}"


def check_gpio_access() -> Tuple[bool, str]:
    """
    Test GPIO device access.

    Returns:
        Tuple of (success: bool, message: str)
    """
    gpio_path = Path('/dev/gpiomem')

    if not gpio_path.exists():
        return False, "GPIO device not found"

    if not os.access(gpio_path, os.R_OK | os.W_OK):
        return False, "No GPIO permission - add user to 'gpio' group and reboot"

    return True, "GPIO device accessible"


def check_system_command(command: str) -> Tuple[bool, str]:
    """
    Test if a system command exists.

    Args:
        command: Command name to check

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return True, f"{command} found at {result.stdout.strip()}"
        else:
            return False, f"{command} not found in PATH"
    except subprocess.TimeoutExpired:
        return False, f"Timeout checking for {command}"
