# IR Illuminator Integration Research Report
## Project Reference Plan (PRP) Document
**Project:** Interactive Wand Gesture Recognition
**Component:** 850nm DC12V 42-LED IR Board with NoIR Camera
**Date:** 2025-11-22
**Status:** Research Phase

---

## Executive Summary

This document provides comprehensive research and implementation guidance for integrating an 850nm DC12V 42-LED infrared illuminator board with a Raspberry Pi 5 and NoIR camera for wand tracking applications. The research covers hardware setup, optimal configuration, safety considerations, computer vision integration, and practical implementation guidelines.

**Key Findings:**
- 850nm IR wavelength is optimal for NoIR camera sensitivity and provides superior image quality compared to 940nm
- Logic-level MOSFET (not relay) recommended for PWM brightness control
- Separate 12V power supply required; estimated power consumption 3-4W for 42-LED board
- Co-axial or ring light positioning provides best results for blob tracking
- Eye safety compliant under IEC 62471 for typical usage scenarios
- SimpleBlobDetector with manual exposure control provides reliable wand tip tracking

---

## 1. Hardware Setup

### 1.1 Power Requirements

#### Power Supply Specifications
- **IR Board Requirements:** DC12V, estimated 3-4W for 42 LEDs
  - Based on scaling from 24-LED boards at ~1.92W (160mA @ 12V)
  - If using high-power 1W LEDs per element: potentially up to 42W
  - **Recommendation:** Use 12V 2A (24W) power supply for safety margin

#### Raspberry Pi 5 Power Requirements
- **Official Requirements:** 5V @ 5A (27W USB-PD)
- **Typical Draw:** 4-5W idle, up to 12W under full load
- **USB Power Budget:** Full 1.6A per port requires PSU_MAX_CURRENT=5000 in config.txt
- **Critical:** Do NOT power IR board from Pi's GPIO (max 16mA per pin)

#### Power Supply Options

**Option 1: Separate Power Supplies (Recommended)**
- Raspberry Pi 5: Official 27W USB-PD adapter
- IR Board: Dedicated 12V 2A power supply
- Advantages: Complete isolation, maximum stability, no interference
- Requirements: Common ground connection between supplies

**Option 2: Single High-Power Supply with Buck Converters**
- Input: 12V 5A (60W) power supply
- Buck converter #1: 12V to 5V @ 5A for Raspberry Pi 5
- Buck converter #2: 12V passthrough for IR board
- Advantages: Single wall outlet, cleaner cable management
- Caution: Requires proper buck converter rated for 5A continuous

### 1.2 GPIO Control Circuit

#### MOSFET vs Relay Decision

**Use MOSFET for IR LED Control** - Critical for PWM dimming capability

| Feature | MOSFET | Relay |
|---------|--------|-------|
| PWM Dimming | Yes - Fast switching | No - Too slow for PWM |
| Size | Compact | Bulky |
| Noise | Silent | Audible clicking |
| Lifespan | Unlimited switching | Limited cycles |
| Isolation | Moderate | Complete |
| Cost | Low | Moderate |

**Verdict:** MOSFET is required for brightness control and preferred for all DC switching applications.

#### Logic-Level MOSFET Circuit

**Critical Requirement:** Raspberry Pi GPIO outputs 3.3V, requiring "logic-level" MOSFETs with gate threshold voltage (Vgs(th)) below 3.3V.

**Recommended MOSFETs:**
- **IRLZ34N** - Logic-level, 30V, 30A (most recommended)
- **IRLZ44N** - Logic-level, 55V, 47A (common for motor control)
- **BUZ11** - Lower gate threshold, reliable
- **IRL540N** - Logic-level, 100V, 28A

**Avoid:** Standard MOSFETs like IRF540 (Vgs(th) = 2-4V) may not fully open at 3.3V

#### Wiring Diagram - MOSFET Control Circuit

```
Raspberry Pi 5                    12V Power Supply
    GPIO (3.3V) ----[1kΩ]---- MOSFET Gate          12V+ ----+
                                                              |
    GND ---------------------- MOSFET Source                  |
                                  |                           |
                                  |                      IR Board
                              12V GND                    LED+ ---+
                                                                 |
                                                          LED- to MOSFET Drain
```

**Complete Connection List:**
1. 12V Power Supply (+) → IR Board LED+ (red wire)
2. IR Board LED- (black wire) → MOSFET Drain pin
3. MOSFET Source pin → 12V Power Supply Ground (-)
4. MOSFET Gate pin → 1kΩ resistor → GPIO pin (e.g., GPIO 18)
5. Raspberry Pi GND → 12V Power Supply Ground (-)  **[CRITICAL: Common Ground]**
6. 10kΩ resistor between MOSFET Gate and Source (pull-down, optional but recommended)

**Component List:**
- 1x Logic-level N-channel MOSFET (IRLZ34N or equivalent)
- 1x 1kΩ resistor (gate protection)
- 1x 10kΩ resistor (gate pull-down, optional)
- Breadboard or PCB for prototyping
- 22 AWG wire for 12V connections
- Dupont jumper wires for GPIO

#### Python GPIO Control Example

```python
import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
IR_LED_PIN = 18  # GPIO 18 supports hardware PWM
GPIO.setup(IR_LED_PIN, GPIO.OUT)

# PWM for brightness control
pwm = GPIO.PWM(IR_LED_PIN, 1000)  # 1kHz frequency
pwm.start(0)  # Start at 0% brightness

# Turn on at 50% brightness
pwm.ChangeDutyCycle(50)

# Turn on at 100% brightness
pwm.ChangeDutyCycle(100)

# Turn off
pwm.ChangeDutyCycle(0)

# Cleanup
pwm.stop()
GPIO.cleanup()
```

### 1.3 Mounting and Positioning Considerations

#### Physical Mounting Options

**Option 1: Camera-Mounted Ring Configuration (Recommended)**
- Mount IR board in circular pattern around camera lens
- Distance: 2-5cm from lens center
- Provides even, shadow-free illumination
- Mimics professional co-axial lighting
- Best for consistent blob detection

**Option 2: Side-Mounted Configuration**
- Mount IR board 10-15cm to side of camera
- Angle: 15-30 degrees toward tracking area
- Creates slight shadows but reduces direct reflections
- Good for textureless backgrounds

**Option 3: Top-Mounted Configuration**
- Mount above camera at 20-30 degree angle
- Distance: 15-30cm above lens
- Provides downward illumination
- Reduces lens flare but may create shadows

#### Optimal Positioning for Blob Tracking

**Key Principles:**
1. **Co-axial is Best:** Light along optical axis minimizes shadows and provides even illumination
2. **Avoid Direct Reflections:** Angle away from reflective surfaces (glass, glossy walls, metal)
3. **Consider Working Distance:** Effective range 2-3 meters for 42-LED board
4. **Test with Background:** Evaluate reflections from your specific environment

**Recommended Setup for Wand Tracking:**
- Camera: Centered at performer eye level or slightly above
- IR Illuminator: Ring-mounted around camera lens OR mounted directly above camera
- Working Area: 1-2.5 meters from camera
- Background: Matte black or dark fabric (minimizes IR reflection)
- Ceiling/Walls: Cover reflective surfaces within camera field of view

#### Mounting Hardware

**For Camera Ring Mount:**
- 3D printed ring adapter (STL files available from camera accessory projects)
- Alternative: Flexible IR LED strip (850nm) wrapped around lens housing
- Use camera tripod mount as base

**For Separate Mount:**
- Adjustable camera mount arm
- Aluminum angle bracket with adjustment slots
- Velcro/adhesive mounting for temporary installation

---

## 2. Optimal Configuration

### 2.1 Positioning Relative to Camera

#### Distance and Angle Guidelines

**Illumination Distance from Camera:**
- **Ring/Co-axial Mount:** 0-5cm from lens (optimal)
- **Side Mount:** 10-20cm lateral distance
- **Top Mount:** 15-30cm vertical distance

**Illumination Angle:**
- **Target:** 0-15 degrees off optical axis (minimal shadowing)
- **Acceptable:** 15-30 degrees (slight shadows, reduced reflections)
- **Avoid:** >45 degrees (excessive shadowing, uneven illumination)

**Working Distance (Camera to Wand):**
- **Optimal Range:** 1.0 - 2.5 meters
- **Minimum:** 0.5 meters (may oversaturate)
- **Maximum:** 3.0 meters (diminishing returns for 42-LED board)

#### Field of View Considerations

**Camera Settings:**
- Use full sensor resolution for best detection (1920x1080 or higher)
- Frame rate: 30 FPS minimum, 60 FPS ideal for fast wand movements
- Focal length: Wide angle preferred (captures larger gesture area)

**Illumination Coverage:**
- IR beam angle: 60-120 degrees typical for multi-LED boards
- Ensure IR coverage matches or exceeds camera FOV
- Test illumination uniformity across entire tracking area

### 2.2 Brightness Levels for Wand Tip Detection

#### Power Level Recommendations

**Starting Configuration:**
- Begin at 50% PWM duty cycle
- Adjust based on ambient IR and camera response
- Target: Wand tip appears as bright, distinct blob without saturation

**Environmental Factors:**
1. **Outdoor/High Ambient Light:** Increase to 80-100%
2. **Indoor/Controlled Lighting:** 30-50% typically sufficient
3. **Reflective Background:** Reduce to 20-40% to prevent false positives
4. **Matte Black Background:** Can use 50-70% safely

#### Camera Exposure Optimization

**Manual Exposure Control (Critical):**
```python
import cv2

# Open camera
cap = cv2.VideoCapture(0)

# Set manual exposure (disable auto)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 = manual mode
cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # Range: -13 to -1, lower = darker

# Set manual ISO
cap.set(cv2.CAP_PROP_ISO_SPEED, 400)  # Fixed ISO

# Set manual white balance for NoIR
cap.set(cv2.CAP_PROP_AUTO_WB, 0)  # Disable auto white balance
cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 4000)  # Adjust as needed
```

**Recommended Exposure Values:**
- **Fast Wand Movement:** -8 to -10 (short exposure, prevents motion blur)
- **Moderate Movement:** -6 to -8 (balanced)
- **Slow/Precise Tracking:** -4 to -6 (longer exposure, more detail)

**ISO Settings:**
- **Low Noise Priority:** ISO 100-200
- **Balanced:** ISO 400-800
- **High Sensitivity:** ISO 1600+ (increases noise)

#### Brightness Testing Protocol

1. Set IR to 50% PWM, camera exposure to -6
2. Capture test frame with wand tip in center
3. Check histogram: Wand tip should be in 200-245 range (not 255 = saturated)
4. Verify no false blobs detected in background
5. Adjust IR power up/down by 10% increments
6. Lock settings once optimal

### 2.3 Avoiding IR Reflection and False Positives

#### Common Reflection Sources

**High-Risk Surfaces:**
- Glass windows and mirrors (specular reflection)
- Glossy painted walls
- Metal surfaces (doorknobs, fixtures)
- Shiny floors (polished wood, tile)
- Electronics with glossy screens
- Eyeglasses and jewelry

**Mitigation Strategies:**

1. **Background Control:**
   - Use matte black fabric backdrop
   - Cover or remove reflective objects from tracking area
   - Position camera to avoid windows/mirrors in FOV

2. **Illuminator Positioning:**
   - Angle IR board slightly off-axis to reflective surfaces
   - Use directional LED boards (narrower beam angle) if available

3. **Computer Vision Filtering:**
   - Background subtraction (remove static IR sources)
   - Kalman filtering (track expected wand motion, reject outliers)
   - Blob size/shape filtering (reflections often different shape)
   - Temporal consistency (track blob across frames, reject transients)

#### False Positive Reduction Techniques

**1. Background Subtraction:**
```python
import cv2

# Create background subtractor
bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=500,
    varThreshold=16,
    detectShadows=False
)

# Process frame
fg_mask = bg_subtractor.apply(frame)

# Use mask to filter out static IR sources
```

**2. Kalman Filter for Motion Tracking:**
```python
import cv2
import numpy as np

# Initialize Kalman filter
kalman = cv2.KalmanFilter(4, 2)  # 4 states (x,y,dx,dy), 2 measurements (x,y)
kalman.measurementMatrix = np.array([[1,0,0,0],
                                      [0,1,0,0]], np.float32)
kalman.transitionMatrix = np.array([[1,0,1,0],
                                     [0,1,0,1],
                                     [0,0,1,0],
                                     [0,0,0,1]], np.float32)

# Predict and update with each detection
prediction = kalman.predict()
estimated = kalman.correct(np.array([[x], [y]], np.float32))

# Reject measurements far from prediction (likely false positives)
distance = np.sqrt((x - prediction[0])**2 + (y - prediction[1])**2)
if distance > MAX_DISTANCE_THRESHOLD:
    # Reject as false positive
    pass
```

**3. Blob Shape Filtering:**
```python
# SimpleBlobDetector with shape constraints
params = cv2.SimpleBlobDetector_Params()

# Filter by circularity (reflections often non-circular)
params.filterByCircularity = True
params.minCircularity = 0.7  # 0.0 = line, 1.0 = perfect circle

# Filter by convexity
params.filterByConvexity = True
params.minConvexity = 0.8

# Filter by inertia (aspect ratio)
params.filterByInertia = True
params.minInertiaRatio = 0.6  # Rejects elongated shapes
```

**4. Temporal Filtering:**
- Require blob to be present for N consecutive frames (e.g., 3 frames)
- Reject transient reflections that appear for only 1-2 frames
- Track blob ID across frames using position/size matching

---

## 3. Safety

### 3.1 Eye Safety with 850nm IR LEDs

#### IEC 62471 Standard Overview

**Standard:** IEC 62471:2006 - "Photobiological safety of lamps and lamp systems"

**Risk Groups:**
- **Exempt Group:** No photobiological hazard (most small IR LEDs)
- **Risk Group 1:** Low risk (safe under normal conditions)
- **Risk Group 2:** Moderate risk (do not stare at source)
- **Risk Group 3:** High risk (momentary exposure hazardous)

#### 850nm Wavelength Hazard Profile

**Critical Facts:**
- **850nm is in retinal hazard band** - This near-IR wavelength can reach the retina
- Eye is transparent to 850nm (unlike skin which blocks it)
- **Invisible to most people** - No blink reflex response
- Higher power density than 940nm for same perceived brightness
- EU limit: 10mW/cm² above 700nm under IEC 62471

#### Exposure Limits

**IEC 62471 Exposure Limit (EL):**
- For exposure duration <10 seconds: Radiant exposure limit applies
- For continuous exposure: Irradiance limit E (W/m²) and radiance L (W/sr·m²)
- Specific limits depend on source size, viewing distance, and exposure duration

**Practical Safety Guidelines:**

1. **Typical 42-LED IR Board at 12V:**
   - Estimated total power: 3-4W
   - At 1 meter distance: ~3-4 mW/cm² (safe for continuous viewing)
   - At 0.5 meter distance: ~12-16 mW/cm² (exceeds EU guideline)
   - **Recommendation:** Maintain >1 meter distance from direct viewing

2. **Safe Operating Practices:**
   - Do NOT stare directly into IR board at close range (<50cm)
   - Do NOT use optical instruments (binoculars, telescopes) to view IR source
   - Mount IR board above eye level or angled away from performer's eyes
   - Use diffuser film if mounting close to eye level
   - Brief exposure during setup is safe; avoid prolonged direct exposure

3. **Verification:**
   - Use IR detection card or smartphone camera to verify beam pattern
   - Measure irradiance with calibrated meter if available
   - Most smartphone cameras can see 850nm as purple/pink glow

#### Risk Assessment for Wand Tracking Application

**Typical Setup:**
- IR board mounted near camera, 1.5-2m from performer
- Performer not looking directly at IR source (focused on gesture area)
- Exposure duration: Intermittent during spellcasting (seconds, not continuous)

**Risk Level:** **LOW - Exempt to Risk Group 1**

**Justification:**
- Distance >1 meter reduces irradiance below hazardous levels
- Intermittent exposure (not continuous staring)
- Performer's attention on wand/gesture, not IR source
- Power level (3-4W distributed across 42 LEDs) well below Class 2 threshold

**Safety Compliance:** Meets IEC 62471 requirements for consumer products

### 3.2 Power Consumption and Heat Management

#### Power Consumption Analysis

**42-LED IR Board Estimated Power:**
- **Standard LEDs:** 3-4W (70-100mW per LED) - Most likely for your board
- **High-Power LEDs:** Up to 42W (1W per LED) - Less likely, requires active cooling

**Verification Method:**
1. Measure current draw with multimeter in series with 12V supply
2. Calculate power: P = V × I (e.g., 12V × 0.3A = 3.6W)
3. Compare to power supply rating (should be <80% of PSU capacity)

**Power Supply Sizing:**
- 42-LED board @ 4W + 20% safety margin = 5W minimum
- **Recommended:** 12V 2A (24W) power supply provides ample headroom
- Allows for PWM brightness up to 100% without voltage sag

#### Heat Dissipation

**Thermal Characteristics:**
- IR LEDs convert electrical power to heat and IR radiation
- Efficiency: ~15-25% electrical to IR, remaining 75-85% becomes heat
- For 4W input: ~3W heat generation
- Temperature rise depends on board design and airflow

**Cooling Requirements:**

1. **Passive Cooling (Recommended for <5W):**
   - Aluminum PCB or board with thermal vias
   - Heatsink (optional): Small aluminum or copper heatsink with thermal adhesive
   - Natural convection: Mount vertically or at angle for air circulation
   - Ambient operation: Typical board temperature 40-60°C (safe)

2. **Active Cooling (Required for >10W):**
   - Small 40mm fan, 12V, 0.1A (powered from same supply)
   - Direct airflow across LED board
   - Reduces temperature to 30-40°C above ambient

**Mounting Considerations:**
- Do NOT enclose IR board in sealed plastic case (heat buildup)
- Provide ventilation slots if mounting in enclosure
- Keep away from heat-sensitive components (camera sensor)
- Monitor temperature during first test: Should be comfortably touchable

**Temperature Monitoring:**
- Use IR thermometer or thermal camera for non-contact measurement
- Target: <70°C LED junction temperature for longevity
- If board feels too hot to touch (>60°C), reduce duty cycle or add heatsink

**Fire Safety:**
- Use appropriate wire gauge: 22 AWG for <2A, 18 AWG for >2A
- Secure all connections (no exposed wire)
- Use fuse or circuit breaker on 12V supply (2A fast-blow fuse recommended)
- Never leave powered system unattended during initial testing

### 3.3 Electrical Safety with 12V

#### Voltage and Current Hazards

**12V DC Safety Profile:**
- **Voltage:** 12V is considered "Safety Extra-Low Voltage" (SELV)
- **Shock Hazard:** Minimal - 12V insufficient to penetrate dry skin (body resistance ~1kΩ)
- **Not lethal under normal conditions**
- **Exception:** Wet conditions or open wounds increase conductivity (avoid)

**Current Hazards:**
- 2A current can cause resistive heating in thin wires → fire hazard
- Short circuit can draw >10A momentarily → melting, sparks, fire
- **Use appropriate wire gauge and fuse protection**

#### Safe Wiring Practices

**Wire Gauge Selection:**
- 22 AWG: Good for up to 2A over short distances (<2m)
- 20 AWG: Safe for 2-3A
- 18 AWG: Recommended for 3-5A or longer runs (>2m)

**Connection Standards:**
- Use screw terminals, crimp connectors, or solder joints
- Avoid twisting bare wires together (unreliable, fire risk)
- Insulate all connections with heat shrink tubing or electrical tape
- Secure wires with cable ties to prevent strain on connections

**Polarity and Protection:**
- **Mark polarity clearly:** Red = +12V, Black = Ground/0V
- Add reverse polarity protection diode (1N4001 or equivalent) if desired
- Use 2A fast-blow fuse on +12V line
- Add 1000µF capacitor near IR board for supply filtering (optional)

#### Grounding and Isolation

**Common Ground Requirement:**
- Raspberry Pi GND and 12V supply GND must be connected
- This allows GPIO control signal to reference 12V circuit
- **Use single dedicated wire for ground connection** (star ground configuration)

**Isolation Considerations:**
- MOSFET provides moderate isolation (gate to drain/source)
- For complete isolation, use optocoupler + MOSFET (adds complexity)
- Current design is safe; optocoupler unnecessary for 12V DC

**Ground Loop Prevention:**
- Use single ground point (power supply ground terminal)
- Avoid multiple ground paths between Pi and 12V supply
- Keep ground wires short and direct

#### Electrical Testing Checklist

**Before First Power-Up:**
1. [ ] Visually inspect all connections
2. [ ] Verify polarity (red to +12V, black to GND)
3. [ ] Check for exposed wire/potential shorts
4. [ ] Measure resistance: 12V+ to 12V- should be >10Ω (with IR board connected)
5. [ ] Confirm MOSFET wiring: Gate to GPIO, Drain to LED-, Source to GND
6. [ ] Double-check common ground: Pi GND to 12V GND

**During Power-Up:**
1. [ ] Connect 12V supply to IR board (not to Pi yet)
2. [ ] Power on 12V supply
3. [ ] Check IR board lights up (view with smartphone camera)
4. [ ] Measure voltage at IR board terminals: Should be 11.5-12.5V
5. [ ] Feel IR board temperature after 1 minute: Should be warm, not hot
6. [ ] Power off 12V supply
7. [ ] Connect ground wire: Pi GND to 12V GND
8. [ ] Power on Raspberry Pi 5
9. [ ] Power on 12V supply
10. [ ] Test GPIO control: Set GPIO high/low to switch IR

---

## 4. Integration with Computer Vision

### 4.1 How 850nm IR Works with NoIR Cameras

#### NoIR Camera Sensor Characteristics

**Standard vs NoIR Sensor:**
- **Standard Camera:** Has IR-cut filter (blocks >700nm)
- **NoIR Camera:** IR-cut filter removed, sensitive to 400-1000nm
- **Result:** NoIR sensors respond strongly to 850nm IR

**Sensor Response at 850nm:**
- All three color channels (R, G, B) are sensitive to 850nm
- Red channel typically has highest sensitivity (~80-90% of peak)
- Green and blue channels also respond (~60-70% of peak)
- **Result:** IR appears as bright white/gray in captured images

**Raspberry Pi Camera Module 3 NoIR:**
- Sensor: Sony IMX708, 12MP
- Quantum Efficiency at 850nm: Not published, but confirmed to work well
- Sensitivity higher at 850nm than 940nm (confirmed by users)
- Sensitivity drops roughly linearly from 850nm to 1050nm

#### 850nm vs 940nm Comparison

| Characteristic | 850nm | 940nm |
|----------------|-------|-------|
| Camera Sensitivity | High (optimal) | Lower (~60% of 850nm) |
| Visible to Human Eye | Faint red glow | Invisible |
| IR Range | Longer (better efficiency) | Shorter |
| Image Quality | Excellent | Good |
| Cost | Lower | Similar |
| **Recommendation** | **Preferred for wand tracking** | Use if covert operation required |

**Why 850nm is Better for Your Application:**
- Maximum camera sensitivity → brightest wand tip blob
- Greater range allows lower LED power → cooler operation
- Lower cost and wider availability
- Faint red glow is negligible in dim lighting (typical for interactive installations)

#### IR Illumination Characteristics

**Illumination Properties:**
- 850nm IR reflects off objects similar to visible light
- Diffuse reflection from matte surfaces (good for background suppression)
- Specular reflection from glossy surfaces (causes false positives - manage carefully)
- No color information (all objects appear as grayscale brightness)

**Advantages for Blob Tracking:**
1. High contrast: Bright IR LED on wand tip appears as distinct bright spot
2. Background suppression: Ambient visible light doesn't interfere with IR channel
3. Invisible to audience: Doesn't distract from theatrical presentation
4. Consistent lighting: Independent of room lighting changes

### 4.2 Optimal Camera Settings for IR Blob Detection

#### Camera Parameter Configuration

**Resolution:**
- **Recommended:** 640x480 (VGA) for real-time processing
- Higher resolution (1920x1080) provides more precision but slower FPS
- Balance: 1280x720 @ 30 FPS for good precision and speed

**Frame Rate:**
- **Minimum:** 30 FPS
- **Recommended:** 60 FPS for fast wand movements
- Higher FPS reduces motion blur and improves temporal resolution

#### Exposure Control (Critical)

**Manual Exposure Settings:**
```python
import cv2
from picamera2 import Picamera2

# For PiCamera2 (Raspberry Pi Camera Module 3)
picam2 = Picamera2()
config = picam2.create_preview_configuration()

# Manual exposure control
config["controls"]["ExposureTime"] = 10000  # 10ms (adjust 5000-20000)
config["controls"]["AnalogueGain"] = 4.0    # ISO equivalent (1.0-16.0)

# Disable auto functions
config["controls"]["AeEnable"] = False      # Disable auto exposure
config["controls"]["AwbEnable"] = False     # Disable auto white balance

# Set color gains for NoIR (reduces color cast)
config["controls"]["ColourGains"] = (1.5, 1.5)  # (Red gain, Blue gain)

picam2.configure(config)
picam2.start()
```

**Recommended Values:**
- **ExposureTime:** 5000-15000 µs (5-15ms)
  - Shorter exposure: Less motion blur, darker image
  - Longer exposure: More motion blur, brighter image
  - Start with 10000 µs and adjust

- **AnalogueGain (ISO equivalent):**
  - Low gain (1.0-2.0): Clean image, less sensitivity
  - Medium gain (3.0-5.0): Balanced (recommended)
  - High gain (8.0+): Noisy but sensitive

**Tuning Process:**
1. Start with ExposureTime=10000, AnalogueGain=4.0
2. Capture frame with IR LED wand tip
3. Check histogram: Wand tip should be 200-240 range
4. If too dim: Increase AnalogueGain or ExposureTime
5. If too bright/saturated: Decrease ExposureTime first
6. If motion blur visible: Reduce ExposureTime, increase AnalogueGain to compensate

#### White Balance for NoIR

**Problem:** NoIR sensors see IR as bright intensity, but color channels can be imbalanced

**Solution:** Set fixed color gains to reduce color cast
```python
# Adjust red and blue gains to neutralize color cast
config["controls"]["ColourGains"] = (1.5, 1.8)  # Typical for 850nm IR
```

**Tuning:**
- Capture frame with IR illumination only
- If image appears pinkish: Increase blue gain
- If image appears cyan: Increase red gain
- Goal: Neutral gray appearance

#### Image Pre-Processing

**Recommended Pipeline:**
1. Capture frame from camera
2. Convert to grayscale (BGR → GRAY)
3. Apply Gaussian blur (reduces noise)
4. Apply binary threshold
5. Morphological operations (optional: removes small noise)
6. Blob detection

```python
import cv2
import numpy as np

# Capture frame
ret, frame = cap.read()

# Convert to grayscale
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Gaussian blur (kernel size must be odd)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Binary threshold (adjust threshold value based on IR brightness)
_, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

# Optional: Morphological opening (removes small noise)
kernel = np.ones((3,3), np.uint8)
morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

# Blob detection on processed image
keypoints = detector.detect(morph)
```

**Threshold Value Selection:**
- Too low (e.g., 100): Detects noise and false positives
- Too high (e.g., 240): Misses dim parts of wand LED
- **Recommended:** 180-220 for well-illuminated wand tip
- Use adaptive thresholding if lighting varies

### 4.3 Tuning SimpleBlobDetector for IR Markers

#### SimpleBlobDetector Algorithm Overview

SimpleBlobDetector identifies blobs by:
1. Thresholding grayscale image at multiple levels (minThreshold to maxThreshold)
2. Extracting connected components (blobs) at each threshold
3. Computing blob centers and sizes
4. Merging blobs closer than minDistBetweenBlobs
5. Filtering blobs by color, area, circularity, convexity, and inertia

#### Optimal Parameters for IR LED Wand Tip

```python
import cv2

# Create parameter object
params = cv2.SimpleBlobDetector_Params()

# Thresholding
params.minThreshold = 10
params.maxThreshold = 255
params.thresholdStep = 10

# Filter by Color (Brightness)
params.filterByColor = True
params.blobColor = 255  # Detect bright blobs (white on black background)

# Filter by Area (size in pixels)
params.filterByArea = True
params.minArea = 10       # Minimum blob size (adjust based on distance and LED size)
params.maxArea = 500      # Maximum blob size (prevents detecting large reflections)

# Filter by Circularity (0.0 = line, 1.0 = perfect circle)
params.filterByCircularity = True
params.minCircularity = 0.6  # LED should appear roughly circular
params.maxCircularity = 1.0

# Filter by Convexity (ratio of blob area to convex hull area)
params.filterByConvexity = True
params.minConvexity = 0.8    # LED blob should be convex (not concave)

# Filter by Inertia (aspect ratio: 0.0 = line, 1.0 = circle)
params.filterByInertia = True
params.minInertiaRatio = 0.5  # Rejects elongated shapes (e.g., reflections from edges)

# Distance between blobs
params.minDistBetweenBlobs = 30  # Minimum separation between detected blobs (pixels)

# Create detector
detector = cv2.SimpleBlobDetector_create(params)

# Detect blobs
keypoints = detector.detect(image)

# Draw detected blobs
im_with_keypoints = cv2.drawKeypoints(image, keypoints, np.array([]),
                                       (0, 255, 0),
                                       cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
```

#### Parameter Tuning Guidelines

**Area Filtering (Most Important):**
- **Minimum Area:** Set based on expected LED size at maximum distance
  - Close range (0.5m): minArea = 50-100 pixels
  - Medium range (1.5m): minArea = 20-50 pixels
  - Far range (3m): minArea = 5-20 pixels
- **Maximum Area:** Prevents detecting large reflections or filled regions
  - Set to 5-10x the expected LED size
  - Example: If LED typically 100 pixels, set maxArea = 500-1000

**Circularity Filtering:**
- **minCircularity = 0.6-0.8:** Allows slightly oval shapes (perspective distortion)
- **minCircularity = 0.5:** More permissive (useful if LED appears as streak due to motion blur)
- **minCircularity = 0.9:** Very strict (rejects anything not nearly circular)

**Convexity Filtering:**
- **minConvexity = 0.8-0.9:** Standard setting for LED blobs
- Rejects concave shapes (unlikely for point light source)

**Inertia Filtering:**
- **minInertiaRatio = 0.5-0.7:** Allows slightly elongated blobs
- Lower values: More permissive (useful for fast motion)
- Higher values: Stricter circularity

**Distance Between Blobs:**
- **minDistBetweenBlobs = 30-50 pixels:** Typical for wand tracking
- Prevents detecting multiple blobs for single LED (due to thresholding artifacts)
- Set based on expected spacing if tracking multiple LEDs

#### Practical Tuning Workflow

**Step 1: Capture Reference Image**
```python
# Capture frame with wand LED visible
ret, frame = cap.read()
cv2.imwrite("reference.jpg", frame)
```

**Step 2: Start with Permissive Parameters**
```python
params.filterByArea = True
params.minArea = 5
params.maxArea = 5000
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
```

**Step 3: Verify Detection**
- Run detector on reference image
- Check if LED is detected (should have at least 1 keypoint)
- If not detected: Check threshold values and ensure image is bright enough

**Step 4: Add Area Constraint**
- Measure detected blob size (keypoints[0].size)
- Set minArea = 0.5 × measured size
- Set maxArea = 3.0 × measured size

**Step 5: Enable Shape Filters Progressively**
- Enable circularity: minCircularity = 0.6
- Test detection still works
- Enable convexity: minConvexity = 0.8
- Test detection still works
- Enable inertia: minInertiaRatio = 0.5
- Test detection still works

**Step 6: Test with Motion and Variations**
- Capture frames with wand at different distances
- Capture frames with wand in motion (blur)
- Capture frames with potential reflections
- Adjust parameters to balance detection rate and false positive rejection

#### Integration with Existing Wand Tracking System

Based on your project's current implementation, integrate SimpleBlobDetector:

```python
import cv2
import numpy as np
from picamera2 import Picamera2

# Initialize camera
picam2 = Picamera2()
config = picam2.create_preview_configuration()
config["controls"]["ExposureTime"] = 10000
config["controls"]["AnalogueGain"] = 4.0
config["controls"]["AeEnable"] = False
picam2.configure(config)
picam2.start()

# Configure SimpleBlobDetector
params = cv2.SimpleBlobDetector_Params()
params.filterByColor = True
params.blobColor = 255
params.filterByArea = True
params.minArea = 20
params.maxArea = 500
params.filterByCircularity = True
params.minCircularity = 0.6
params.filterByConvexity = True
params.minConvexity = 0.8
params.filterByInertia = True
params.minInertiaRatio = 0.5
detector = cv2.SimpleBlobDetector_create(params)

# Main tracking loop
wand_trail = []
while True:
    # Capture frame
    frame = picam2.capture_array()

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold for bright objects
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    # Detect blobs
    keypoints = detector.detect(thresh)

    # If wand detected, add to trail
    if len(keypoints) > 0:
        # Use largest blob (in case multiple detections)
        largest_blob = max(keypoints, key=lambda kp: kp.size)
        wand_pos = (int(largest_blob.pt[0]), int(largest_blob.pt[1]))
        wand_trail.append(wand_pos)

        # Limit trail length
        if len(wand_trail) > 100:
            wand_trail.pop(0)

    # Draw trail on frame
    for i in range(1, len(wand_trail)):
        cv2.line(frame, wand_trail[i-1], wand_trail[i], (0, 255, 0), 2)

    # Draw detected blobs
    frame_with_blobs = cv2.drawKeypoints(frame, keypoints, np.array([]),
                                          (0, 0, 255),
                                          cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # Display
    cv2.imshow("Wand Tracking", frame_with_blobs)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
```

#### Advanced: Multiple LED Tracking

If your wand has multiple IR LEDs for 3D pose estimation:

```python
# Detect multiple blobs
keypoints = detector.detect(thresh)

# Sort by size (brightness)
keypoints_sorted = sorted(keypoints, key=lambda kp: kp.size, reverse=True)

# Extract top N LEDs (e.g., 3 for triangulation)
if len(keypoints_sorted) >= 3:
    led1 = keypoints_sorted[0].pt
    led2 = keypoints_sorted[1].pt
    led3 = keypoints_sorted[2].pt

    # Calculate wand orientation from LED positions
    # (solvePnP or custom geometric solution)
```

---

## 5. Documentation and Resources

### 5.1 Technical Documentation URLs

#### IR Illumination and Computer Vision

1. **Basler Near-Infrared (NIR) Cameras Guide**
   https://www.baslerweb.com/en/learning/near-infrared-nir-cameras/
   - Comprehensive overview of NIR camera technology and applications

2. **850nm vs 940nm Wavelength Comparison**
   https://smartlivingindia.com/learn/850nm-vs-940nm-ir-wavelengths/
   - Detailed comparison of IR wavelengths for security and vision applications

3. **Kolari Vision 850nm Infrared Information**
   https://kolarivision.com/camera-filters/850nm-infrared/
   - Technical details on 850nm photography and camera modifications

4. **Raspberry Pi NoIR Camera Marker Tracking**
   https://dreamonward.com/2019/10/16/picamera-exploration/
   - Practical guide to using NoIR camera for IR marker tracking

5. **Waveshare RPi NoIR Camera V2 Wiki**
   https://www.waveshare.com/wiki/RPi_NoIR_Camera_V2
   - Specifications and usage information for NoIR cameras

#### OpenCV and Blob Detection

6. **OpenCV SimpleBlobDetector Official Documentation**
   https://docs.opencv.org/3.4/d0/d7a/classcv_1_1SimpleBlobDetector.html
   - Complete API reference for SimpleBlobDetector class

7. **LearnOpenCV: Blob Detection Tutorial**
   https://learnopencv.com/blob-detection-using-opencv-python-c/
   - Step-by-step tutorial with code examples

8. **OpenCV Answers: Tracking Infrared LED**
   https://answers.opencv.org/question/94298/tracking-an-infrared-led-or/
   - Community discussion on IR LED tracking techniques

9. **SimpleBlobDetector Threshold Discussion**
   https://answers.opencv.org/question/60374/simpleblobdetector-threshold/
   - Detailed explanation of thresholding parameters

#### Raspberry Pi GPIO Control

10. **Controlling Relay from Raspberry Pi (Electronics Stack Exchange)**
    https://electronics.stackexchange.com/questions/448739/correct-way-to-control-12v-relay-from-a-raspberry-pi
    - Detailed circuit analysis for transistor/relay control

11. **My HydroPi: Connecting Relay Board**
    https://myhydropi.com/connecting-a-relay-board-to-a-raspberry-pi/
    - Practical wiring guide with diagrams

12. **Raspberry Pi Control Relay via GPIO (Tutorials)**
    https://tutorials-raspberrypi.com/raspberry-pi-control-relay-switch-via-gpio/
    - Complete tutorial with code examples

13. **ElectronicsHub: Raspberry Pi Relay Control**
    https://www.electronicshub.org/control-a-relay-using-raspberry-pi/
    - Comprehensive guide including safety considerations

14. **Raspberry Pi Forums: Full LED Brightness with MOSFET and PWM**
    https://forums.raspberrypi.com/viewtopic.php?t=122390
    - Practical discussion on MOSFET selection and PWM control

15. **Raspberry Pi Stack Exchange: Controlling 12V RGB LED Strip**
    https://raspberrypi.stackexchange.com/questions/5231/controlling-a-12v-rgb-led-strip-with-the-gpio
    - MOSFET wiring and PWM dimming techniques

#### Raspberry Pi 5 Power and Configuration

16. **Bret.dk: How to Power Raspberry Pi 5 - Complete Guide**
    https://bret.dk/how-to-power-the-raspberry-pi-5-a-complete-guide/
    - Official power requirements and alternatives

17. **Raspberry Pi Forums: Powering the Raspberry Pi 5**
    https://forums.raspberrypi.com/viewtopic.php?t=357129
    - Community discussion on power supply options

18. **Raspberry Pi Forums: Power Supply +5V via GPIO**
    https://forums.raspberrypi.com/viewtopic.php?t=358008
    - GPIO power considerations and PSU_MAX_CURRENT configuration

#### Eye Safety and IEC Standards

19. **Vishay: Eye Safety for Infrared LEDs (PDF)**
    https://www.vishay.com/docs/81935/eyesafe.pdf
    - Comprehensive technical document on IR LED eye safety

20. **Renesas: Eye Safety for Proximity Sensing Using IR LEDs**
    https://www.renesas.com/en/document/apn/an1737-eye-safety-proximity-sensing-using-infrared-light-emitting-diodes
    - Application note with calculations and guidelines

21. **Electronics Stack Exchange: Eye Safety Limits for IR LEDs**
    https://electronics.stackexchange.com/questions/366731/how-do-i-determine-eye-safety-limits-for-ir-leds
    - Practical discussion on applying IEC 62471 standard

22. **Tech-LED: Near Infrared (NIR) LED Guide**
    https://tech-led.com/near-infrared-nir-led/
    - Specifications and safety information for NIR LEDs

23. **Smart Vision Lights: IEC/EN 62471 Summary (PDF)**
    https://smartvisionlights.com/wp-content/uploads/IEC_62471_summary.pdf
    - Concise summary of IEC 62471 standard requirements

24. **Lumileds: LUXEON IR Family Eye Safety**
    https://lumileds.com/AB191-4-LUXEON-IR-Family-Eye-Safety-Application-Brief
    - Application brief with safety calculations for high-power IR LEDs

#### Raspberry Pi Camera and NoIR

25. **Raspberry Pi Camera Module 3 Product Brief (PDF)**
    https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf
    - Official specifications for Camera Module 3 and NoIR variants

26. **Arducam: Camera Module 3 In-Depth Look**
    https://blog.arducam.com/official-camera-module-3-a-closer-look/
    - Detailed analysis of Camera Module 3 features and performance

27. **Raspberry Pi Forums: NoIR Camera Sensitivity**
    https://forums.raspberrypi.com/viewtopic.php?t=131384
    - Community discussion on NoIR sensitivity characteristics

28. **Raspberry Pi Forums: RPi V3 NoIR Camera QE in IR Spectrum**
    https://forums.raspberrypi.com/viewtopic.php?t=387992
    - Technical discussion on quantum efficiency at IR wavelengths

#### Machine Vision Lighting Techniques

29. **Advanced Illumination: Coaxial Lights**
    https://advancedillumination.com/products/category/coaxial-light/
    - Professional coaxial lighting systems for machine vision

30. **Vision Datum: How to Choose Coaxial Lights**
    https://shop.visiondatum.com/blogs/blog/how-to-choose-coaxial-lights
    - Guide to selecting and positioning coaxial illumination

31. **Edmund Optics: IR Adjustable LED Ring Light**
    https://www.edmundoptics.com/p/ir-adjustable-led-ring-light/4013/
    - Specifications for professional IR ring lights

32. **ProPhotonix: Infrared Machine Vision Lighting**
    https://www.prophotonix.com/applications/machine-vision-lighting/ir-machine-vision-lighting/
    - Overview of IR lighting for industrial vision applications

33. **Spectrum Illumination: Diffused Axial Lighting**
    https://spectrumillumination.com/product-type/diffused-axial/
    - Technical information on axial (on-axis) illumination

#### Computer Vision Algorithms and Filtering

34. **GitHub: BlobTracker - IR Blob Tracker**
    https://github.com/timrolls/BlobTracker
    - Open-source IR blob tracking with perspective correction

35. **Interactive & Immersive: Blob Tracking in TouchDesigner**
    https://interactiveimmersive.io/blog/touchdesigner-resources/blob-tracking-tricks-in-touchdesigner/
    - Advanced blob tracking techniques applicable to real-time systems

36. **Electronics Stack Exchange: Making IR LEDs Identifiable**
    https://electronics.stackexchange.com/questions/38809/any-ideas-to-make-ir-leds-identifiable-during-position-tracking
    - Techniques for tracking multiple IR markers

37. **OpenCV Answers: Detect IR LED in OpenCV**
    https://answers.opencv.org/question/202932/detect-ir-led-in-opencv/
    - Practical advice on IR detection algorithms

### 5.2 Datasheets and Component Information

#### Recommended MOSFETs

- **IRLZ34N Datasheet:** Logic-level N-channel MOSFET (30V, 30A)
  Search: "IRLZ34N datasheet PDF"
  Key specs: Vgs(th) = 1-2V, Rds(on) = 0.042Ω @ 5V Vgs

- **IRLZ44N Datasheet:** Logic-level N-channel MOSFET (55V, 47A)
  Search: "IRLZ44N datasheet PDF"
  Key specs: Vgs(th) = 1-2V, Rds(on) = 0.022Ω @ 5V Vgs

- **IRL540N Datasheet:** Logic-level N-channel MOSFET (100V, 28A)
  Search: "IRL540N datasheet PDF"
  Key specs: Vgs(th) = 1-2V, Rds(on) = 0.044Ω @ 5V Vgs

#### IR LED Boards

- **850nm IR Illuminator Boards:** Search "850nm 42 LED board specifications"
  Typical specs:
  - Wavelength: 850nm ±10nm
  - Forward voltage: 1.2-1.5V per LED
  - Forward current: 50-150mA per LED (depending on type)
  - Beam angle: 60-120 degrees
  - Radiant intensity: 10-50 mW/sr per LED

#### Power Supplies

- **12V 2A AC/DC Adapter:** UL/CE certified
  - Output: 12V DC ±5%, 2A maximum
  - Input: 100-240V AC, 50/60Hz
  - Protection: Overcurrent, short-circuit, overvoltage
  - Connector: 2.1mm barrel jack (standard) or screw terminals

- **Raspberry Pi 5 27W USB-PD Power Supply (Official)**
  - Output: 5.1V @ 5A (USB-PD)
  - Connector: USB-C
  - Protocols: USB Power Delivery 3.0

### 5.3 Additional Reading

#### Academic Papers (Optional Deep Dive)

1. **"Vision-Based Finger Detection, Tracking, and Event Identification"**
   https://pmc.ncbi.nlm.nih.gov/articles/PMC3231698/
   - Multi-touch sensing techniques applicable to wand tracking

2. **"Robust Real-Time Eye Detection and Tracking"** (ScienceDirect)
   https://www.sciencedirect.com/science/article/abs/pii/S1077314204001158
   - Advanced tracking algorithms under variable lighting

#### Community Forums and Support

- **Raspberry Pi Forums - Camera Section**
  https://forums.raspberrypi.com/viewforum.php?f=43
  - Active community for camera troubleshooting

- **OpenCV Q&A Forum**
  https://answers.opencv.org/
  - Expert help on computer vision algorithms

- **Electronics Stack Exchange**
  https://electronics.stackexchange.com/
  - Circuit design and safety questions

- **Raspberry Pi Stack Exchange**
  https://raspberrypi.stackexchange.com/
  - Raspberry Pi-specific hardware and software questions

---

## 6. Practical Implementation Checklist

### 6.1 Pre-Assembly Checklist

**Components to Acquire:**
- [ ] 850nm DC12V 42-LED IR illuminator board
- [ ] 12V 2A power supply (barrel jack or screw terminal output)
- [ ] Logic-level N-channel MOSFET (IRLZ34N, IRLZ44N, or IRL540N)
- [ ] 1kΩ resistor (1/4W or 1/2W)
- [ ] 10kΩ resistor (1/4W or 1/2W, optional pull-down)
- [ ] 2A fast-blow fuse + fuse holder (recommended)
- [ ] 22 AWG hookup wire (red and black)
- [ ] Heat shrink tubing or electrical tape
- [ ] Breadboard or perfboard for circuit assembly
- [ ] Multimeter (for testing)
- [ ] IR detection card or smartphone (to verify IR operation)

**Tools Required:**
- [ ] Wire strippers
- [ ] Soldering iron and solder (if permanent assembly)
- [ ] Screwdriver set
- [ ] Heat gun or lighter (for heat shrink)
- [ ] Cable ties
- [ ] Mounting hardware (brackets, screws, or 3D printed parts)

### 6.2 Assembly Steps

**Step 1: Circuit Assembly**
1. Insert MOSFET into breadboard
2. Connect 1kΩ resistor between GPIO wire and MOSFET Gate
3. Connect 10kΩ resistor between MOSFET Gate and Source (optional)
4. Verify connections with multimeter (no shorts)

**Step 2: Power Supply Wiring**
1. Connect 12V power supply to fuse holder
2. Connect fuse holder output to breadboard power rails
3. Connect IR board LED+ to +12V rail (red wire)
4. Connect IR board LED- to MOSFET Drain (black wire)
5. Connect MOSFET Source to 12V ground rail

**Step 3: Raspberry Pi Integration**
1. Power off Raspberry Pi 5
2. Connect jumper wire from GPIO pin (e.g., GPIO 18) to MOSFET Gate resistor
3. Connect jumper wire from Pi GND to 12V ground rail (common ground)
4. Double-check all connections

**Step 4: Initial Power-Up**
1. Verify all connections one final time
2. Power on 12V supply (Pi still off)
3. Check for smoke, smell, or heat (emergency: disconnect immediately)
4. Use smartphone camera to verify IR board lights up
5. Measure voltage at IR board: should be 11.5-12.5V
6. Power on Raspberry Pi 5

**Step 5: GPIO Control Test**
```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
IR_PIN = 18
GPIO.setup(IR_PIN, GPIO.OUT)

# Test on/off
print("IR ON")
GPIO.output(IR_PIN, GPIO.HIGH)
time.sleep(2)

print("IR OFF")
GPIO.output(IR_PIN, GPIO.LOW)
time.sleep(2)

GPIO.cleanup()
```

**Step 6: PWM Dimming Test**
```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
IR_PIN = 18
GPIO.setup(IR_PIN, GPIO.OUT)

pwm = GPIO.PWM(IR_PIN, 1000)  # 1kHz
pwm.start(0)

# Fade in
for duty in range(0, 101, 5):
    pwm.ChangeDutyCycle(duty)
    print(f"Brightness: {duty}%")
    time.sleep(0.2)

# Fade out
for duty in range(100, -1, -5):
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.2)

pwm.stop()
GPIO.cleanup()
```

### 6.3 Camera Configuration Steps

**Step 1: Install Required Libraries**
```bash
sudo apt update
sudo apt install -y python3-opencv python3-picamera2
```

**Step 2: Enable Camera Interface**
```bash
sudo raspi-config
# Navigate to: Interfacing Options → Camera → Enable
sudo reboot
```

**Step 3: Test Camera Capture**
```python
from picamera2 import Picamera2
import cv2

picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)
picam2.start()

# Capture test image
frame = picam2.capture_array()
cv2.imwrite("test_capture.jpg", frame)
print("Test image saved as test_capture.jpg")

picam2.stop()
```

**Step 4: Configure Manual Exposure for IR**
```python
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration()

# Manual settings for IR tracking
config["controls"]["ExposureTime"] = 10000  # Start at 10ms
config["controls"]["AnalogueGain"] = 4.0     # Medium gain
config["controls"]["AeEnable"] = False       # Disable auto exposure
config["controls"]["AwbEnable"] = False      # Disable auto white balance
config["controls"]["ColourGains"] = (1.5, 1.5)  # Neutral for 850nm

picam2.configure(config)
picam2.start()

# Capture with manual settings
frame = picam2.capture_array()
cv2.imwrite("ir_test.jpg", frame)

picam2.stop()
```

**Step 5: Tune Exposure for Your Setup**
- Capture image with IR on and wand visible
- Check wand tip brightness (should be 200-240 in histogram)
- If too dim: increase AnalogueGain or ExposureTime
- If too bright: decrease ExposureTime
- If motion blur: decrease ExposureTime, increase AnalogueGain

### 6.4 Blob Detection Tuning Steps

**Step 1: Capture Reference Images**
```python
# Capture images at various distances
distances = ["close_50cm", "medium_150cm", "far_250cm"]
for dist in distances:
    input(f"Position wand at {dist}, then press Enter")
    frame = picam2.capture_array()
    cv2.imwrite(f"reference_{dist}.jpg", frame)
    print(f"Captured reference_{dist}.jpg")
```

**Step 2: Start with Minimal Filtering**
```python
import cv2

params = cv2.SimpleBlobDetector_Params()
params.filterByColor = True
params.blobColor = 255
params.filterByArea = True
params.minArea = 5
params.maxArea = 5000
# All other filters disabled

detector = cv2.SimpleBlobDetector_create(params)
```

**Step 3: Test on Reference Images**
```python
for dist in distances:
    img = cv2.imread(f"reference_{dist}.jpg", cv2.IMREAD_GRAYSCALE)
    keypoints = detector.detect(img)
    print(f"{dist}: Detected {len(keypoints)} blobs")

    if len(keypoints) > 0:
        print(f"  Blob sizes: {[kp.size for kp in keypoints]}")

    # Draw and save
    img_with_kp = cv2.drawKeypoints(img, keypoints, None, (0,255,0),
                                     cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    cv2.imwrite(f"detected_{dist}.jpg", img_with_kp)
```

**Step 4: Add Area Constraints**
```python
# Based on observed blob sizes from Step 3
# Example: If sizes are [45, 80, 30] pixels
min_observed = 30
max_observed = 80

params.minArea = int(min_observed * 0.5)  # 50% margin
params.maxArea = int(max_observed * 3.0)  # 3x margin

print(f"Set minArea={params.minArea}, maxArea={params.maxArea}")
detector = cv2.SimpleBlobDetector_create(params)
# Re-test on reference images
```

**Step 5: Enable Shape Filters**
```python
params.filterByCircularity = True
params.minCircularity = 0.6

params.filterByConvexity = True
params.minConvexity = 0.8

params.filterByInertia = True
params.minInertiaRatio = 0.5

detector = cv2.SimpleBlobDetector_create(params)
# Re-test on reference images
```

**Step 6: Test in Real-Time**
```python
while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    keypoints = detector.detect(thresh)

    frame_with_kp = cv2.drawKeypoints(frame, keypoints, None, (0,0,255),
                                       cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imshow("Real-Time Detection", frame_with_kp)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

### 6.5 Final Integration with Existing Project

**Step 1: Review Current Code**
- Read HarryPotterWandcv.py to understand existing tracking approach
- Identify where IR illumination control should be added
- Determine if SimpleBlobDetector improves upon current method

**Step 2: Add IR Control Module**
```python
# ir_control.py
import RPi.GPIO as GPIO

class IRIlluminator:
    def __init__(self, pin=18, frequency=1000):
        self.pin = pin
        self.frequency = frequency
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)

    def set_brightness(self, percent):
        """Set brightness 0-100%"""
        self.pwm.ChangeDutyCycle(max(0, min(100, percent)))

    def on(self, brightness=100):
        """Turn on at specified brightness"""
        self.set_brightness(brightness)

    def off(self):
        """Turn off"""
        self.set_brightness(0)

    def cleanup(self):
        """Cleanup GPIO"""
        self.pwm.stop()
        GPIO.cleanup()
```

**Step 3: Integrate with Main Script**
```python
# Add to HarryPotterWandcv.py

from ir_control import IRIlluminator

# Initialize IR illuminator
ir = IRIlluminator(pin=18)
ir.on(brightness=50)  # Start at 50%

try:
    # Existing wand tracking code here
    # ...

finally:
    # Cleanup on exit
    ir.cleanup()
```

**Step 4: Test Complete System**
1. Power on Raspberry Pi and 12V supply
2. Run HarryPotterWandcv.py
3. Verify IR illumination turns on
4. Test wand tracking with IR LED wand tip
5. Verify spell detection works correctly
6. Test servo, LED, and audio outputs
7. Run extended test (10+ minutes) to check thermal stability

### 6.6 Troubleshooting Guide

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| IR doesn't turn on | Wiring error | Check MOSFET connections, measure voltage |
| IR always on | GPIO not connected/working | Verify GPIO pin number, test with LED |
| IR very dim | Insufficient gate voltage | Use logic-level MOSFET (IRLZ34N) |
| GPIO control doesn't work | No common ground | Connect Pi GND to 12V GND |
| IR flickers | Loose connection | Secure all wire connections |
| MOSFET gets hot | Wrong MOSFET type or short | Check MOSFET rating, inspect for shorts |
| No blob detected | Exposure too dark | Increase ExposureTime or AnalogueGain |
| Multiple false blobs | Reflections | Adjust IR angle, add background subtraction |
| Camera image pinkish | White balance incorrect | Adjust ColourGains in camera config |
| Blob detection slow | High resolution | Reduce resolution to 640x480 |
| Wand trail jittery | Noise in detection | Add Kalman filter or smoothing |
| Power supply voltage drops | Undersized PSU | Use 12V 2A or larger supply |
| Raspberry Pi reboots | Insufficient power | Use official 27W power supply |

---

## 7. Safety Guidelines Summary

### Critical Safety Rules

1. **Never stare directly at 850nm IR LEDs at close range (<50cm)**
2. **Always use fuse protection on 12V supply (2A fast-blow)**
3. **Verify common ground connection before powering on**
4. **Use logic-level MOSFET (Vgs(th) < 3.3V) for GPIO control**
5. **Ensure adequate ventilation for IR board (no sealed enclosures)**
6. **Inspect all connections for exposed wire/shorts before power-up**
7. **Keep 12V wiring away from GPIO pins (risk of damage)**
8. **Monitor IR board temperature during first hour of operation**

### Recommended Operating Parameters

- **IR Duty Cycle:** 50% for typical indoor use
- **Operating Distance:** 1-2.5 meters from camera
- **Mounting Position:** Above or around camera lens, not at eye level
- **Continuous Operation:** Maximum 8 hours, then inspect for heat
- **Maximum Ambient Temperature:** 30°C (IR board may reach 60°C surface temp)

---

## 8. Conclusion

This research document provides comprehensive guidance for integrating an 850nm DC12V 42-LED IR illuminator board with your Interactive Wand Gesture Recognition project. Key takeaways:

1. **850nm is the optimal wavelength** for NoIR camera sensitivity and wand tracking performance
2. **Use MOSFET control (not relay)** for PWM brightness adjustment and silent operation
3. **Separate 12V power supply required** with common ground to Raspberry Pi
4. **Manual camera exposure control is critical** for consistent blob detection
5. **SimpleBlobDetector with tuned parameters** provides reliable wand tip tracking
6. **Eye safety is manageable** at >1m distance with intermittent exposure
7. **Proper positioning (co-axial/ring mount)** minimizes reflections and false positives

**Estimated Implementation Time:**
- Hardware assembly: 2-3 hours
- Camera configuration: 1-2 hours
- Blob detector tuning: 2-4 hours
- Integration with existing code: 2-3 hours
- Testing and refinement: 3-5 hours
- **Total: 10-17 hours**

**Next Steps:**
1. Acquire components from checklist (Section 6.1)
2. Assemble MOSFET control circuit (Section 6.2)
3. Configure camera with manual exposure (Section 6.3)
4. Tune SimpleBlobDetector parameters (Section 6.4)
5. Integrate with existing HarryPotterWandcv.py (Section 6.5)
6. Test complete system and iterate

This integration will significantly improve wand tracking reliability, especially in varying ambient lighting conditions, while adding precise brightness control for optimal computer vision performance.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-22
**Author:** Research Analyst
**Project:** Interactive Wand Gesture Recognition

For questions or clarifications, refer to the documentation URLs in Section 5 or consult the community forums listed in Section 5.3.
