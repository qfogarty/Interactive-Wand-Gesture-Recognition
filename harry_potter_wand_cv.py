import math
import random
import time
from threading import Thread, Lock

import cv2
import numpy as np
from picamera2 import Picamera2
from pygame import mixer

from utils.animations import move_servo_smoothly, spell_fade_out
from utils.audio import play_spell_sound

# Load configuration
try:
    from config_loader import get_config
    config = get_config()
    USE_CONFIG = True
except (ImportError, SystemExit):
    # Fallback to hardcoded paths if config not available
    print("WARNING: config.yaml not found, using hardcoded paths")
    USE_CONFIG = False

# === Configuration and Paths ===
if USE_CONFIG:
    PROJECT_ROOT = config.paths.project_root
    LASTFRAME_PATH = config.paths.lastframe
    MODEL_PATH = config.paths.model
else:
    # Backward compatibility fallback
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.resolve()
    LASTFRAME_PATH = PROJECT_ROOT / "lastframe.jpg"
    MODEL_PATH = PROJECT_ROOT / "new_custom_classifier.pkl"

# Initialize audio and load sound effects/music
mixer.init()
if USE_CONFIG:
    ALOHA_SOUND = mixer.Sound(str(config.paths.sounds / "Alohamora.mp3"))
    COLLO_SOUND = mixer.Sound(str(config.paths.sounds / "Colloportus.mp3"))
    BACKGROUND_TRACK = str(config.paths.sounds / "loop.mp3")
    mixer.music.set_volume(config.audio.background_volume)
else:
    ALOHA_SOUND = mixer.Sound(str(PROJECT_ROOT / "Sounds" / "Alohamora.mp3"))
    COLLO_SOUND = mixer.Sound(str(PROJECT_ROOT / "Sounds" / "Colloportus.mp3"))
    BACKGROUND_TRACK = str(PROJECT_ROOT / "Sounds" / "loop.mp3")
    mixer.music.set_volume(0.6)

mixer.music.load(BACKGROUND_TRACK)
mixer.music.play(-1)

# === Camera Initialization ===
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(1)  # Allow camera to warm up

# === Servo Setup (Optional) ===
servo = None
servo_enabled = config.hardware.servo.enabled if USE_CONFIG else False

if servo_enabled:
    try:
        from gpiozero import Servo
        from gpiozero.pins.pigpio import PiGPIOFactory

        factory = PiGPIOFactory()
        servo = Servo(
            config.hardware.servo.gpio_pin,
            pin_factory=factory,
            min_pulse_width=config.hardware.servo.min_pulse_width,
            max_pulse_width=config.hardware.servo.max_pulse_width,
            initial_value=None
        )
        servo.min()
        time.sleep(1.5)
        servo.detach()
        print("✓ Servo initialized")
    except Exception as e:
        print(f"WARNING: Servo initialization failed: {e}")
        servo = None
else:
    print("Servo disabled in config")

# === LED Strip Initialization (Optional) ===
neo = None
# Use .get() for backward compatibility with configs missing 'enabled' field
led_enabled = config.hardware.led.get('enabled', True) if USE_CONFIG else False

if led_enabled:
    try:
        from pi5neo import Pi5Neo
        if USE_CONFIG:
            neo = Pi5Neo(
                config.hardware.led.spi_device,
                config.hardware.led.count,
                config.hardware.led.timing
            )
        else:
            neo = Pi5Neo('/dev/spidev0.0', 30, 800)
        print("✓ LED strip initialized")
    except Exception as e:
        print(f"WARNING: LED initialization failed: {e}")
        neo = None
else:
    print("LED strip disabled in config")

# === Blob Detector Configuration ===
params = cv2.SimpleBlobDetector_Params()
if USE_CONFIG:
    params.minThreshold = config.detection.blob_detector.min_threshold
    params.maxThreshold = config.detection.blob_detector.max_threshold
    params.minArea = config.detection.blob_detector.min_area
    params.maxArea = config.detection.blob_detector.max_area
    params.minCircularity = config.detection.blob_detector.min_circularity
    params.minInertiaRatio = config.detection.blob_detector.min_inertia_ratio
else:
    params.minThreshold = 180
    params.maxThreshold = 255
    params.minArea = 15
    params.maxArea = 500
    params.minCircularity = 0.75
    params.minInertiaRatio = 0.3

params.filterByColor = 1
params.blobColor = 255
params.filterByArea = 1
params.filterByCircularity = 1
params.filterByInertia = 1
# Creates the configured blob detector
detector = cv2.SimpleBlobDetector_create(params)

# === Reflector Detector (Optional) ===
reflector_detector = None
if USE_CONFIG and config.detection.get('wand_type', 'led') == 'reflector':
    from utils.reflector_detector import ReflectorDetector
    reflector_detector = ReflectorDetector(config)
    reflector_detector.initialize()
    print("✓ Reflector wand mode enabled")
else:
    print("LED wand mode enabled")

# === Gesture State Management ===
class GestureState:
    """Manages wand gesture tracking state"""

    def __init__(self):
        self.last_move = 0  # 0=open, 1=closed
        self.points = []  # Points in current trace
        self.trace_started = False
        self.trace_start_time = None
        self.last_blob_time = None
        self.last_blob_position = None
        self.stillness_timer = 0
        self.status_text = "Ready..."
        self.last_valid_output_frame = None

    def reset_trace(self):
        """Reset all trace-related state"""
        self.trace_started = False
        self.trace_start_time = None
        self.last_blob_position = None
        self.stillness_timer = 0
        self.status_text = "Ready..."
        self.points.clear()

    def update_position(self, position, current_time):
        """Update blob position and timestamp"""
        self.last_blob_position = position
        self.last_blob_time = current_time

    def start_trace(self):
        """Begin gesture tracing"""
        self.trace_started = True
        self.points.clear()
        self.status_text = "Tracing..."
        print("Start Tracing!!")

    def add_trace_point(self, x, y):
        """Add point to trace if valid"""
        if not np.isnan(x) and not np.isnan(y):
            self.points.append((int(x), int(y)))

    def is_trace_too_short(self, stillness_duration_threshold):
        """Check if trace should be cancelled"""
        return len(self.points) < 10 and self.stillness_timer > (stillness_duration_threshold / 0.05)

    def is_trace_complete(self, stillness_duration_threshold):
        """Check if trace is complete"""
        return self.stillness_timer > (stillness_duration_threshold / 0.05) and len(self.points) >= 10

    def update_stillness(self, blob_movement, movement_threshold):
        """Update stillness timer based on movement"""
        if blob_movement < movement_threshold:
            self.stillness_timer += 1
        else:
            self.stillness_timer = 0


# === Global State Variables ===
lastMove = 0  # 0=open, 1=closed (still needed by threaded_predict)

# Gesture detection thresholds
if USE_CONFIG:
    presence_duration_threshold = config.detection.gesture.presence_duration
    stillness_duration_threshold = config.detection.gesture.stillness_duration
    movement_threshold = config.detection.gesture.movement_threshold
else:
    presence_duration_threshold = 0.6
    stillness_duration_threshold = 1.0
    movement_threshold = 6

# === Prediction Thread Control ===
predicting = False
prediction_lock = Lock()  # Ensures only one prediction runs at a time


def screen_flash_feedback(spell_type):
    """Flash screen border when LEDs are disabled for visual feedback."""
    if neo is not None:
        return  # LEDs handle the feedback

    # Spell colors: purple for open, blue for close
    color = (180, 60, 255) if spell_type == "open" else (70, 200, 255)

    # Create a colored frame and flash it
    for _ in range(8):
        flash_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(flash_frame, (0, 0), (640, 480), color, 15)
        cv2.putText(flash_frame, spell_type.upper(), (220, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
        cv2.imshow("Wand Tracking", flash_frame)
        cv2.waitKey(60)


# === Prediction Thread ===
# Handles image preprocessing and model inference in a thread
# Import at module level to avoid per-prediction import overhead
from harry_potter_wand_sklearn import predict_spell_from_array

def threaded_predict(mask):
    global lastMove, predicting
    bg_volume = config.audio.background_volume if USE_CONFIG else 0.6

    try:
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        _, mask = cv2.threshold(mask, 80, 255, cv2.THRESH_BINARY)
        mask = cv2.resize(mask, (28, 28), interpolation=cv2.INTER_AREA)
        mask = cv2.dilate(mask, (3, 3))

        # Use array-based prediction to skip disk I/O (saves ~10-20ms)
        prediction = str(predict_spell_from_array(mask, MODEL_PATH))
        print("Prediction:", prediction)

        if prediction == "0" and lastMove == 0:
            print("Alohamora!!")
            play_spell_sound(ALOHA_SOUND, bg_volume)
            move_servo_smoothly(neo, servo, "open")
            screen_flash_feedback("open")
            lastMove = 1
        elif prediction == "1" and lastMove == 1:
            print("Colloportus!!")
            play_spell_sound(COLLO_SOUND, bg_volume)
            move_servo_smoothly(neo, servo, "close")
            screen_flash_feedback("close")
            lastMove = 0
    finally:
        with prediction_lock:
            predicting = False

# === Main Loop ===
# Initialize gesture state
state = GestureState()

try:
    while True:
        # Read and flip camera feed
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Detect wand tip blob
        if reflector_detector:
            # Reflector mode: use advanced filtering pipeline
            position = reflector_detector.detect(gray)
            if position:
                keypoints = [cv2.KeyPoint(float(position[0]), float(position[1]), 20)]
            else:
                keypoints = []
        else:
            # LED mode: use standard blob detector
            keypoints = detector.detect(gray)

        output_frame = cv2.drawKeypoints(gray, keypoints, np.array([]), (0, 0, 255),
                                         cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        current_time = time.time()
        points_array = cv2.KeyPoint_convert(keypoints)

        if len(points_array) > 0:
            x, y = points_array[0]
            current_position = (x, y)
            blob_movement = 0
            if state.last_blob_position:
                blob_movement = math.hypot(x - state.last_blob_position[0], y - state.last_blob_position[1])

            # Start trace if wand is present and moving
            if not state.trace_started:
                if state.trace_start_time is None:
                    state.trace_start_time = current_time
                elif current_time - state.trace_start_time > presence_duration_threshold and blob_movement > movement_threshold:
                    state.start_trace()
            else:
                # Add wand path to points
                state.add_trace_point(x, y)
                for i in range(1, len(state.points)):
                    pt1 = state.points[i - 1]
                    pt2 = state.points[i]
                    if pt1 and pt2:
                        cv2.line(output_frame, pt1, pt2, (255, 255, 0), 7)
                state.last_valid_output_frame = output_frame.copy()

                # Track if wand is staying still
                state.update_stillness(blob_movement, movement_threshold)

                # Cancel short traces
                if state.is_trace_too_short(stillness_duration_threshold):
                    print("Canceled trace — likely a reflection.")
                    state.reset_trace()
                    if reflector_detector:
                        reflector_detector.reset()
                    time.sleep(0.5)
                    continue

                # Spell casting complete when still long enough
                if state.is_trace_complete(stillness_duration_threshold):
                    print("Tracing Done!!")
                    mask = cv2.inRange(state.last_valid_output_frame, np.array([255, 255, 0]), np.array([255, 255, 0]))
                    with prediction_lock:
                        if not predicting:
                            predicting = True
                            Thread(target=threaded_predict, args=(mask,)).start()
                    state.reset_trace()
                    if reflector_detector:
                        reflector_detector.reset()
                    time.sleep(1)
                    continue

            state.update_position(current_position, current_time)
        else:
            # Trigger prediction if wand leaves the frame while tracing
            if state.trace_started and state.last_blob_time and time.time() - state.last_blob_time > stillness_duration_threshold:
                print("Tracing Done (Wand Left Frame)!!")
                mask = cv2.inRange(state.last_valid_output_frame, np.array([255, 255, 0]), np.array([255, 255, 0]))
                with prediction_lock:
                    if not predicting:
                        predicting = True
                        Thread(target=threaded_predict, args=(mask,)).start()
                state.reset_trace()
                if reflector_detector:
                    reflector_detector.reset()
                time.sleep(1)
                continue
            state.trace_start_time = None

        # Draw status and visuals
        cv2.putText(output_frame, state.status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 255, 0) if state.status_text == "Ready..." else (0, 100, 255), 2)
        if state.trace_started and int(time.time() * 4) % 2 == 0:
            cv2.rectangle(output_frame, (5, 5), (635, 475), (255, 0, 0), 3)

        cv2.imshow("Wand Tracking", output_frame)
        cv2.imshow("Gray Feed", gray)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Exiting on 'q' press...")
            break

finally:
    # Cleanup on exit
    cv2.destroyAllWindows()
    if servo:
        servo.detach()
    if neo:
        neo.fill_strip(0, 0, 0)
        neo.update_strip()
    mixer.music.stop()
    print("Exited safely.")
