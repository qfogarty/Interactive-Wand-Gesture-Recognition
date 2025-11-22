import time
import cv2
import numpy as np
import math
import random
from threading import Thread, Lock

from picamera2 import Picamera2
from pi5neo import Pi5Neo
from pygame import mixer

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

# === LED Strip Initialization ===
if USE_CONFIG:
    neo = Pi5Neo(
        config.hardware.led.spi_device,
        config.hardware.led.count,
        config.hardware.led.timing
    )
else:
    neo = Pi5Neo('/dev/spidev0.0', 30, 800)
num_leds = neo.num_leds

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

# === Global State Variables ===
lastMove = 0  # 0=open, 1=closed
points = []  # Points in current trace
trace_started = False
trace_start_time = None
last_blob_time = None
last_blob_position = None
stillness_timer = 0
status_text = "Ready..."

# Gesture detection thresholds
if USE_CONFIG:
    presence_duration_threshold = config.detection.gesture.presence_duration
    stillness_duration_threshold = config.detection.gesture.stillness_duration
    movement_threshold = config.detection.gesture.movement_threshold
else:
    presence_duration_threshold = 0.6
    stillness_duration_threshold = 1.0
    movement_threshold = 6

last_valid_output_frame = None  # Keeps track of last good frame

# === Prediction Thread Control ===
predicting = False
prediction_lock = Lock()  # Ensures only one prediction runs at a time

# === Helpers ===
def lerp(a, b, t):
    return a + (b - a) * t

# Light animation when a spell fades out
def spell_fade_out(spell):
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

# Smooth animation of servo and LED effects during spell

def move_servo_smoothly(target_func):
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
    spell_fade_out(target_func)
    time.sleep(0.2)
    if servo:
        servo.detach()

# Play sound with volume ducking

def play_spell_sound(sound_effect):
    bg_volume = config.audio.background_volume if USE_CONFIG else 0.6
    mixer.music.set_volume(bg_volume * 0.67)  # Duck to 67% during spell
    sound_effect.play()
    time.sleep(0.1)
    mixer.music.set_volume(bg_volume)

# Handles image preprocessing and model inference in a thread
def threaded_predict(mask):
    global lastMove, predicting
    try:
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        _, mask = cv2.threshold(mask, 80, 255, cv2.THRESH_BINARY)
        mask = cv2.resize(mask, (28, 28), interpolation=cv2.INTER_AREA)
        mask = cv2.dilate(mask, (3, 3))
        cv2.imwrite(LASTFRAME_PATH, mask)

        from HarryPotterWandsklearn import predict_spell
        prediction = str(predict_spell(LASTFRAME_PATH, MODEL_PATH))
        print("Prediction:", prediction)

        if prediction == "0" and lastMove == 0:
            print("Alohamora!!")
            play_spell_sound(ALOHA_SOUND)
            move_servo_smoothly("open")
            lastMove = 1
        elif prediction == "1" and lastMove == 1:
            print("Colloportus!!")
            play_spell_sound(COLLO_SOUND)
            move_servo_smoothly("close")
            lastMove = 0
    finally:
        with prediction_lock:
            predicting = False

# === Main Loop ===
try:
    while True:
        # Read and flip camera feed
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Detect wand tip blob
        keypoints = detector.detect(gray)
        output_frame = cv2.drawKeypoints(gray, keypoints, np.array([]), (0, 0, 255),
                                         cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        current_time = time.time()
        points_array = cv2.KeyPoint_convert(keypoints)

        if len(points_array) > 0:
            x, y = points_array[0]
            current_position = (x, y)
            blob_movement = 0
            if last_blob_position:
                blob_movement = math.hypot(x - last_blob_position[0], y - last_blob_position[1])

            # Start trace if wand is present and moving
            if not trace_started:
                if trace_start_time is None:
                    trace_start_time = current_time
                elif current_time - trace_start_time > presence_duration_threshold and blob_movement > movement_threshold:
                    trace_started = True
                    print("Start Tracing!!")
                    points.clear()
                    status_text = "Tracing..."
            else:
                # Add wand path to points
                if not np.isnan(x) and not np.isnan(y):
                    points.append((int(x), int(y)))
                for i in range(1, len(points)):
                    pt1 = points[i - 1]
                    pt2 = points[i]
                    if pt1 and pt2:
                        cv2.line(output_frame, pt1, pt2, (255, 255, 0), 7)
                last_valid_output_frame = output_frame.copy()

                # Track if wand is staying still
                if blob_movement < movement_threshold:
                    stillness_timer += 1
                else:
                    stillness_timer = 0

                # Cancel short traces
                if len(points) < 10 and stillness_timer > (stillness_duration_threshold / 0.05):
                    print("Canceled trace — likely a reflection.")
                    trace_started = False
                    trace_start_time = None
                    last_blob_position = None
                    stillness_timer = 0
                    status_text = "Canceled."
                    time.sleep(0.5)
                    continue

                # Spell casting complete when still long enough
                if stillness_timer > (stillness_duration_threshold / 0.05):
                    print("Tracing Done!!")
                    mask = cv2.inRange(last_valid_output_frame, np.array([255, 255, 0]), np.array([255, 255, 0]))
                    with prediction_lock:
                        if not predicting:
                            predicting = True
                            Thread(target=threaded_predict, args=(mask,)).start()
                    trace_started = False
                    trace_start_time = None
                    last_blob_position = None
                    stillness_timer = 0
                    status_text = "Ready..."
                    time.sleep(1)
                    continue

            last_blob_position = current_position
            last_blob_time = current_time
        else:
            # Trigger prediction if wand leaves the frame while tracing
            if trace_started and last_blob_time and time.time() - last_blob_time > stillness_duration_threshold:
                print("Tracing Done (Wand Left Frame)!!")
                mask = cv2.inRange(last_valid_output_frame, np.array([255, 255, 0]), np.array([255, 255, 0]))
                with prediction_lock:
                    if not predicting:
                        predicting = True
                        Thread(target=threaded_predict, args=(mask,)).start()
                trace_started = False
                trace_start_time = None
                last_blob_position = None
                stillness_timer = 0
                status_text = "Ready..."
                time.sleep(1)
                continue
            trace_start_time = None

        # Draw status and visuals
        cv2.putText(output_frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 255, 0) if status_text == "Ready..." else (0, 100, 255), 2)
        if trace_started and int(time.time() * 4) % 2 == 0:
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
    neo.fill_strip(0, 0, 0)
    neo.update_strip()
    mixer.music.stop()
    print("Exited safely.")
