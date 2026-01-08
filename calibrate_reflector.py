#!/usr/bin/env python3
"""
Interactive Reflector Wand Calibrator

Adjust detection parameters in real-time while watching the camera feed.
Wave your wand in front of the camera and tune settings until detection is reliable.

Controls:
    q - Quit and save settings
    ESC - Quit without saving

    Brightness threshold:
        w/s - Increase/decrease brightness_threshold

    Blob detection:
        e/d - Increase/decrease min_threshold
        r/f - Increase/decrease min_area

    Tracking:
        t/g - Increase/decrease max_jump_distance
        y/h - Increase/decrease required_frames

    Other:
        SPACE - Reset to defaults
        p - Print current settings
"""

import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class ReflectorCalibrator:
    """Interactive calibration tool for reflector wand detection."""

    # Default values
    DEFAULTS = {
        'brightness_threshold': 180,
        'min_threshold': 80,
        'min_area': 10,
        'max_area': 800,
        'min_circularity': 0.4,
        'min_inertia_ratio': 0.2,
        'max_jump_distance': 100,
        'required_frames': 3,
    }

    def __init__(self):
        self.params = dict(self.DEFAULTS)
        self.camera = None
        self.bg_subtractor = None
        self.detection_history = []
        self.last_position = None
        self.consecutive_detections = 0
        self.load_current_config()

    def load_current_config(self):
        """Load current settings from config.yaml if available."""
        try:
            import yaml
            config_path = PROJECT_ROOT / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                reflector = config.get('detection', {}).get('reflector', {})

                if 'brightness_threshold' in reflector:
                    self.params['brightness_threshold'] = reflector['brightness_threshold']

                blob = reflector.get('blob_detector', {})
                if 'min_threshold' in blob:
                    self.params['min_threshold'] = blob['min_threshold']
                if 'min_area' in blob:
                    self.params['min_area'] = blob['min_area']
                if 'max_area' in blob:
                    self.params['max_area'] = blob['max_area']
                if 'min_circularity' in blob:
                    self.params['min_circularity'] = blob['min_circularity']

                kalman = reflector.get('kalman', {})
                if 'max_jump_distance' in kalman:
                    self.params['max_jump_distance'] = kalman['max_jump_distance']

                temporal = reflector.get('temporal', {})
                if 'required_frames' in temporal:
                    self.params['required_frames'] = temporal['required_frames']

                print("Loaded current settings from config.yaml")
        except Exception as e:
            print(f"Using defaults (couldn't load config: {e})")

    def init_camera(self):
        """Initialize the Pi camera."""
        try:
            from picamera2 import Picamera2

            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()

            # Set camera controls for IR detection
            self.camera.set_controls({
                "ExposureTime": 8000,
                "AnalogueGain": 6.0,
                "Brightness": -0.3
            })

            time.sleep(0.5)  # Let camera warm up
            print("Camera initialized")
            return True

        except ImportError:
            print("ERROR: picamera2 not installed (run on Raspberry Pi)")
            return False
        except Exception as e:
            print(f"ERROR: Camera initialization failed: {e}")
            return False

    def init_bg_subtractor(self):
        """Initialize MOG2 background subtractor."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=120,
            varThreshold=25,
            detectShadows=False
        )

    def create_blob_detector(self):
        """Create blob detector with current parameters."""
        params = cv2.SimpleBlobDetector_Params()

        params.minThreshold = self.params['min_threshold']
        params.maxThreshold = 255
        params.thresholdStep = 10

        params.filterByArea = True
        params.minArea = self.params['min_area']
        params.maxArea = self.params['max_area']

        params.filterByCircularity = True
        params.minCircularity = self.params['min_circularity']

        params.filterByInertia = True
        params.minInertiaRatio = self.params['min_inertia_ratio']

        params.filterByConvexity = False
        params.filterByColor = False

        return cv2.SimpleBlobDetector_create(params)

    def detect_wand(self, frame):
        """Detect wand tip in frame."""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(gray)

        # Threshold for brightness
        _, bright_mask = cv2.threshold(
            gray,
            self.params['brightness_threshold'],
            255,
            cv2.THRESH_BINARY
        )

        # Combine masks
        combined = cv2.bitwise_and(fg_mask, bright_mask)

        # Clean up
        kernel = np.ones((3, 3), np.uint8)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        # Detect blobs
        detector = self.create_blob_detector()

        # Invert for blob detection (blobs are dark on white)
        inverted = cv2.bitwise_not(combined)
        keypoints = detector.detect(inverted)

        # Find best candidate
        best_point = None
        best_brightness = 0

        for kp in keypoints:
            x, y = int(kp.pt[0]), int(kp.pt[1])
            if 0 <= x < gray.shape[1] and 0 <= y < gray.shape[0]:
                brightness = gray[y, x]
                if brightness > best_brightness:
                    best_brightness = brightness
                    best_point = (x, y)

        # Validate with tracking
        if best_point:
            if self.last_position:
                dist = np.sqrt(
                    (best_point[0] - self.last_position[0])**2 +
                    (best_point[1] - self.last_position[1])**2
                )
                if dist > self.params['max_jump_distance']:
                    best_point = None  # Reject outlier

            if best_point:
                self.consecutive_detections += 1
                self.last_position = best_point
        else:
            self.consecutive_detections = 0

        # Check temporal validation
        valid_detection = (
            best_point is not None and
            self.consecutive_detections >= self.params['required_frames']
        )

        return gray, combined, best_point, valid_detection

    def draw_overlay(self, frame, gray, mask, point, valid):
        """Draw detection overlay on frame."""
        display = frame.copy()
        h, w = display.shape[:2]

        # Draw detection point
        if point:
            color = (0, 255, 0) if valid else (0, 255, 255)  # Green if valid, yellow if pending
            cv2.circle(display, point, 15, color, 2)
            cv2.circle(display, point, 3, color, -1)

            # Draw crosshairs
            cv2.line(display, (point[0] - 20, point[1]), (point[0] + 20, point[1]), color, 1)
            cv2.line(display, (point[0], point[1] - 20), (point[0], point[1] + 20), color, 1)

        # Status text
        status = "TRACKING" if valid else ("DETECTING..." if point else "NO DETECTION")
        status_color = (0, 255, 0) if valid else (0, 255, 255) if point else (0, 0, 255)
        cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # Parameter display
        y_offset = 60
        params_text = [
            f"[W/S] brightness: {self.params['brightness_threshold']}",
            f"[E/D] min_threshold: {self.params['min_threshold']}",
            f"[R/F] min_area: {self.params['min_area']}",
            f"[T/G] max_jump: {self.params['max_jump_distance']}",
            f"[Y/H] req_frames: {self.params['required_frames']}",
        ]

        for text in params_text:
            cv2.putText(display, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 20

        # Instructions
        cv2.putText(display, "Q=Save & Quit | ESC=Quit | SPACE=Reset", (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Consecutive detection counter
        cv2.putText(display, f"Detections: {self.consecutive_detections}/{self.params['required_frames']}",
                    (w - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        return display

    def handle_key(self, key):
        """Handle keyboard input. Returns True to continue, False to quit."""
        if key == ord('q'):
            self.save_config()
            return False
        elif key == 27:  # ESC
            print("Quit without saving")
            return False

        # Brightness threshold
        elif key == ord('w'):
            self.params['brightness_threshold'] = min(255, self.params['brightness_threshold'] + 10)
        elif key == ord('s'):
            self.params['brightness_threshold'] = max(50, self.params['brightness_threshold'] - 10)

        # Min threshold
        elif key == ord('e'):
            self.params['min_threshold'] = min(200, self.params['min_threshold'] + 10)
        elif key == ord('d'):
            self.params['min_threshold'] = max(20, self.params['min_threshold'] - 10)

        # Min area
        elif key == ord('r'):
            self.params['min_area'] = min(100, self.params['min_area'] + 5)
        elif key == ord('f'):
            self.params['min_area'] = max(1, self.params['min_area'] - 5)

        # Max jump distance
        elif key == ord('t'):
            self.params['max_jump_distance'] = min(300, self.params['max_jump_distance'] + 10)
        elif key == ord('g'):
            self.params['max_jump_distance'] = max(20, self.params['max_jump_distance'] - 10)

        # Required frames
        elif key == ord('y'):
            self.params['required_frames'] = min(10, self.params['required_frames'] + 1)
        elif key == ord('h'):
            self.params['required_frames'] = max(1, self.params['required_frames'] - 1)

        # Reset
        elif key == ord(' '):
            self.params = dict(self.DEFAULTS)
            print("Reset to defaults")

        # Print current
        elif key == ord('p'):
            self.print_settings()

        return True

    def print_settings(self):
        """Print current settings."""
        print("\n--- Current Settings ---")
        for key, value in self.params.items():
            print(f"  {key}: {value}")
        print("------------------------\n")

    def save_config(self):
        """Save calibrated settings to config.yaml."""
        try:
            import yaml
            config_path = PROJECT_ROOT / "config.yaml"

            # Read existing config
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Update reflector settings
            if 'detection' not in config:
                config['detection'] = {}

            config['detection']['wand_type'] = 'reflector'

            if 'reflector' not in config['detection']:
                config['detection']['reflector'] = {}

            reflector = config['detection']['reflector']
            reflector['brightness_threshold'] = self.params['brightness_threshold']

            if 'blob_detector' not in reflector:
                reflector['blob_detector'] = {}
            reflector['blob_detector']['min_threshold'] = self.params['min_threshold']
            reflector['blob_detector']['min_area'] = self.params['min_area']
            reflector['blob_detector']['max_area'] = self.params['max_area']
            reflector['blob_detector']['min_circularity'] = self.params['min_circularity']

            if 'kalman' not in reflector:
                reflector['kalman'] = {}
            reflector['kalman']['max_jump_distance'] = self.params['max_jump_distance']

            if 'temporal' not in reflector:
                reflector['temporal'] = {}
            reflector['temporal']['required_frames'] = self.params['required_frames']

            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            print(f"\n✓ Settings saved to {config_path}")
            self.print_settings()

        except Exception as e:
            print(f"ERROR saving config: {e}")
            self.print_settings()
            print("Copy these settings manually to config.yaml")

    def run(self):
        """Main calibration loop."""
        print("\n" + "="*50)
        print("  Reflector Wand Calibrator")
        print("="*50)
        print("\nWave your wand in front of the camera.")
        print("Adjust settings until detection is reliable.\n")

        if not self.init_camera():
            return

        self.init_bg_subtractor()

        cv2.namedWindow("Calibrator", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Detection Mask", cv2.WINDOW_NORMAL)

        print("Starting calibration... Press Q to save and quit.\n")

        try:
            while True:
                # Capture frame
                frame = self.camera.capture_array()

                # Detect wand
                gray, mask, point, valid = self.detect_wand(frame)

                # Draw overlay
                display = self.draw_overlay(frame, gray, mask, point, valid)

                # Show windows
                cv2.imshow("Calibrator", cv2.cvtColor(display, cv2.COLOR_RGB2BGR))
                cv2.imshow("Detection Mask", mask)

                # Handle input
                key = cv2.waitKey(1) & 0xFF
                if key != 255:
                    if not self.handle_key(key):
                        break

        except KeyboardInterrupt:
            print("\nInterrupted")

        finally:
            self.camera.stop()
            cv2.destroyAllWindows()
            print("Calibration ended")


def main():
    calibrator = ReflectorCalibrator()
    calibrator.run()


if __name__ == "__main__":
    main()
