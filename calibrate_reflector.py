#!/usr/bin/env python3
"""
Interactive Reflector Wand Calibrator

Adjust detection parameters in real-time while watching the camera feed.
Wave your wand in front of the camera and tune settings until detection is reliable.

Controls:
    q - Quit and save settings
    ESC - Quit without saving

    Step size modes:
        1 - Fine mode (1x step)
        2 - Normal mode (2x step)
        3 - Coarse mode (5x step)

    Detection thresholds:
        w/s - Brightness threshold (+-10)
        e/d - Min blob threshold (+-10)

    Blob size:
        r/f - Min area (+-5)
        u/j - Max area (+-50)

    Blob shape:
        i/k - Min circularity (+-0.05)
        n/b - Min inertia ratio (+-0.05)

    Background subtraction (MOG2):
        o/l - MOG2 history frames (+-30)
        ,/. - MOG2 variance threshold (+-5)

    Tracking:
        t/g - Max jump distance (+-10)
        y/h - Required frames (+-1)

    Views & Debug:
        v - Cycle debug views (Combined/FG Mask/Bright Mask/Grayscale)
        m - Toggle mask overlay on main view

    Calibration:
        a - Auto-calibrate brightness (wave wand during calibration)
        SPACE - Reset to defaults
        p - Print current settings to console
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
        'mog2_history': 120,
        'mog2_var_threshold': 25,
    }

    # Pre-allocated morphological kernel (class constant)
    _MORPH_KERNEL = np.ones((3, 3), np.uint8)

    def __init__(self):
        self.params = dict(self.DEFAULTS)
        self.camera = None
        self.bg_subtractor = None
        self.detection_history = []
        self.last_position = None
        self.consecutive_detections = 0

        # New UI state
        self.step_multiplier = 2  # 1=fine, 2=normal, 5=coarse
        self.debug_view_mode = 0  # 0=combined, 1=fg_mask, 2=bright_mask, 3=gray
        self.show_mask_overlay = False

        # Stats tracking
        self.stats = {
            'detections_total': 0,
            'detections_valid': 0,
            'fps': 0.0,
            'last_frame_time': time.time()
        }

        # Cache intermediate masks for debug views
        self._last_fg_mask = None
        self._last_bright_mask = None
        self._last_gray = None

        # Cached blob detector (recreated only when params change)
        self._blob_detector = None
        self._blob_params_hash = None

        # Pre-computed squared max_jump_distance for faster comparison
        self._max_jump_sq = self.DEFAULTS['max_jump_distance'] ** 2

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
                if 'min_inertia_ratio' in blob:
                    self.params['min_inertia_ratio'] = blob['min_inertia_ratio']

                kalman = reflector.get('kalman', {})
                if 'max_jump_distance' in kalman:
                    self.params['max_jump_distance'] = kalman['max_jump_distance']

                temporal = reflector.get('temporal', {})
                if 'required_frames' in temporal:
                    self.params['required_frames'] = temporal['required_frames']

                mog2 = reflector.get('mog2', {})
                if 'history' in mog2:
                    self.params['mog2_history'] = mog2['history']
                if 'var_threshold' in mog2:
                    self.params['mog2_var_threshold'] = mog2['var_threshold']

                # Update cached squared distance
                self._max_jump_sq = self.params['max_jump_distance'] ** 2

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
        """Initialize MOG2 background subtractor with current params."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self.params['mog2_history'],
            varThreshold=self.params['mog2_var_threshold'],
            detectShadows=False
        )

    def _get_blob_params_hash(self):
        """Get hash of current blob detector parameters for cache invalidation."""
        return (
            self.params['min_threshold'],
            self.params['min_area'],
            self.params['max_area'],
            self.params['min_circularity'],
            self.params['min_inertia_ratio']
        )

    def create_blob_detector(self):
        """Create blob detector with current parameters (cached)."""
        # Check if we can use cached detector
        current_hash = self._get_blob_params_hash()
        if self._blob_detector is not None and self._blob_params_hash == current_hash:
            return self._blob_detector

        # Create new detector
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

        self._blob_detector = cv2.SimpleBlobDetector_create(params)
        self._blob_params_hash = current_hash
        return self._blob_detector

    def detect_wand(self, frame):
        """Detect wand tip in frame. Returns all intermediate masks for debug."""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        self._last_gray = gray

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(gray)
        self._last_fg_mask = fg_mask

        # Threshold for brightness
        _, bright_mask = cv2.threshold(
            gray,
            self.params['brightness_threshold'],
            255,
            cv2.THRESH_BINARY
        )
        self._last_bright_mask = bright_mask

        # Combine masks
        combined = cv2.bitwise_and(fg_mask, bright_mask)

        # Clean up (using pre-allocated kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, self._MORPH_KERNEL)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, self._MORPH_KERNEL)

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
            self.stats['detections_total'] += 1
            if self.last_position:
                # Use squared distance to avoid expensive sqrt
                dist_sq = ((best_point[0] - self.last_position[0])**2 +
                           (best_point[1] - self.last_position[1])**2)
                if dist_sq > self._max_jump_sq:
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

        if valid_detection:
            self.stats['detections_valid'] += 1

        return gray, combined, best_point, valid_detection

    def analyze_noise_floor(self, mask):
        """Analyze noise in the detection mask."""
        noise_pixels = np.count_nonzero(mask)
        noise_percentage = (noise_pixels / mask.size) * 100
        return noise_pixels, noise_percentage

    def suggest_brightness_threshold(self, gray):
        """Suggest optimal brightness threshold based on frame analysis."""
        mean_brightness = np.mean(gray)
        max_brightness = np.max(gray)
        # Suggest threshold at 80% of max brightness
        suggested = int(max_brightness * 0.8)
        return suggested, mean_brightness, max_brightness

    def auto_calibrate(self):
        """Attempt automatic brightness calibration by analyzing wand movement."""
        print("\n>>> Auto-calibrating... Wave your wand NOW! <<<")

        brightness_samples = []
        for i in range(60):  # ~2 seconds of data
            frame = self.camera.capture_array()
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            fg_mask = self.bg_subtractor.apply(gray)

            # Find bright moving pixels
            moving_bright = cv2.bitwise_and(fg_mask, gray)
            if np.any(moving_bright > 0):
                bright_pixels = moving_bright[moving_bright > 50]
                if len(bright_pixels) > 10:
                    brightness_samples.append(np.mean(bright_pixels))

            # Show progress
            if i % 20 == 0:
                print(f"  Sampling... {i}/60")

            time.sleep(0.033)  # ~30fps

        if len(brightness_samples) > 5:
            # Set threshold to 70% of average detected brightness
            avg_brightness = np.mean(brightness_samples)
            suggested = int(avg_brightness * 0.7)
            self.params['brightness_threshold'] = max(50, min(255, suggested))
            print(f"\n  Auto-calibrated brightness_threshold: {self.params['brightness_threshold']}")
            print(f"  (based on {len(brightness_samples)} samples, avg brightness: {avg_brightness:.0f})")
        else:
            print("\n  Could not auto-calibrate - no wand movement detected")
            print("  Try waving wand more actively in front of camera")

    def draw_overlay(self, frame, gray, mask, point, valid):
        """Draw detection overlay on frame."""
        display = frame.copy()
        h, w = display.shape[:2]

        # Apply mask overlay if enabled
        if self.show_mask_overlay and mask is not None:
            mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
            mask_rgb = cv2.cvtColor(mask_colored, cv2.COLOR_BGR2RGB)
            display = cv2.addWeighted(display, 0.7, mask_rgb, 0.3, 0)

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

        # Parameter display - left column
        y_offset = 60
        params_text = [
            f"[W/S] brightness: {self.params['brightness_threshold']}",
            f"[E/D] min_thresh: {self.params['min_threshold']}",
            f"[R/F] min_area: {self.params['min_area']}",
            f"[U/J] max_area: {self.params['max_area']}",
            f"[I/K] circularity: {self.params['min_circularity']:.2f}",
            f"[N/B] inertia: {self.params['min_inertia_ratio']:.2f}",
            f"[O/L] mog2_hist: {self.params['mog2_history']}",
            f"[,/.] mog2_var: {self.params['mog2_var_threshold']}",
            f"[T/G] max_jump: {self.params['max_jump_distance']}",
            f"[Y/H] req_frames: {self.params['required_frames']}",
        ]

        for text in params_text:
            cv2.putText(display, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            y_offset += 18

        # Step mode indicator
        mode_names = {1: "FINE", 2: "NORMAL", 5: "COARSE"}
        mode_text = f"[1/2/3] Step: {mode_names.get(self.step_multiplier, '?')} ({self.step_multiplier}x)"
        cv2.putText(display, mode_text, (10, y_offset + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 255), 1)

        # Debug view indicator
        view_names = ["Combined", "FG Mask", "Bright Mask", "Grayscale"]
        view_text = f"[V] View: {view_names[self.debug_view_mode]}"
        cv2.putText(display, view_text, (10, y_offset + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 255, 180), 1)

        # Mask overlay indicator
        overlay_text = f"[M] Overlay: {'ON' if self.show_mask_overlay else 'OFF'}"
        cv2.putText(display, overlay_text, (10, y_offset + 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 180, 180), 1)

        # Instructions at bottom
        cv2.putText(display, "Q=Save | ESC=Quit | SPACE=Reset | A=Auto | P=Print",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        # Right side - stats and info
        # Consecutive detection counter
        cv2.putText(display, f"Detections: {self.consecutive_detections}/{self.params['required_frames']}",
                    (w - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # FPS
        cv2.putText(display, f"FPS: {self.stats['fps']:.1f}",
                    (w - 100, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Valid/Total stats
        cv2.putText(display, f"Valid: {self.stats['detections_valid']}",
                    (w - 100, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        cv2.putText(display, f"Total: {self.stats['detections_total']}",
                    (w - 100, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        # Noise analysis
        if mask is not None:
            noise_px, noise_pct = self.analyze_noise_floor(mask)
            noise_color = (0, 0, 255) if noise_pct > 2.0 else (0, 255, 255) if noise_pct > 0.5 else (0, 255, 0)
            cv2.putText(display, f"Noise: {noise_pct:.1f}%",
                        (w - 100, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.4, noise_color, 1)

        # Brightness suggestion
        suggested, mean_br, max_br = self.suggest_brightness_threshold(gray)
        cv2.putText(display, f"Suggested: {suggested}",
                    (w - 120, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 255), 1)
        cv2.putText(display, f"(mean:{mean_br:.0f} max:{max_br})",
                    (w - 140, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 200), 1)

        return display

    def get_debug_view(self):
        """Get the current debug view based on mode."""
        view_names = ["Combined", "FG Mask (MOG2)", "Bright Mask", "Grayscale"]
        if self.debug_view_mode == 0:
            return None, view_names[0]  # Combined mask handled in main loop
        elif self.debug_view_mode == 1:
            return self._last_fg_mask, view_names[1]
        elif self.debug_view_mode == 2:
            return self._last_bright_mask, view_names[2]
        elif self.debug_view_mode == 3:
            return self._last_gray, view_names[3]
        return None, "Unknown"

    def handle_key(self, key):
        """Handle keyboard input. Returns True to continue, False to quit."""
        if key == ord('q'):
            self.save_config()
            return False
        elif key == 27:  # ESC
            print("Quit without saving")
            return False

        # Step size modes
        elif key == ord('1'):
            self.step_multiplier = 1
            print("Fine adjustment mode (1x)")
        elif key == ord('2'):
            self.step_multiplier = 2
            print("Normal adjustment mode (2x)")
        elif key == ord('3'):
            self.step_multiplier = 5
            print("Coarse adjustment mode (5x)")

        # Brightness threshold
        elif key == ord('w'):
            self.params['brightness_threshold'] = min(255, self.params['brightness_threshold'] + 10 * self.step_multiplier)
        elif key == ord('s'):
            self.params['brightness_threshold'] = max(50, self.params['brightness_threshold'] - 10 * self.step_multiplier)

        # Min threshold
        elif key == ord('e'):
            self.params['min_threshold'] = min(200, self.params['min_threshold'] + 10 * self.step_multiplier)
        elif key == ord('d'):
            self.params['min_threshold'] = max(20, self.params['min_threshold'] - 10 * self.step_multiplier)

        # Min area
        elif key == ord('r'):
            self.params['min_area'] = min(200, self.params['min_area'] + 5 * self.step_multiplier)
        elif key == ord('f'):
            self.params['min_area'] = max(3, self.params['min_area'] - 5 * self.step_multiplier)

        # Max area (new)
        elif key == ord('u'):
            self.params['max_area'] = min(2000, self.params['max_area'] + 50 * self.step_multiplier)
        elif key == ord('j'):
            self.params['max_area'] = max(100, self.params['max_area'] - 50 * self.step_multiplier)

        # Min circularity (new)
        elif key == ord('i'):
            self.params['min_circularity'] = min(1.0, self.params['min_circularity'] + 0.05 * self.step_multiplier)
        elif key == ord('k'):
            self.params['min_circularity'] = max(0.1, self.params['min_circularity'] - 0.05 * self.step_multiplier)

        # Min inertia ratio (new)
        elif key == ord('n'):
            self.params['min_inertia_ratio'] = min(1.0, self.params['min_inertia_ratio'] + 0.05 * self.step_multiplier)
        elif key == ord('b'):
            self.params['min_inertia_ratio'] = max(0.05, self.params['min_inertia_ratio'] - 0.05 * self.step_multiplier)

        # MOG2 history (new)
        elif key == ord('o'):
            self.params['mog2_history'] = min(500, self.params['mog2_history'] + 30 * self.step_multiplier)
            self.init_bg_subtractor()  # Reinitialize with new params
        elif key == ord('l'):
            self.params['mog2_history'] = max(30, self.params['mog2_history'] - 30 * self.step_multiplier)
            self.init_bg_subtractor()

        # MOG2 variance threshold (new)
        elif key == ord(','):
            self.params['mog2_var_threshold'] = min(100, self.params['mog2_var_threshold'] + 5 * self.step_multiplier)
            self.init_bg_subtractor()
        elif key == ord('.'):
            self.params['mog2_var_threshold'] = max(5, self.params['mog2_var_threshold'] - 5 * self.step_multiplier)
            self.init_bg_subtractor()

        # Max jump distance
        elif key == ord('t'):
            self.params['max_jump_distance'] = min(500, self.params['max_jump_distance'] + 10 * self.step_multiplier)
            self._max_jump_sq = self.params['max_jump_distance'] ** 2
        elif key == ord('g'):
            self.params['max_jump_distance'] = max(20, self.params['max_jump_distance'] - 10 * self.step_multiplier)
            self._max_jump_sq = self.params['max_jump_distance'] ** 2

        # Required frames
        elif key == ord('y'):
            self.params['required_frames'] = min(15, self.params['required_frames'] + 1)
        elif key == ord('h'):
            self.params['required_frames'] = max(1, self.params['required_frames'] - 1)

        # Debug view cycling (new)
        elif key == ord('v'):
            self.debug_view_mode = (self.debug_view_mode + 1) % 4
            view_names = ["Combined", "FG Mask (MOG2)", "Brightness Mask", "Grayscale"]
            print(f"Debug view: {view_names[self.debug_view_mode]}")

        # Mask overlay toggle (new)
        elif key == ord('m'):
            self.show_mask_overlay = not self.show_mask_overlay
            print(f"Mask overlay: {'ON' if self.show_mask_overlay else 'OFF'}")

        # Auto-calibrate (new)
        elif key == ord('a'):
            self.auto_calibrate()

        # Reset
        elif key == ord(' '):
            self.params = dict(self.DEFAULTS)
            self._max_jump_sq = self.params['max_jump_distance'] ** 2
            self._blob_detector = None  # Force blob detector recreation
            self.init_bg_subtractor()  # Reinitialize MOG2 with defaults
            print("Reset to defaults")

        # Print current
        elif key == ord('p'):
            self.print_settings()

        return True

    def print_settings(self):
        """Print current settings."""
        print("\n--- Current Settings ---")
        for key, value in self.params.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
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

            # Blob detector settings
            if 'blob_detector' not in reflector:
                reflector['blob_detector'] = {}
            reflector['blob_detector']['min_threshold'] = self.params['min_threshold']
            reflector['blob_detector']['min_area'] = self.params['min_area']
            reflector['blob_detector']['max_area'] = self.params['max_area']
            reflector['blob_detector']['min_circularity'] = round(self.params['min_circularity'], 2)
            reflector['blob_detector']['min_inertia_ratio'] = round(self.params['min_inertia_ratio'], 2)

            # MOG2 settings
            if 'mog2' not in reflector:
                reflector['mog2'] = {}
            reflector['mog2']['history'] = self.params['mog2_history']
            reflector['mog2']['var_threshold'] = self.params['mog2_var_threshold']

            # Kalman settings
            if 'kalman' not in reflector:
                reflector['kalman'] = {}
            reflector['kalman']['max_jump_distance'] = self.params['max_jump_distance']

            # Temporal settings
            if 'temporal' not in reflector:
                reflector['temporal'] = {}
            reflector['temporal']['required_frames'] = self.params['required_frames']

            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            print(f"\nSettings saved to {config_path}")
            self.print_settings()

        except Exception as e:
            print(f"ERROR saving config: {e}")
            self.print_settings()
            print("Copy these settings manually to config.yaml")

    def run(self):
        """Main calibration loop."""
        print("\n" + "="*50)
        print("  Reflector Wand Calibrator (Enhanced)")
        print("="*50)
        print("\nWave your wand in front of the camera.")
        print("Adjust settings until detection is reliable.")
        print("\nTip: Press 1/2/3 to change adjustment step size")
        print("     Press V to cycle debug views")
        print("     Press A for auto-calibration\n")

        if not self.init_camera():
            return

        self.init_bg_subtractor()

        cv2.namedWindow("Calibrator", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Debug View", cv2.WINDOW_NORMAL)

        print("Starting calibration... Press Q to save and quit.\n")

        try:
            while True:
                # Calculate FPS
                now = time.time()
                self.stats['fps'] = 1.0 / (now - self.stats['last_frame_time'] + 0.001)
                self.stats['last_frame_time'] = now

                # Capture frame
                frame = self.camera.capture_array()

                # Detect wand
                gray, mask, point, valid = self.detect_wand(frame)

                # Draw overlay
                display = self.draw_overlay(frame, gray, mask, point, valid)

                # Show main window
                cv2.imshow("Calibrator", cv2.cvtColor(display, cv2.COLOR_RGB2BGR))

                # Show debug view
                debug_mask, view_name = self.get_debug_view()
                if debug_mask is None:
                    debug_mask = mask  # Default to combined mask
                cv2.setWindowTitle("Debug View", f"Debug: {view_name}")
                cv2.imshow("Debug View", debug_mask)

                # Handle input (use waitKey(30) for smoother interaction)
                key = cv2.waitKey(30) & 0xFF
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
