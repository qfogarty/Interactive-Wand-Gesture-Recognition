"""
Reflector wand detector with advanced filtering.

Optimized for passive IR reflector wands (Universal Studios style) using:
- MOG2 background subtraction to isolate moving reflections
- Relaxed blob detection for dimmer, less circular signals
- Kalman filter for smooth tracking and outlier rejection
- Temporal validation to filter transient false positives
"""

import cv2
import numpy as np
from collections import deque
from typing import Optional, Tuple


class ReflectorDetector:
    """
    Advanced wand tip detector optimized for passive IR reflector wands.

    Performance optimizations:
    - Pre-allocated morphological kernel
    - Cached config values at initialization
    - Pre-allocated numpy buffers for Kalman filter
    - Squared distance comparison to avoid sqrt
    - Direct consecutive detection tracking
    """

    # Pre-allocated morphological kernel (class constant)
    _MORPH_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    def __init__(self, config):
        self.config = config
        self.bg_subtractor = None
        self.kalman = None
        self.blob_detector = None
        self.detection_history = deque(maxlen=10)
        self.is_tracking = False
        self.frames_since_detection = 0

        # Cached config values (set in initialize())
        self.brightness_threshold = 120
        self.max_jump_distance = 100
        self._max_jump_sq = 10000  # Squared for fast comparison
        self._required_frames = 3
        self._consecutive_detections = 0

        # Pre-allocated buffers for Kalman filter
        self._measurement_buffer = np.zeros((2, 1), dtype=np.float32)
        self._state_buffer = np.zeros((4, 1), dtype=np.float32)

    def initialize(self):
        """Initialize all detection components."""
        # Cache config values once at initialization
        cfg = self._get_reflector_config()
        self.brightness_threshold = cfg.get('brightness_threshold', 120)
        self._required_frames = cfg['temporal'].get('required_frames', 3)
        self.max_jump_distance = cfg['kalman'].get('max_jump_distance', 100)
        self._max_jump_sq = self.max_jump_distance ** 2

        self._init_mog2()
        self._init_kalman()
        self._init_blob_detector()

        print("  MOG2 background subtractor: ready")
        print("  Kalman filter: ready")
        print(f"  Blob detector (reflector params): ready")
        print(f"  Brightness threshold: {self.brightness_threshold}")

    def _get_reflector_config(self):
        """Get reflector config with defaults."""
        defaults = {
            'mog2': {
                'history': 120,
                'var_threshold': 25,
                'learning_rate': -1
            },
            'blob_detector': {
                'min_threshold': 80,
                'max_threshold': 255,
                'min_area': 10,
                'max_area': 800,
                'min_circularity': 0.4,
                'min_inertia_ratio': 0.2
            },
            'brightness_threshold': 120,  # Minimum brightness to consider as reflector
            'kalman': {
                'process_noise': 0.03,
                'measurement_noise': 0.5,
                'max_jump_distance': 100
            },
            'temporal': {
                'required_frames': 3
            }
        }

        # Try to get config values, fall back to defaults
        try:
            reflector_cfg = self.config.detection.get('reflector', {})
            # Merge with defaults
            for key in defaults:
                if key not in reflector_cfg:
                    reflector_cfg[key] = defaults[key]
                elif isinstance(defaults[key], dict):
                    # Merge nested dicts only if default is a dict
                    for subkey in defaults[key]:
                        if subkey not in reflector_cfg[key]:
                            reflector_cfg[key][subkey] = defaults[key][subkey]
            return reflector_cfg
        except (AttributeError, KeyError):
            return defaults

    def _init_mog2(self):
        """Initialize MOG2 background subtractor."""
        cfg = self._get_reflector_config()['mog2']
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=cfg.get('history', 120),
            varThreshold=cfg.get('var_threshold', 25),
            detectShadows=False
        )
        self.learning_rate = cfg.get('learning_rate', -1)
        # Convert -1 to None for OpenCV (auto mode)
        if self.learning_rate == -1:
            self.learning_rate = -1  # OpenCV uses -1 for auto

    def _init_kalman(self):
        """Initialize Kalman filter for position smoothing."""
        cfg = self._get_reflector_config()['kalman']

        # 4 state variables (x, y, dx, dy), 2 measurements (x, y)
        self.kalman = cv2.KalmanFilter(4, 2)

        # Measurement matrix - we only observe x and y
        self.kalman.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], np.float32)

        # Transition matrix - constant velocity model
        self.kalman.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], np.float32)

        # Process noise covariance
        process_noise = cfg.get('process_noise', 0.03)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise

        # Measurement noise covariance
        measurement_noise = cfg.get('measurement_noise', 0.5)
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * measurement_noise

        # Post-correction error covariance
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)

        self.max_jump_distance = cfg.get('max_jump_distance', 100)

    def _init_blob_detector(self):
        """Initialize blob detector with relaxed parameters for reflectors."""
        cfg = self._get_reflector_config()['blob_detector']

        params = cv2.SimpleBlobDetector_Params()

        # Thresholds - much lower for dim reflectors
        params.minThreshold = cfg.get('min_threshold', 80)
        params.maxThreshold = cfg.get('max_threshold', 255)
        params.thresholdStep = 10

        # Area filtering
        params.filterByArea = True
        params.minArea = cfg.get('min_area', 10)
        params.maxArea = cfg.get('max_area', 800)

        # Circularity - relaxed for irregular reflector shapes
        params.filterByCircularity = True
        params.minCircularity = cfg.get('min_circularity', 0.4)

        # Inertia - relaxed for elongated shapes
        params.filterByInertia = True
        params.minInertiaRatio = cfg.get('min_inertia_ratio', 0.2)

        # Convexity
        params.filterByConvexity = True
        params.minConvexity = 0.5

        # Color - looking for bright blobs
        params.filterByColor = True
        params.blobColor = 255

        self.blob_detector = cv2.SimpleBlobDetector_create(params)

    def detect(self, gray_frame) -> Optional[Tuple[int, int]]:
        """
        Main detection method.

        Args:
            gray_frame: Grayscale camera frame

        Returns:
            Validated wand position (x, y) or None if no confident detection
        """
        # Step 1: Apply background subtraction to isolate moving objects
        fg_mask = self.bg_subtractor.apply(gray_frame, learningRate=self.learning_rate)

        # Step 2: Create brightness mask for reflector signals (must be bright!)
        _, bright_mask = cv2.threshold(gray_frame, self.brightness_threshold, 255, cv2.THRESH_BINARY)

        # Step 3: Combine masks - must be both moving AND bright
        combined_mask = cv2.bitwise_and(fg_mask, bright_mask)

        # Step 4: Morphological cleanup to remove noise (using pre-allocated kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, self._MORPH_KERNEL)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, self._MORPH_KERNEL)

        # Step 5: Blob detection on combined mask
        keypoints = self.blob_detector.detect(combined_mask)

        # Step 6: Get best candidate (largest blob)
        raw_detection = None
        if keypoints:
            best_kp = max(keypoints, key=lambda kp: kp.size)
            raw_detection = (best_kp.pt[0], best_kp.pt[1])

        # Step 7: Apply Kalman filter for smoothing and outlier rejection
        smoothed_position = self._apply_kalman(raw_detection)

        # Step 8: Temporal validation
        validated_position = self._temporal_validate(smoothed_position)

        return validated_position

    def _apply_kalman(self, detection: Optional[Tuple[float, float]]) -> Optional[Tuple[int, int]]:
        """Apply Kalman filter for smoothing and outlier rejection."""
        # Predict next position
        prediction = self.kalman.predict()
        pred_x, pred_y = int(prediction[0]), int(prediction[1])

        if detection is not None:
            det_x, det_y = detection

            # Use squared distance to avoid expensive sqrt
            dist_sq = (det_x - pred_x)**2 + (det_y - pred_y)**2

            if not self.is_tracking:
                # First detection - initialize filter state
                self._state_buffer[0, 0] = det_x
                self._state_buffer[1, 0] = det_y
                self._state_buffer[2, 0] = 0
                self._state_buffer[3, 0] = 0
                self.kalman.statePost = self._state_buffer.copy()
                self.is_tracking = True
                self.frames_since_detection = 0
                return (int(det_x), int(det_y))

            elif dist_sq < self._max_jump_sq:
                # Valid detection within expected range - update filter (reuse buffer)
                self._measurement_buffer[0, 0] = det_x
                self._measurement_buffer[1, 0] = det_y
                corrected = self.kalman.correct(self._measurement_buffer)
                self.frames_since_detection = 0
                return (int(corrected[0]), int(corrected[1]))
            else:
                # Outlier detected - use prediction only
                self.frames_since_detection += 1
                if self.frames_since_detection < 10:
                    return (pred_x, pred_y)
        else:
            # No detection - use prediction if recently tracking
            self.frames_since_detection += 1
            if self.is_tracking and self.frames_since_detection < 10:
                return (pred_x, pred_y)

        # Lost tracking after too many missed frames
        if self.frames_since_detection >= 10:
            self.is_tracking = False

        return None

    def _temporal_validate(self, position: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Require N consecutive detections to validate."""
        # Track consecutive detections directly instead of iterating
        if position is not None:
            self._consecutive_detections += 1
        else:
            self._consecutive_detections = 0

        # Keep history for debugging/analysis purposes
        self.detection_history.append(position)

        # Only return position if we have enough consecutive detections
        if self._consecutive_detections >= self._required_frames:
            return position
        return None

    def reset(self):
        """Reset tracking state (call when trace completes)."""
        self.is_tracking = False
        self.frames_since_detection = 0
        self._consecutive_detections = 0
        self.detection_history.clear()
        # Reset Kalman state without recreating the filter object
        self._state_buffer.fill(0)
        self.kalman.statePost = self._state_buffer.copy()
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)

    def get_debug_mask(self, gray_frame) -> np.ndarray:
        """
        Generate debug visualization showing what the detector sees.

        Args:
            gray_frame: Grayscale camera frame

        Returns:
            BGR frame showing foreground mask with detected blobs
        """
        # Get foreground mask (don't update the model)
        fg_mask = self.bg_subtractor.apply(gray_frame, learningRate=0)

        # Create brightness mask
        _, bright_mask = cv2.threshold(gray_frame, 60, 255, cv2.THRESH_BINARY)

        # Combined mask
        combined_mask = cv2.bitwise_and(fg_mask, bright_mask)

        # Convert to BGR for visualization
        debug = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR)

        # Detect and draw blobs
        keypoints = self.blob_detector.detect(combined_mask)
        debug = cv2.drawKeypoints(debug, keypoints, np.array([]), (0, 255, 0),
                                  cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        return debug
