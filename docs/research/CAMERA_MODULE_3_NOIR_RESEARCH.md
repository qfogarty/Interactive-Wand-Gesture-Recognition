# Raspberry Pi Camera Module 3 NoIR (Wide Angle) - Comprehensive Research Report

**Project:** Interactive Wand Gesture Recognition
**Hardware:** Raspberry Pi 5 with Camera Module 3 NoIR Wide Angle
**Document Type:** Project Research Plan (PRP)
**Date:** November 22, 2025
**Primary Use Case:** IR blob tracking for wand gesture recognition

---

## Table of Contents

1. [Hardware Setup](#1-hardware-setup)
2. [Software Setup](#2-software-setup)
3. [Night Vision Optimization](#3-night-vision-optimization)
4. [Integration with OpenCV](#4-integration-with-opencv)
5. [Blob Detection for IR Tracking](#5-blob-detection-for-ir-tracking)
6. [Configuration Examples](#6-configuration-examples)
7. [Best Practices](#7-best-practices)
8. [Official Documentation Links](#8-official-documentation-links)

---

## 1. Hardware Setup

### 1.1 Camera Module 3 NoIR Wide Specifications

**Sensor: Sony IMX708**
- **Resolution:** 11.9 megapixels (4608 × 2592 pixels)
- **Sensor Size:** 7.4 mm diagonal
- **Pixel Size:** 1.4 μm × 1.4 μm
- **Field of View:** 120 degrees (Wide variant)
- **Autofocus:** Phase Detection Autofocus (PDAF)
- **HDR Support:** Yes (High Dynamic Range)
- **IR Filter:** None (NoIR variant - infrared sensitive)
- **Output Format:** RAW10
- **Operating Temperature:** 0°C to 50°C

**Key Features:**
- Dynamic Defect Pixel Correction (DPC)
- QBC re-mosaic function
- Common video modes: 1080p50, 720p100, 480p120

### 1.2 Raspberry Pi 5 CSI Connection

**CRITICAL DIFFERENCES FROM PREVIOUS MODELS:**

The Raspberry Pi 5 uses a **different CSI connector** than previous Raspberry Pi models:

- **Connector Type:** 22-pin MIPI CSI socket (smaller than Pi 4's connector)
- **Cable Requirement:** Pi 5-compatible 22-pin ribbon cable (NOT the standard 15-pin cable)
- **Adapter Requirement:** If your Camera Module 3 came with a 15-pin cable, you'll need a Pi 5 camera adapter cable

**Physical Connection Steps:**

1. **POWER DOWN:** Before connecting any camera, shut down your Raspberry Pi 5 and disconnect it from power
2. **Locate CSI Port:** Pi 5 has two CSI ports - either port can be used for camera connection
3. **Open the Connector:** Gently pull the clip up on the CSI port
4. **Insert Cable with Correct Orientation:**
   - Metal contacts should face the **Ethernet connector and PoE pins**
   - Alternatively: colored portion of cable should face the micro HDMI slots
   - Gold pins should lie on the same side as the Ethernet socket
5. **Secure the Connector:** Slot the cable in as far as it will go, then push the clip down firmly
6. **Power On:** Reconnect power and boot the Pi

**Important Notes:**
- No manual configuration required - Raspberry Pi OS auto-detects Camera Module 3
- Autofocus is automatically enabled for Camera Module 3
- Both CSI ports are equivalent for single-camera setups

### 1.3 Hardware Requirements Checklist

- [ ] Raspberry Pi 5
- [ ] Camera Module 3 NoIR Wide
- [ ] Pi 5-compatible 22-pin camera cable (or adapter)
- [ ] External IR illumination (850nm or 940nm IR LEDs for night vision)
- [ ] Adequate power supply for Pi 5 (5V, 5A recommended)
- [ ] Raspberry Pi OS Bullseye or later (64-bit recommended)

---

## 2. Software Setup

### 2.1 libcamera vs Legacy Camera Stack

**IMPORTANT:** Camera Module 3 is **NOT compatible** with the legacy camera stack.

**Why libcamera?**

| Feature | libcamera (Modern) | Legacy Stack |
|---------|-------------------|--------------|
| **Camera Module 3 Support** | Yes | No |
| **Active Development** | Yes | No (frozen) |
| **Open Source** | Yes | No (proprietary Broadcom) |
| **Bug Fixes** | Ongoing | None |
| **Performance** | Comparable | Comparable |
| **Processing Location** | ARM cores | GPU (VideoCore) |
| **Python Library** | picamera2 | picamera (deprecated) |

**Key Points:**
- Raspberry Pi OS Bullseye and later contain only the libcamera-based stack
- The legacy camera stack will NOT work with Camera Module 3
- All new projects should use libcamera + picamera2
- Processing moved from GPU to ARM cores (slightly higher ARM load)

### 2.2 picamera2 Library Installation

**Installation Method (Recommended):**

```bash
# Update system first
sudo apt update
sudo apt upgrade

# Install picamera2 (with GUI dependencies)
sudo apt install -y python3-picamera2

# For minimal installation without GUI/window system components:
sudo apt install python3-picamera2 --no-install-recommends

# Verify installation
python3 -c "from picamera2 import Picamera2; print('picamera2 installed successfully')"
```

**Why use apt instead of pip?**
- Ensures compatible versions of picamera2 and underlying libcamera libraries
- Handles system dependencies automatically
- Strongly recommended by Raspberry Pi Foundation

**Pre-installation Status:**
- Pre-installed on standard Raspberry Pi OS images (Bullseye+)
- NOT pre-installed on Raspberry Pi OS Lite

**Compatibility:**
- Works on all Raspberry Pi boards (including Pi Zero)
- Requires Raspberry Pi OS Bullseye or later (32-bit or 64-bit)
- NOT supported on Buster or earlier OS versions

### 2.3 NoIR Camera Configuration Requirements

**Critical Configuration for NoIR Cameras:**

NoIR (No Infrared filter) cameras require **different tuning files** than standard cameras because:
- Auto White Balance (AWB) settings differ significantly
- Infrared sensitivity changes color balance algorithms
- Exposure metering needs adjustment for IR wavelengths

**Tuning File Locations:**

**For Raspberry Pi 5 (PISP - Pi Image Signal Processor):**
```bash
/usr/share/libcamera/ipa/rpi/pisp/imx708_noir.json          # Standard 75° NoIR
/usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json    # Wide 120° NoIR
```

**For Raspberry Pi 4 and earlier (VC4):**
```bash
/usr/share/libcamera/ipa/rpi/vc4/imx708_noir.json
/usr/share/libcamera/ipa/rpi/vc4/imx708_wide_noir.json
```

**Using Tuning Files:**

**With rpicam-apps (command line):**
```bash
# Test camera with NoIR tuning
rpicam-hello --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json

# Capture image with NoIR tuning
rpicam-still --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json -o test.jpg

# Record video with NoIR tuning
rpicam-vid --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json -t 10000 -o test.h264
```

**With picamera2 (Python):**
```python
from picamera2 import Picamera2

picam2 = Picamera2()

# Load NoIR tuning file
tuning = Picamera2.load_tuning_file("/usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json")
picam2.configure(picam2.create_preview_configuration(tuning=tuning))

picam2.start()
```

**Four Camera Module 3 Variants:**
1. Standard (75° FOV with IR filter)
2. Wide (120° FOV with IR filter)
3. NoIR (75° FOV without IR filter)
4. NoIR Wide (120° FOV without IR filter) - **Your variant**

---

## 3. Night Vision Optimization

### 3.1 Critical Understanding: NoIR is NOT Night Vision

**IMPORTANT:** The NoIR camera is NOT a night vision camera by itself.

**What NoIR Means:**
- NoIR = No Infrared filter removed
- Camera sensor is sensitive to infrared light (850-950nm)
- In darkness, the camera sees nothing without illumination
- **External IR illumination is REQUIRED for night vision**

### 3.2 IR Illumination Requirements

**LED Wavelength Selection:**

| Wavelength | Visibility to Humans | Brightness to Camera | Use Case |
|------------|---------------------|---------------------|-----------|
| **850nm** | Faint red glow visible | Brighter | Better tracking performance |
| **940nm** | Nearly invisible | Dimmer | Covert applications |

**Recommendations:**
- **For wand tracking:** 850nm provides better performance and brightness
- Mount IR LEDs on the wand tip for optimal blob detection
- Position additional IR flood lights for ambient IR if needed
- Power: 3-5 IR LEDs (850nm) typically sufficient for wand tracking

### 3.3 Low-Light Settings Optimization

**Key Parameters to Adjust:**

**Exposure Control:**
```python
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()

# Manual exposure control for IR tracking
picam2.set_controls({
    "AeEnable": False,              # Disable auto-exposure
    "ExposureTime": 10000,          # Exposure time in microseconds (10ms)
    "AnalogueGain": 8.0,            # Increase gain for low light (range: 1.0-16.0)
    "AwbEnable": False,             # Disable auto white balance
    "Brightness": 0.2,              # Adjust brightness (-1.0 to 1.0)
    "Contrast": 1.2                 # Increase contrast for blob detection
})
```

**Important Notes:**
- ExposureTime takes a few frames to settle - don't capture immediately after setting
- Higher frame rates limit maximum exposure time
- If frame rate is too high, sensor will cap exposure time accordingly

**Frame Rate Control:**
```python
# Set fixed frame rate
config = picam2.create_preview_configuration(
    main={"size": (640, 480)},
    controls={
        "FrameDurationLimits": (33333, 33333),  # 30 FPS (microseconds)
        "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.Fast
    }
)
picam2.configure(config)
```

**Frame Duration Examples:**
- 30 FPS: (33333, 33333) microseconds
- 60 FPS: (16666, 16666) microseconds
- 120 FPS: (8333, 8333) microseconds

### 3.4 Optimal Settings for IR Wand Tracking

**Recommended Configuration:**

```python
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()

# Load NoIR tuning file
tuning = Picamera2.load_tuning_file("/usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json")

# Configure for IR blob tracking
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "XRGB8888"},  # RGB format for OpenCV
    controls={
        "FrameDurationLimits": (16666, 16666),  # 60 FPS for smooth tracking
        "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.Fast
    },
    tuning=tuning
)

picam2.configure(config)

# Manual controls for consistent IR detection
picam2.set_controls({
    "AeEnable": False,           # Disable auto-exposure
    "AwbEnable": False,          # Disable auto white balance
    "ExposureTime": 8000,        # 8ms exposure (adjust based on IR brightness)
    "AnalogueGain": 6.0,         # Moderate gain
    "Brightness": -0.3,          # Underexpose to isolate IR LED
    "Contrast": 1.5,             # High contrast for better blob detection
    "Sharpness": 1.0             # Some sharpness helps edge detection
})

picam2.start()
```

**Tuning Tips:**
- **Underexpose the scene** to make the IR LED stand out as the brightest point
- Start with `ExposureTime: 5000-10000` microseconds
- Adjust `AnalogueGain` if LED is too dim (increase) or blooming (decrease)
- Use `Brightness: -0.2 to -0.5` to darken background and isolate LED
- Higher `Contrast` improves blob detection threshold effectiveness

### 3.5 HDR Mode Considerations

**HDR with NoIR at Night:**
- HDR mode + NoIR + night conditions = **poor autofocus performance**
- HDR adds latency and complexity
- **Recommendation:** Disable HDR for real-time IR tracking

```python
# Disable HDR for IR tracking
config = picam2.create_video_configuration(
    main={"size": (640, 480)},
    controls={"HdrMode": controls.HdrModeEnum.Off}
)
```

### 3.6 Wide Angle Lens Considerations

**120° Field of View Impact:**

**Advantages:**
- Larger tracking area for wand gestures
- Greater detection range
- Fewer "out of frame" events during rapid movements

**Disadvantages:**
- Barrel distortion (warping, especially at edges)
- Lower effective resolution at center
- May require distortion correction for precise gesture recognition

**Distortion Correction:**

Wide-angle lenses introduce barrel distortion that can affect gesture accuracy. OpenCV provides calibration tools:

```python
import cv2
import numpy as np

# Perform camera calibration (one-time setup)
# Use a checkerboard pattern and cv2.calibrateCamera()
# Save calibration parameters: camera_matrix, dist_coeffs

# Load saved calibration
camera_matrix = np.load('camera_matrix.npy')
dist_coeffs = np.load('dist_coeffs.npy')

# Apply undistortion to frames
frame = picam2.capture_array()
undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
```

**For Your Use Case:**
- If gestures are performed in the center 60-70% of frame, distortion correction may not be necessary
- Corner/edge distortion is most pronounced
- Consider testing first before implementing correction (adds processing overhead)

---

## 4. Integration with OpenCV

### 4.1 Basic picamera2 + OpenCV Setup

**Standard Integration Pattern:**

```python
import cv2
from picamera2 import Picamera2

# Initialize camera
picam2 = Picamera2()

# Configure for OpenCV compatibility
config = picam2.create_preview_configuration(
    main={
        "format": 'XRGB8888',    # RGB format (not BGR) for OpenCV
        "size": (640, 480)
    }
)
picam2.configure(config)
picam2.start()

# Main processing loop
while True:
    # Capture frame as numpy array
    frame = picam2.capture_array()

    # Process with OpenCV
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Display
    cv2.imshow("Camera", frame)

    # Exit on 'q' key
    if cv2.waitKey(1) == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
picam2.stop()
```

**Key Points:**
- `format: 'XRGB8888'` provides RGB order (OpenCV uses BGR by default)
- `capture_array()` returns a numpy array compatible with OpenCV
- `waitKey(1)` is necessary to update OpenCV windows (quirk of OpenCV)

### 4.2 Format Conversion Options

**RGB to BGR Conversion (if needed):**

```python
# If you need BGR format for certain OpenCV functions
frame_rgb = picam2.capture_array()
frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
```

**For IR Tracking (Grayscale):**

```python
# Capture RGB and convert to grayscale
frame = picam2.capture_array()
gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

# Or configure camera for grayscale directly (more efficient)
config = picam2.create_preview_configuration(
    main={"format": 'YUV420', "size": (640, 480)}
)
```

### 4.3 Real-Time Processing with Callbacks

**Using Request Callbacks for Frame Processing:**

```python
from picamera2 import Picamera2
import cv2

picam2 = Picamera2()

# Process frames in camera thread (runs at camera framerate)
def process_frame(request):
    # Get frame from request
    frame = request.make_array("main")

    # Your processing here
    # WARNING: Keep processing lightweight - runs in camera thread

    return

# Attach callback
picam2.pre_callback = process_frame

config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Keep running
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    picam2.stop()
```

**Callback Best Practices:**
- Callbacks run in camera thread at camera framerate
- Keep processing lightweight to avoid dropping frames
- For heavy processing, use main loop with `capture_array()`
- Don't do too much processing within request callback

### 4.4 Dual Stream Configuration

**High-Res + Low-Res for Processing:**

```python
from picamera2 import Picamera2

picam2 = Picamera2()

# Configure dual streams
config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},    # High-res for recording
    lores={"size": (640, 480), "format": "YUV420"}      # Low-res for processing
)
picam2.configure(config)
picam2.start()

while True:
    # Capture low-res stream for fast processing
    frame_lores = picam2.capture_array("lores")

    # Process low-res frame
    # ... blob detection, tracking, etc.

    # Optionally capture high-res for recording/saving
    # frame_main = picam2.capture_array("main")
```

**Benefits:**
- Process at lower resolution for speed
- Record/save at higher resolution for quality
- Reduces processing overhead significantly

---

## 5. Blob Detection for IR Tracking

### 5.1 SimpleBlobDetector Configuration

**Basic SimpleBlobDetector Setup:**

```python
import cv2
from picamera2 import Picamera2

# Initialize camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Configure SimpleBlobDetector for IR LED
params = cv2.SimpleBlobDetector_Params()

# Threshold parameters (isolate bright IR LED)
params.minThreshold = 200         # Ignore pixels below this brightness
params.maxThreshold = 255         # Keep brightest pixels
params.thresholdStep = 10

# Filter by area (adjust based on LED size at distance)
params.filterByArea = True
params.minArea = 10               # Minimum blob size (pixels)
params.maxArea = 500              # Maximum blob size (pixels)

# Filter by circularity (IR LED should be round)
params.filterByCircularity = True
params.minCircularity = 0.7       # 0 = any shape, 1 = perfect circle

# Filter by convexity
params.filterByConvexity = True
params.minConvexity = 0.8

# Filter by inertia (roundness)
params.filterByInertia = True
params.minInertiaRatio = 0.5

# Create detector
detector = cv2.SimpleBlobDetector_create(params)

# Main loop
while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Detect blobs
    keypoints = detector.detect(gray)

    # Draw detected blobs
    frame_with_blobs = cv2.drawKeypoints(
        frame, keypoints, None,
        (0, 255, 0),
        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    )

    # Extract blob positions
    for kp in keypoints:
        x, y = int(kp.pt[0]), int(kp.pt[1])
        size = int(kp.size)
        print(f"IR LED at ({x}, {y}), size: {size}")

    cv2.imshow("IR Blob Detection", frame_with_blobs)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

### 5.2 Threshold-Based Blob Detection (Alternative)

**Custom Threshold + Contour Detection:**

```python
import cv2
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Threshold to isolate bright IR LED
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

    # Optional: morphological operations to clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter and draw contours
    for contour in contours:
        area = cv2.contourArea(contour)

        # Filter by area
        if 10 < area < 500:
            # Calculate centroid
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Draw circle at blob center
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                print(f"IR LED at ({cx}, {cy})")

    cv2.imshow("Threshold Detection", frame)
    cv2.imshow("Threshold Mask", thresh)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

### 5.3 Background Subtraction for Noise Reduction

**Using MOG2 for Background Subtraction:**

```python
import cv2
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Create background subtractor
backSub = cv2.createBackgroundSubtractorMOG2(
    history=500,
    varThreshold=16,
    detectShadows=False
)

while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Apply background subtraction
    fg_mask = backSub.apply(gray)

    # Threshold to get bright moving objects (IR LED)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

    # Find contours of moving bright objects
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if 10 < area < 500:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

    cv2.imshow("Frame", frame)
    cv2.imshow("Foreground Mask", fg_mask)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

### 5.4 Kalman Filter for Tracking Smoothness

**Adding Kalman Filter for Smooth Tracking:**

```python
import cv2
import numpy as np
from picamera2 import Picamera2

# Initialize Kalman Filter
kalman = cv2.KalmanFilter(4, 2)  # 4 state variables, 2 measurements
kalman.measurementMatrix = np.array([[1, 0, 0, 0],
                                      [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0],
                                     [0, 1, 0, 1],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Blob detector
params = cv2.SimpleBlobDetector_Params()
params.minThreshold = 200
params.maxThreshold = 255
params.filterByArea = True
params.minArea = 10
params.maxArea = 500
params.filterByCircularity = True
params.minCircularity = 0.7
detector = cv2.SimpleBlobDetector_create(params)

predicted = None

while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Detect blobs
    keypoints = detector.detect(gray)

    # Kalman prediction
    prediction = kalman.predict()
    predicted = (int(prediction[0]), int(prediction[1]))

    if keypoints:
        # Use detected blob position
        kp = keypoints[0]  # Use first/brightest blob
        measured = np.array([[np.float32(kp.pt[0])], [np.float32(kp.pt[1])]])
        kalman.correct(measured)

        # Draw detected position
        cv2.circle(frame, (int(kp.pt[0]), int(kp.pt[1])), 5, (0, 255, 0), -1)

    # Draw predicted position
    if predicted:
        cv2.circle(frame, predicted, 3, (255, 0, 0), -1)

    cv2.imshow("Kalman Tracking", frame)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

### 5.5 Multi-LED Tracking

**Tracking Multiple IR LEDs:**

```python
import cv2
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Blob detector configured for multiple LEDs
params = cv2.SimpleBlobDetector_Params()
params.minThreshold = 200
params.maxThreshold = 255
params.filterByArea = True
params.minArea = 10
params.maxArea = 500
detector = cv2.SimpleBlobDetector_create(params)

# Store LED trail for gesture recognition
led_trail = []
max_trail_length = 50

while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Detect all blobs
    keypoints = detector.detect(gray)

    # Draw all detected LEDs
    for kp in keypoints:
        x, y = int(kp.pt[0]), int(kp.pt[1])
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        # Add to trail (use brightest/largest for primary wand)
        if len(keypoints) > 0:
            led_trail.append((x, y))

    # Limit trail length
    if len(led_trail) > max_trail_length:
        led_trail.pop(0)

    # Draw trail
    for i in range(1, len(led_trail)):
        cv2.line(frame, led_trail[i-1], led_trail[i], (255, 0, 255), 2)

    cv2.imshow("Multi-LED Tracking", frame)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

---

## 6. Configuration Examples

### 6.1 Complete IR Wand Tracking Setup

**Production-Ready Configuration:**

```python
#!/usr/bin/env python3
"""
IR Wand Tracking with Camera Module 3 NoIR Wide
Optimized for Raspberry Pi 5
"""

import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
import time

class IRWandTracker:
    def __init__(self):
        self.picam2 = Picamera2()
        self.setup_camera()
        self.setup_blob_detector()
        self.trail = []
        self.max_trail_length = 100

    def setup_camera(self):
        """Configure Camera Module 3 NoIR Wide for IR tracking"""

        # Load NoIR tuning file for Pi 5
        tuning = Picamera2.load_tuning_file(
            "/usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json"
        )

        # Configure camera for real-time processing
        config = self.picam2.create_video_configuration(
            main={
                "size": (640, 480),
                "format": "XRGB8888"
            },
            controls={
                "FrameDurationLimits": (16666, 16666),  # 60 FPS
                "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.Fast
            },
            tuning=tuning
        )

        self.picam2.configure(config)

        # Manual exposure and gain for consistent IR detection
        self.picam2.set_controls({
            "AeEnable": False,              # Disable auto-exposure
            "AwbEnable": False,             # Disable auto white balance
            "ExposureTime": 8000,           # 8ms exposure
            "AnalogueGain": 6.0,            # Moderate gain
            "Brightness": -0.3,             # Underexpose background
            "Contrast": 1.5,                # High contrast
            "Sharpness": 1.0,               # Edge enhancement
            "HdrMode": controls.HdrModeEnum.Off
        })

        self.picam2.start()
        time.sleep(2)  # Allow camera to stabilize

    def setup_blob_detector(self):
        """Configure SimpleBlobDetector for IR LED"""
        params = cv2.SimpleBlobDetector_Params()

        # Threshold for bright IR LED
        params.minThreshold = 200
        params.maxThreshold = 255
        params.thresholdStep = 10

        # Area filtering (adjust based on LED distance)
        params.filterByArea = True
        params.minArea = 10
        params.maxArea = 500

        # Circularity filtering (LED should be round)
        params.filterByCircularity = True
        params.minCircularity = 0.7

        # Convexity filtering
        params.filterByConvexity = True
        params.minConvexity = 0.8

        # Inertia filtering (roundness)
        params.filterByInertia = True
        params.minInertiaRatio = 0.5

        self.detector = cv2.SimpleBlobDetector_create(params)

    def detect_wand(self, frame):
        """Detect IR LED wand position"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        keypoints = self.detector.detect(gray)

        if keypoints:
            # Use brightest/largest blob
            kp = max(keypoints, key=lambda k: k.size)
            x, y = int(kp.pt[0]), int(kp.pt[1])
            return (x, y)
        return None

    def update_trail(self, position):
        """Update wand position trail"""
        if position:
            self.trail.append(position)
            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)

    def draw_trail(self, frame):
        """Draw wand movement trail"""
        for i in range(1, len(self.trail)):
            cv2.line(frame, self.trail[i-1], self.trail[i],
                    (255, 0, 255), 2)

    def run(self):
        """Main tracking loop"""
        print("IR Wand Tracker Running...")
        print("Press 'q' to quit, 'c' to clear trail")

        try:
            while True:
                # Capture frame
                frame = self.picam2.capture_array()

                # Detect wand
                position = self.detect_wand(frame)

                # Update trail
                self.update_trail(position)

                # Draw visualization
                if position:
                    cv2.circle(frame, position, 10, (0, 255, 0), -1)
                self.draw_trail(frame)

                # Display
                cv2.imshow("IR Wand Tracking", frame)

                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.trail.clear()
                    print("Trail cleared")

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.picam2.stop()
        cv2.destroyAllWindows()
        print("Tracking stopped")

if __name__ == "__main__":
    tracker = IRWandTracker()
    tracker.run()
```

### 6.2 Performance Monitoring Configuration

**Track FPS and Processing Time:**

```python
import cv2
from picamera2 import Picamera2
import time

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# FPS tracking
fps_start_time = time.time()
fps_frame_count = 0
fps = 0

while True:
    loop_start = time.time()

    # Capture
    frame = picam2.capture_array()

    # Process
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # ... your processing here ...

    # Calculate FPS
    fps_frame_count += 1
    if fps_frame_count >= 30:
        fps_end_time = time.time()
        fps = fps_frame_count / (fps_end_time - fps_start_time)
        fps_start_time = fps_end_time
        fps_frame_count = 0

    # Calculate loop time
    loop_time = (time.time() - loop_start) * 1000  # ms

    # Display stats
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Loop: {loop_time:.1f}ms", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Performance Monitor", frame)

    if cv2.waitKey(1) == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

### 6.3 Camera Adjustment Script

**Test Different Exposure/Gain Settings:**

```python
import cv2
from picamera2 import Picamera2
import time

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "XRGB8888"}
)
picam2.configure(config)
picam2.start()

# Initial settings
exposure_time = 8000  # microseconds
gain = 6.0
brightness = -0.3
contrast = 1.5

def apply_settings():
    picam2.set_controls({
        "AeEnable": False,
        "AwbEnable": False,
        "ExposureTime": exposure_time,
        "AnalogueGain": gain,
        "Brightness": brightness,
        "Contrast": contrast
    })
    time.sleep(0.5)  # Wait for settings to take effect

apply_settings()

print("Camera Adjustment Tool")
print("Controls:")
print("  e/E: Decrease/Increase Exposure")
print("  g/G: Decrease/Increase Gain")
print("  b/B: Decrease/Increase Brightness")
print("  c/C: Decrease/Increase Contrast")
print("  p: Print current settings")
print("  q: Quit")

while True:
    frame = picam2.capture_array()

    # Display current settings
    cv2.putText(frame, f"Exposure: {exposure_time}us", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Gain: {gain:.1f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Brightness: {brightness:.2f}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Contrast: {contrast:.2f}", (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Camera Adjustment", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('e'):
        exposure_time = max(1000, exposure_time - 1000)
        apply_settings()
    elif key == ord('E'):
        exposure_time = min(30000, exposure_time + 1000)
        apply_settings()
    elif key == ord('g'):
        gain = max(1.0, gain - 0.5)
        apply_settings()
    elif key == ord('G'):
        gain = min(16.0, gain + 0.5)
        apply_settings()
    elif key == ord('b'):
        brightness = max(-1.0, brightness - 0.1)
        apply_settings()
    elif key == ord('B'):
        brightness = min(1.0, brightness + 0.1)
        apply_settings()
    elif key == ord('c'):
        contrast = max(0.0, contrast - 0.1)
        apply_settings()
    elif key == ord('C'):
        contrast = min(2.0, contrast + 0.1)
        apply_settings()
    elif key == ord('p'):
        print(f"\nCurrent Settings:")
        print(f"  ExposureTime: {exposure_time}")
        print(f"  AnalogueGain: {gain}")
        print(f"  Brightness: {brightness}")
        print(f"  Contrast: {contrast}")

picam2.stop()
cv2.destroyAllWindows()
```

---

## 7. Best Practices

### 7.1 Performance Optimization

**Frame Processing Strategies:**

1. **Use Lower Resolution for Processing**
   ```python
   # Configure dual streams
   config = picam2.create_video_configuration(
       main={"size": (1920, 1080)},    # Recording
       lores={"size": (320, 240)}       # Processing (4x faster)
   )
   ```

2. **Minimize Processing Per Frame**
   - Process every Nth frame for expensive operations
   - Use frame-skipping for non-critical detection
   - Cache results when possible

3. **Optimize OpenCV Operations**
   - Use `cv2.UMat` for GPU acceleration (if available)
   - Limit region of interest (ROI) for processing
   - Use lookup tables (LUT) for repetitive operations

4. **Threading Strategies**
   ```python
   import threading
   from queue import Queue

   frame_queue = Queue(maxsize=2)

   def capture_thread():
       while running:
           frame = picam2.capture_array()
           if not frame_queue.full():
               frame_queue.put(frame)

   def process_thread():
       while running:
           if not frame_queue.empty():
               frame = frame_queue.get()
               # Process frame
   ```

5. **Disable Unnecessary Features**
   - Turn off preview if not needed
   - Disable auto-focus after initial focus
   - Minimize window updates

**Performance Targets:**
- 60 FPS: Smooth real-time tracking
- 30 FPS: Acceptable for gesture recognition
- <30 FPS: Consider optimization

### 7.2 Camera Configuration Best Practices

**Startup Sequence:**

```python
# 1. Initialize
picam2 = Picamera2()

# 2. Load tuning file (if NoIR)
tuning = Picamera2.load_tuning_file("path/to/tuning.json")

# 3. Configure
config = picam2.create_video_configuration(tuning=tuning)
picam2.configure(config)

# 4. Start
picam2.start()

# 5. Wait for stabilization
time.sleep(2)

# 6. Set manual controls (after start)
picam2.set_controls({...})

# 7. Wait for controls to take effect
time.sleep(0.5)

# 8. Begin processing
```

**Control Update Timing:**
- Set controls AFTER `picam2.start()`
- Wait 2-5 frames for exposure changes to settle
- Don't change controls every frame (causes instability)

### 7.3 IR LED Optimization

**Wand LED Configuration:**

1. **LED Selection:**
   - Use 850nm IR LEDs for better camera response
   - Power: 100-150mW per LED sufficient
   - Viewing angle: 15-30° for directional brightness

2. **LED Placement:**
   - Mount at wand tip for clear tracking point
   - Use diffuser for larger, more visible blob
   - Consider multiple LEDs for redundancy

3. **Power Considerations:**
   - Use constant current driver for stable brightness
   - Battery: 3.7V Li-Ion with current limiting resistor
   - Avoid PWM dimming (creates flickering in camera)

4. **Testing LED Visibility:**
   ```python
   # Capture frame
   frame = picam2.capture_array()
   gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

   # Check max brightness
   max_val = np.max(gray)
   print(f"Max brightness: {max_val}")

   # Goal: max_val > 240 for reliable detection
   # Adjust exposure/gain or LED power accordingly
   ```

### 7.4 Error Handling and Recovery

**Robust Camera Initialization:**

```python
def initialize_camera(max_retries=3):
    for attempt in range(max_retries):
        try:
            picam2 = Picamera2()
            config = picam2.create_video_configuration(
                main={"size": (640, 480), "format": "XRGB8888"}
            )
            picam2.configure(config)
            picam2.start()
            time.sleep(2)

            # Test capture
            frame = picam2.capture_array()
            if frame is not None:
                print("Camera initialized successfully")
                return picam2

        except Exception as e:
            print(f"Camera init attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise RuntimeError("Failed to initialize camera")

    return None
```

**Frame Capture Error Handling:**

```python
def safe_capture(picam2, timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            frame = picam2.capture_array()
            if frame is not None and frame.size > 0:
                return frame
        except Exception as e:
            print(f"Capture error: {e}")
            time.sleep(0.1)

    raise TimeoutError("Frame capture timeout")
```

### 7.5 Calibration and Testing

**Camera Calibration Checklist:**

1. **Focus Check:**
   - Test autofocus at expected wand distances
   - Lock focus if distance is constant
   - Use manual focus mode if needed

2. **Exposure Calibration:**
   - Test in actual lighting conditions
   - Verify IR LED is brightest object
   - Check for blown-out highlights (LED blooming)

3. **Detection Validation:**
   - Test blob detection at various distances
   - Verify detection at frame edges (wide angle)
   - Check for false positives from reflections

4. **Performance Testing:**
   - Measure actual FPS under load
   - Monitor CPU usage (should be <80%)
   - Test sustained operation (thermal throttling)

**Test Script Template:**

```python
#!/usr/bin/env python3
"""Camera Module 3 NoIR Test Suite"""

import cv2
from picamera2 import Picamera2
import time
import numpy as np

def test_camera_detection():
    """Test if camera is detected"""
    try:
        cameras = Picamera2.global_camera_info()
        print(f"Detected cameras: {len(cameras)}")
        for cam in cameras:
            print(f"  {cam}")
        return len(cameras) > 0
    except Exception as e:
        print(f"Camera detection failed: {e}")
        return False

def test_capture_basic():
    """Test basic frame capture"""
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "XRGB8888"}
        )
        picam2.configure(config)
        picam2.start()
        time.sleep(2)

        frame = picam2.capture_array()
        picam2.stop()

        print(f"Captured frame: {frame.shape}, dtype: {frame.dtype}")
        return frame is not None
    except Exception as e:
        print(f"Capture test failed: {e}")
        return False

def test_fps_performance():
    """Test sustained frame rate"""
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "XRGB8888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)

    frame_count = 0
    start_time = time.time()
    duration = 10  # seconds

    while time.time() - start_time < duration:
        frame = picam2.capture_array()
        frame_count += 1

    fps = frame_count / duration
    picam2.stop()

    print(f"Average FPS: {fps:.1f}")
    return fps > 25  # Pass if >25 FPS

def test_blob_detection():
    """Test IR LED blob detection"""
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "XRGB8888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)

    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = 200
    params.maxThreshold = 255
    params.filterByArea = True
    params.minArea = 10
    detector = cv2.SimpleBlobDetector_create(params)

    detection_count = 0
    for _ in range(30):
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        keypoints = detector.detect(gray)
        if keypoints:
            detection_count += 1

    picam2.stop()
    detection_rate = detection_count / 30
    print(f"Blob detection rate: {detection_rate*100:.1f}%")
    return detection_rate > 0.5

def run_all_tests():
    """Run complete test suite"""
    print("=== Camera Module 3 NoIR Test Suite ===\n")

    tests = [
        ("Camera Detection", test_camera_detection),
        ("Basic Capture", test_capture_basic),
        ("FPS Performance", test_fps_performance),
        ("Blob Detection", test_blob_detection),
    ]

    results = []
    for name, test_func in tests:
        print(f"Running: {name}...")
        try:
            result = test_func()
            results.append((name, result))
            print(f"  Result: {'PASS' if result else 'FAIL'}\n")
        except Exception as e:
            results.append((name, False))
            print(f"  Result: FAIL ({e})\n")

    print("\n=== Test Summary ===")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r for _, r in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

if __name__ == "__main__":
    run_all_tests()
```

---

## 8. Official Documentation Links

### 8.1 Hardware Documentation

**Camera Module 3 Official Documentation:**
- [Camera Module 3 Product Brief (PDF)](https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf)
- [Camera Module 3 Sensor Assembly Brief (PDF)](https://datasheets.raspberrypi.com/camera/sensor-assembly-product-brief.pdf)
- [Raspberry Pi Camera Accessories Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [Camera Module 3 Product Page](https://www.raspberrypi.com/products/camera-module-3/)

**IMX708 Sensor Resources:**
- [Arducam 12MP IMX708 Wiki](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/12MP-IMX708/)
- [Waveshare IMX708 Camera Wiki](https://www.waveshare.com/wiki/IMX708_Camera)
- [Raspberry Pi Camera Module 3 - Waveshare Wiki](https://www.waveshare.com/wiki/Raspberry_Pi_Camera_Module_3)

**Raspberry Pi 5 Connection Guides:**
- [How to use Two Camera Modules with Raspberry Pi 5](https://thepihut.com/blogs/raspberry-pi-tutorials/how-to-use-two-camera-modules-with-raspberry-pi-5)
- [Getting a camera working on Raspberry Pi 5](https://www.xda-developers.com/connect-a-camera-module-to-raspberry-pi-5/)
- [Arducam Quick Start Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Quick-Start-Guide/)

### 8.2 Software Documentation

**picamera2 Official Resources:**
- [picamera2 GitHub Repository](https://github.com/raspberrypi/picamera2)
- [picamera2 Manual (PDF)](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [picamera2 PyPI Package](https://pypi.org/project/picamera2/)
- [picamera2.com Official Site](https://picamera2.com/)

**picamera2 Guides and Tutorials:**
- [Set Up Python Picamera2 on Raspberry Pi - Random Nerd Tutorials](https://randomnerdtutorials.com/raspberry-pi-picamera2-python/)
- [Picamera2 User Guide - Arducam Wiki](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/PiCamera2-User-Guide/)
- [Installation and Setup - DeepWiki](https://deepwiki.com/raspberrypi/picamera2/1.1-installation-and-setup)
- [Examples and Applications - DeepWiki](https://deepwiki.com/raspberrypi/picamera2/9-examples-and-applications)

**picamera2 Example Code:**
- [opencv_face_detect.py Example](https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect.py)
- [capture_motion.py Example](https://github.com/raspberrypi/picamera2/blob/main/examples/capture_motion.py)
- [picamera2 Examples Directory](https://github.com/raspberrypi/picamera2/tree/main/examples)

**libcamera Documentation:**
- [libcamera and rpicam-apps - Arducam Wiki](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Libcamera-User-Guide/)
- [Camera Software - Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html)

### 8.3 OpenCV Integration

**OpenCV with picamera2:**
- [Can Picamera2 work with OpenCV?](https://picamera2.com/can-picamera2-work-with-opencv/)
- [Using the Raspberry Pi Camera on Bullseye OS and OpenCV](https://toptechboy.com/using-the-raspberry-pi-camera-on-bullseye-os-and-opencv/)
- [Face Detection on Raspberry Pi 5 using OpenCV and Camera Module](https://www.cytron.io/tutorial/face-detection-on-raspberry-pi5-using-opencv-and-camera-module)
- [reTerminal and Pi camera with OpenCV - Seeed Studio Wiki](https://wiki.seeedstudio.com/reTerminal_DM_opencv/)

**OpenCV Blob Detection:**
- [Blob Detection Using OpenCV (Python, C++)](https://learnopencv.com/blob-detection-using-opencv-python-c/)
- [Blob Detection using OpenCV - OpenCV Blog](https://opencv.org/blog/blob-detection-using-opencv/)
- [SimpleBlobDetector Class Reference](https://docs.opencv.org/3.4/d0/d7a/classcv_1_1SimpleBlobDetector.html)

### 8.4 NoIR and IR Tracking

**NoIR Camera Resources:**
- [Using Camera Module V3 NoIR as Night-vision Camera - Forums](https://forums.raspberrypi.com/viewtopic.php?t=361003)
- [NoIR Camera Settings for Dark Nights - Forums](https://forums.raspberrypi.com/viewtopic.php?t=329590)
- [Raspberry Pi Camera Module 3 NoIR - The Pi Hut](https://thepihut.com/products/raspberry-pi-camera-module-3-noir)
- [Camera Module 3 Review - CNX Software](https://www.cnx-software.com/2023/01/23/raspberry-pi-camera-module-3-review-hdr-autofocus-wide-angle-and-noir-camera/)

**IR LED Tracking Projects:**
- [Turn on a lamp with a gesture - IR cam image processing](https://bloggerbrothers.com/2017/12/09/turn-on-a-lamp-with-a-gesture-ir-cam-image-processing/)
- [Raspberry Pi NoIR camera marker tracking - DreamOnward](https://dreamonward.com/2019/10/16/picamera-exploration/)
- [Tracking an Infrared LED - OpenCV Forum](https://answers.opencv.org/question/94298/tracking-an-infrared-led-or/)

### 8.5 Performance and Optimization

**Performance Resources:**
- [Optimize Raspberry Pi Camera V3 for Fast Capture](https://github.com/raspberrypi/picamera2/issues/926)
- [Increase FPS of real-time image capture](https://github.com/raspberrypi/picamera2/issues/490)
- [Camera module 3 drops lots of frames](https://forums.raspberrypi.com/viewtopic.php?t=347941)

**Calibration and Distortion:**
- [Camera Calibration (undistort lens) with OpenCV](https://github.com/raspberrypi/picamera2/issues/636)
- [Wide-angle lens distortion correction](https://forums.raspberrypi.com/viewtopic.php?t=361052)
- [Realtime Geometric Camera/Lens Distortion Correction](https://forums.raspberrypi.com/viewtopic.php?t=225077)

### 8.6 Community Forums and Support

**Official Forums:**
- [Raspberry Pi Forums - Camera](https://forums.raspberrypi.com/viewforum.php?f=43)
- [picamera2 GitHub Issues](https://github.com/raspberrypi/picamera2/issues)
- [picamera2 GitHub Discussions](https://github.com/raspberrypi/picamera2/discussions)

**Third-Party Resources:**
- [Raspberry Pi Stack Exchange - Camera](https://raspberrypi.stackexchange.com/questions/tagged/camera)
- [OpenCV Forums](https://forum.opencv.org/)

---

## Appendix A: Quick Reference Commands

### Camera Testing Commands

```bash
# Test camera detection
rpicam-hello

# Test NoIR camera with tuning file (Pi 5)
rpicam-hello --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx708_wide_noir.json

# Capture test image
rpicam-still -o test.jpg

# Record 10-second test video
rpicam-vid -t 10000 -o test.h264

# List available cameras
rpicam-hello --list-cameras

# Show camera properties
rpicam-hello --info-text "exp=%exp,ag=%ag,dg=%dg"
```

### System Commands

```bash
# Update system
sudo apt update && sudo apt upgrade

# Install picamera2
sudo apt install -y python3-picamera2

# Install OpenCV (if not installed)
sudo apt install -y python3-opencv

# Check Python packages
pip3 list | grep -E "picamera2|opencv"

# Check libcamera version
dpkg -l | grep libcamera

# Enable legacy camera (NOT recommended for Module 3)
# sudo raspi-config -> Interface Options -> Legacy Camera -> Enable
```

### Troubleshooting Commands

```bash
# Check for camera on CSI bus
vcgencmd get_camera

# View camera-related logs
dmesg | grep -i camera

# Check Raspberry Pi 5 camera config
cat /boot/firmware/config.txt | grep camera

# List available tuning files
ls /usr/share/libcamera/ipa/rpi/pisp/

# Test Python picamera2 import
python3 -c "from picamera2 import Picamera2; print('OK')"
```

---

## Appendix B: Troubleshooting Guide

### Common Issues and Solutions

**Issue: Camera not detected**
- Check CSI cable connection and orientation
- Verify Pi is powered off when connecting cable
- Try alternate CSI port (Pi 5 has two ports)
- Check for bent pins in CSI connector
- Run: `vcgencmd get_camera` (should show detected=1)

**Issue: "Failed to create camera" error**
- Update system: `sudo apt update && sudo apt upgrade`
- Ensure legacy camera stack is disabled
- Reboot after connecting camera
- Check permissions: `sudo usermod -a -G video $USER`

**Issue: No tuning file found for NoIR**
- Verify file exists: `ls /usr/share/libcamera/ipa/rpi/pisp/imx708*noir*`
- Update libcamera: `sudo apt install --reinstall libcamera-ipa`
- Use full absolute path to tuning file

**Issue: Poor IR LED detection**
- Increase IR LED power/brightness
- Adjust camera exposure: lower ExposureTime
- Increase Brightness negative value (darken background)
- Verify NoIR tuning file is loaded
- Check for ambient IR interference

**Issue: Low frame rate / dropped frames**
- Reduce resolution (640x480 instead of 1080p)
- Disable preview if not needed
- Use lores stream for processing
- Minimize processing per frame
- Check CPU temperature: `vcgencmd measure_temp`

**Issue: Blob detection not working**
- Adjust SimpleBlobDetector threshold parameters
- Print max pixel value: `np.max(gray)` (should be >240 for LED)
- Test with cv2.imshow() to visualize thresholded image
- Verify camera is focusing correctly (autofocus)

**Issue: Wide angle distortion affecting tracking**
- Perform camera calibration with checkerboard
- Apply cv2.undistort() to frames
- Or ignore if gestures performed in center 70% of frame

---

## Appendix C: Recommended Hardware

### IR LED Options

**For Wand Mounting:**
- 850nm IR LED, 100-150mW, 15-30° viewing angle
- Examples: VSLY5850, SFH 4550, TSAL6100
- Drive at 20-100mA with current-limiting resistor

**For Ambient Illumination:**
- 850nm IR LED array/flood light
- 12-48 LEDs, wide viewing angle (60-120°)
- Examples: CMVision IR illuminator, homemade LED panel

### Power Solutions

**For Wand:**
- 3.7V Li-Ion battery (18650 or similar)
- Current-limiting resistor or constant-current driver
- On/off switch for battery conservation

**For Raspberry Pi 5:**
- Official Raspberry Pi 27W USB-C Power Supply (5V, 5A)
- Quality USB-C cable (must support 5A)

### Cables and Adapters

**Camera Cable:**
- Raspberry Pi 5 Camera Cable (22-pin, various lengths)
- Part: Raspberry Pi Camera Cable for Pi 5
- Available: 200mm, 300mm, 500mm

**Alternative:**
- Raspberry Pi Zero camera cable (same connector as Pi 5)

---

## Summary and Recommendations

### For Your Interactive Wand Project

**Hardware Setup:**
1. Connect Camera Module 3 NoIR Wide to Pi 5 CSI port with 22-pin cable
2. Mount 850nm IR LED(s) at wand tip (driven at 50-100mA)
3. Position camera with clear view of gesture area

**Software Configuration:**
1. Install latest Raspberry Pi OS (Bullseye or later, 64-bit)
2. Update system and install picamera2
3. Load imx708_wide_noir.json tuning file for Pi 5
4. Configure camera for 640x480 @ 60 FPS
5. Set manual exposure (8000μs) and gain (6.0)
6. Underexpose scene (Brightness: -0.3) to isolate IR LED

**Blob Detection:**
1. Use SimpleBlobDetector with minThreshold=200
2. Filter by area (10-500 pixels) and circularity (>0.7)
3. Track blob center position for gesture trail
4. Integrate with existing SVM classifier for spell recognition

**Performance Optimization:**
1. Process at 640x480 resolution for real-time performance
2. Target 60 FPS for smooth gesture tracking
3. Use threading to separate capture and processing
4. Monitor CPU usage and optimize as needed

**Expected Results:**
- Reliable IR LED detection in dark/low-light environments
- Smooth 60 FPS tracking with <16ms latency
- Accurate gesture recognition when integrated with existing SVM model
- Wide 120° FOV ensures gestures stay in frame

This setup should integrate seamlessly with your existing `HarryPotterWandcv.py` code by replacing the current camera initialization and blob detection sections with the NoIR-optimized configurations provided in this document.

---

**Document Version:** 1.0
**Last Updated:** November 22, 2025
**Author:** Research Analyst
**Project:** Interactive Wand Gesture Recognition

---

## Sources

- [Camera - Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [Raspberry Pi Camera Module 3 - Waveshare Wiki](https://www.waveshare.com/wiki/Raspberry_Pi_Camera_Module_3)
- [Raspberry Pi Camera Module 3 Product Brief (PDF)](https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf)
- [CNX Software - Raspberry Pi Camera Module 3 Review](https://www.cnx-software.com/2023/01/23/raspberry-pi-camera-module-3-review-hdr-autofocus-wide-angle-and-noir-camera/)
- [Techeonics - Raspberry Pi Camera Module 3 Guide](https://techeonics.com/raspberry-pi-camera-module-3-guide/)
- [How to use Two Camera Modules with Raspberry Pi 5 - The Pi Hut](https://thepihut.com/blogs/raspberry-pi-tutorials/how-to-use-two-camera-modules-with-raspberry-pi-5)
- [XDA Developers - Connect a camera module to Raspberry Pi 5](https://www.xda-developers.com/connect-a-camera-module-to-raspberry-pi-5/)
- [Arducam - Quick Start Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Quick-Start-Guide/)
- [The Picamera2 Library (PDF Manual)](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [picamera2 GitHub Repository](https://github.com/raspberrypi/picamera2)
- [Random Nerd Tutorials - Set Up Python Picamera2](https://randomnerdtutorials.com/raspberry-pi-picamera2-python/)
- [Raspberry Pi Forums - Camera Module v3 with legacy stack](https://forums.raspberrypi.com/viewtopic.php?t=350820)
- [Arducam - libcamera and rpicam-apps User Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Libcamera-User-Guide/)
- [Raspberry Pi Forums - Using Camera Module V3 NoIR as Night-vision](https://forums.raspberrypi.com/viewtopic.php?t=361003)
- [Raspberry Pi Stack Exchange - Using NoIR as Night-vision Camera](https://raspberrypi.stackexchange.com/questions/145225/using-camera-module-v3-noir-as-night-vision-camera)
- [Arducam Blog - Official Camera Module 3: A Closer Look](https://blog.arducam.com/official-camera-module-3-a-closer-look/)
- [Raspberry Pi Forums - Noir Camera Settings for Dark Nights](https://forums.raspberrypi.com/viewtopic.php?t=329590)
- [Can Picamera2 work with OpenCV?](https://picamera2.com/can-picamera2-work-with-opencv/)
- [PyImageSearch - Accessing the Raspberry Pi Camera with OpenCV](https://pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/)
- [Raspberry Pi Forums - Using Picamera2 With OpenCv](https://forums.raspberrypi.com/viewtopic.php?t=369522)
- [Cytron - Face Detection on Raspberry Pi 5 using OpenCV](https://www.cytron.io/tutorial/face-detection-on-raspberry-pi5-using-opencv-and-camera-module)
- [picamera2 opencv_face_detect.py Example](https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect.py)
- [DreamOnward - Raspberry Pi NoIR camera marker tracking](https://dreamonward.com/2019/10/16/picamera-exploration/)
- [Blogger Brothers - Turn on a lamp with a gesture (IR)](https://bloggerbrothers.com/2017/12/09/turn-on-a-lamp-with-a-gesture-ir-cam-image-processing/)
- [Learn OpenCV - Blob Detection Using OpenCV](https://learnopencv.com/blob-detection-using-opencv-python-c/)
- [OpenCV Blog - Blob Detection using OpenCV](https://opencv.org/blog/blob-detection-using-opencv/)
- [OpenCV - SimpleBlobDetector Class Reference](https://docs.opencv.org/3.4/d0/d7a/classcv_1_1SimpleBlobDetector.html)
- [CNX Software - Camera Module 3 Review with HDR and NoIR](https://www.cnx-software.com/2023/01/23/raspberry-pi-camera-module-3-review-hdr-autofocus-wide-angle-and-noir-camera/)
- [Raspberry Pi Camera Module 3 Product Brief](https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf)
- [Arducam - 12MP IMX708 Sensor Documentation](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/12MP-IMX708/)
- [Raspberry Pi GitHub - Camera Hardware Documentation](https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/accessories/camera/camera_hardware.adoc)
- [Raspberry Pi Forums - Camera Calibration with picamera2](https://github.com/raspberrypi/picamera2/issues/636)
- [Raspberry Pi Forums - Wide-angle lens distortion](https://forums.raspberrypi.com/viewtopic.php?t=361052)
- [Raspberry Pi Forums - Realtime lens distortion correction](https://forums.raspberrypi.com/viewtopic.php?t=225077)
- [picamera2 GitHub - Optimize for Fast Capture](https://github.com/raspberrypi/picamera2/issues/926)
- [picamera2 GitHub - Increase FPS of real-time capture](https://github.com/raspberrypi/picamera2/issues/490)
- [Arducam Wiki - Picamera2 User Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/PiCamera2-User-Guide/)
