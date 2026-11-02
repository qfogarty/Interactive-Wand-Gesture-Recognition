import queue
import sys
import time
from threading import Thread, Lock

import cv2
import numpy as np
from pygame import mixer

from harry_potter_wand_sklearn import TRAIN_COMMAND, get_model, predict_spell_from_array
from utils.animations import move_servo_smoothly
from utils.audio import play_spell_sound
from utils.camera import camera_settings, open_camera
from utils.casting import (
    BUSY_OUTCOME,
    CastOutcome,
    TraceTracker,
    decide_spell,
    format_attempt,
    rejected_outcome,
    trace_to_input,
)

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
    MODEL_PATH = config.paths.model
else:
    # Backward compatibility fallback
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.resolve()
    MODEL_PATH = PROJECT_ROOT / "new_custom_classifier.pkl"

# Refuse a missing or outdated model before anything starts
try:
    get_model(MODEL_PATH)
except FileNotFoundError:
    print(f"ERROR: No trained model at {MODEL_PATH}")
    print(f"Train one with: {TRAIN_COMMAND}")
    sys.exit(1)
except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

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
camera_cfg = config.hardware.camera if USE_CONFIG else {}
picam2 = open_camera(camera_cfg)

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

# === Global State Variables ===
lastMove = 0  # 0=open, 1=closed (owned by threaded_predict)

# Gesture detection thresholds. Older configs may lack the two newer keys.
if USE_CONFIG:
    gesture_cfg = config.detection.gesture
    tracker = TraceTracker(
        presence_duration=gesture_cfg.presence_duration,
        stillness_duration=gesture_cfg.stillness_duration,
        motion_radius=gesture_cfg.get('motion_radius', 15),
        min_trace_size=gesture_cfg.get('min_trace_size', 40),
    )
else:
    tracker = TraceTracker(
        presence_duration=0.6,
        stillness_duration=1.0,
        motion_radius=15,
        min_trace_size=40,
    )

# === Prediction Thread Control ===
predicting = False
prediction_lock = Lock()  # Ensures only one prediction runs at a time

# === Outcomes ===
# (trace_end, outcome) pairs. Only the main loop reads this and draws, because
# cv2 GUI calls are not thread-safe. A trace_end of None means an extra message
# about a trace that already has its log line.
outcomes = queue.SimpleQueue()

OUTCOME_DISPLAY_SECONDS = 2.5
INSET_SCALE = 4

ATTEMPT_LOG = PROJECT_ROOT / "logs" / "attempts.jsonl"
attempt_log_warned = False


def warn_attempt_log(error):
    """Warn once: losing the log must never stop the app."""
    global attempt_log_warned
    if not attempt_log_warned:
        print(f"WARNING: Could not write {ATTEMPT_LOG}: {error}")
        attempt_log_warned = True


def log_attempt(trace_end, outcome):
    try:
        with open(ATTEMPT_LOG, "a") as f:
            f.write(format_attempt(trace_end, outcome, camera_settings(camera_cfg)) + "\n")
    except OSError as e:
        warn_attempt_log(e)


try:
    ATTEMPT_LOG.parent.mkdir(exist_ok=True)
except OSError as e:
    warn_attempt_log(e)


def draw_outcome(image, outcome):
    """Draw the message and the classifier's input on the tracking view."""
    height, width = image.shape[:2]
    position = (20, height - 20)
    cv2.putText(image, outcome.message, position, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5)
    cv2.putText(image, outcome.message, position, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    if outcome.input_image is not None:
        inset = cv2.resize(outcome.input_image, None, fx=INSET_SCALE, fy=INSET_SCALE,
                           interpolation=cv2.INTER_NEAREST)
        size = inset.shape[0]
        image[10:10 + size, width - 10 - size:width - 10] = cv2.cvtColor(inset, cv2.COLOR_GRAY2BGR)


# === Prediction Thread ===
def threaded_predict(trace_end):
    global lastMove, predicting
    bg_volume = config.audio.background_volume if USE_CONFIG else 0.6

    try:
        try:
            input_image = trace_to_input(trace_end.points)
            prediction = str(predict_spell_from_array(input_image, MODEL_PATH))
            kind, message, lastMove = decide_spell(prediction, lastMove)
        except Exception as e:
            outcomes.put((trace_end, CastOutcome("error", f"Prediction failed: {e}")))
            return

        # Queue first so the message appears as the sound starts
        outcomes.put((trace_end, CastOutcome(kind, message, input_image, prediction)))

        if kind == "spell":
            try:
                if prediction == "0":
                    play_spell_sound(ALOHA_SOUND, bg_volume)
                    move_servo_smoothly(neo, servo, "open")
                else:
                    play_spell_sound(COLLO_SOUND, bg_volume)
                    move_servo_smoothly(neo, servo, "close")
            except Exception as e:
                outcomes.put((None, CastOutcome("error", f"Spell effect failed: {e}")))
    finally:
        with prediction_lock:
            predicting = False


def handle_trace_end(trace_end):
    """Give an ended trace its one outcome, directly or through the worker."""
    global predicting

    if reflector_detector:
        reflector_detector.reset()

    rejected = rejected_outcome(trace_end)
    if rejected:
        outcomes.put((trace_end, rejected))
        return

    with prediction_lock:
        busy = predicting
        predicting = True
    if busy:
        outcomes.put((trace_end, BUSY_OUTCOME))
    else:
        Thread(target=threaded_predict, args=(trace_end,)).start()


# === Main Loop ===
shown_outcome = None
shown_until = 0

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

        # Monotonic: the Pi's wall clock can jump when NTP syncs after boot
        now = time.monotonic()
        points_array = cv2.KeyPoint_convert(keypoints)
        position = tuple(float(v) for v in points_array[0]) if len(points_array) > 0 else None

        trace_end = tracker.update(position, now)
        if trace_end:
            handle_trace_end(trace_end)

        # Draw the live trail
        trail = tracker.points
        for start, end in zip(trail, trail[1:]):
            cv2.line(output_frame, start[:2], end[:2], (255, 255, 0), 7)

        # Report every outcome the worker or the trace handler produced
        while True:
            try:
                ended_trace, outcome = outcomes.get_nowait()
            except queue.Empty:
                break
            print(outcome.message)
            if ended_trace:
                log_attempt(ended_trace, outcome)
            shown_outcome = outcome
            shown_until = now + OUTCOME_DISPLAY_SECONDS

        # Draw status and visuals
        status_text = "Tracing..." if tracker.tracing else "Ready..."
        cv2.putText(output_frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 100, 255) if tracker.tracing else (0, 255, 0), 2)
        if tracker.tracing and int(now * 4) % 2 == 0:
            height, width = output_frame.shape[:2]
            cv2.rectangle(output_frame, (5, 5), (width - 5, height - 5), (255, 0, 0), 3)
        if shown_outcome and now < shown_until:
            draw_outcome(output_frame, shown_outcome)

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
