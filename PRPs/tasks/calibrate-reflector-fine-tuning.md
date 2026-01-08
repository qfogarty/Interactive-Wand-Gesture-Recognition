# Task PRP: Calibrate Reflector Fine-Tuning Enhancement

**Status:** COMPLETED
**Priority:** High
**Risk Level:** Low (single-file enhancement, isolated tool)
**Target File:** `calibrate_reflector.py`

---

## Context

### Problem Statement

The `calibrate_reflector.py` interactive calibration tool needs comprehensive fine-tuning across four areas:

1. **Detection Sensitivity** - Wand not detected reliably, false positives, lighting issues
2. **Parameter Adjustment UX** - Keyboard controls awkward, step sizes need refinement
3. **Visual Feedback** - Hard to see what's being detected, need more debug views
4. **Missing Parameters** - Key parameters not exposed (max_area, circularity, MOG2 settings)

### Current Architecture

```yaml
current_file: calibrate_reflector.py
lines: 432
class: ReflectorCalibrator

detection_pipeline:
  1. Convert RGB to grayscale
  2. MOG2 background subtraction
  3. Brightness threshold mask
  4. Combine masks (AND)
  5. Morphological cleanup
  6. SimpleBlobDetector
  7. Best candidate selection
  8. Jump distance validation
  9. Temporal validation

exposed_parameters:
  - brightness_threshold: 180 (W/S keys, ±10)
  - min_threshold: 80 (E/D keys, ±10)
  - min_area: 10 (R/F keys, ±5)
  - max_jump_distance: 100 (T/G keys, ±10)
  - required_frames: 3 (Y/H keys, ±1)

missing_parameters:
  - max_area: 800 (fixed, not tunable)
  - min_circularity: 0.4 (fixed, not tunable)
  - min_inertia_ratio: 0.2 (fixed, not tunable)
  - mog2_history: 120 (fixed, not tunable)
  - mog2_var_threshold: 25 (fixed, not tunable)

current_displays:
  - Main "Calibrator" window with overlay
  - "Detection Mask" window (combined mask only)
```

### Related Files

```yaml
config_integration:
  - config.yaml: Saves settings to detection.reflector section
  - config_loader.py: DotDict access for configuration

production_detector:
  - utils/reflector_detector.py: Uses same pipeline (309 lines)
  - Must maintain parameter compatibility

documentation:
  - docs/CONFIGURATION.md: Lines 425-456 cover reflector calibration
  - docs/REFLECTOR_CALIBRATOR.md: Usage guide
```

### Pattern Reference

```python
# Current keyboard handling pattern (lines 272-320)
def handle_key(self, key):
    if key == ord('w'):
        self.params['brightness_threshold'] = min(255, self.params['brightness_threshold'] + 10)
    elif key == ord('s'):
        self.params['brightness_threshold'] = max(50, self.params['brightness_threshold'] - 10)
    # ... more key handlers

# Current display pattern (lines 228-270)
def draw_overlay(self, frame, gray, mask, point, valid):
    # Status text
    cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    # Parameter list
    for text in params_text:
        cv2.putText(display, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
```

---

## Gotchas

```yaml
gotchas:
  - issue: "MOG2 needs warm-up period"
    fix: "Don't reset bg_subtractor when changing other params"

  - issue: "Blob detector params require recreation"
    fix: "Call create_blob_detector() after param changes"

  - issue: "Key repeat rate varies by OS"
    fix: "Use cv2.waitKey(50) instead of waitKey(1) for smoother control"

  - issue: "Config.yaml reflector section may not exist"
    fix: "Always create nested dicts before writing (already handled)"

  - issue: "min_area too low causes noise spikes"
    fix: "Set minimum bound to 3 (not 1)"
```

---

## Task Breakdown

### Phase 1: Expose Missing Parameters (Priority: High)

#### Task 1.1: Add max_area Parameter

**ACTION** `calibrate_reflector.py`:

```python
# Line ~44 - DEFAULTS dict
- MODIFY: Add max_area to adjustable params (currently fixed at 800)

# Line ~254 - params_text list
- ADD: Display line for max_area with key hint

# Line ~294-303 - handle_key method
- ADD: Key handlers for max_area (suggest: u/j keys, ±50)
```

**VALIDATE**:
```bash
python3 -c "from calibrate_reflector import ReflectorCalibrator; c = ReflectorCalibrator(); print('max_area:', c.params.get('max_area', 'MISSING'))"
# Expected: max_area: 800
```

**ROLLBACK**: `git checkout calibrate_reflector.py`

---

#### Task 1.2: Add min_circularity Parameter

**ACTION** `calibrate_reflector.py`:

```python
# Line ~44 - DEFAULTS dict
- VERIFY: min_circularity is already in DEFAULTS (0.4)

# Line ~254 - params_text list
- ADD: Display line for min_circularity with key hint

# Line ~294 - handle_key method
- ADD: Key handlers for circularity (suggest: i/k keys, ±0.05)
- BOUNDS: min=0.1, max=1.0
```

**VALIDATE**:
```bash
# Verify circularity adjustment persists to config
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
print('circularity:', cfg.get('detection', {}).get('reflector', {}).get('blob_detector', {}).get('min_circularity', 'NOT_SAVED'))
"
```

---

#### Task 1.3: Add MOG2 Parameters

**ACTION** `calibrate_reflector.py`:

```python
# Line ~44 - DEFAULTS dict
- ADD: 'mog2_history': 120
- ADD: 'mog2_var_threshold': 25

# Line ~130-136 - init_bg_subtractor method
- MODIFY: Use self.params instead of hardcoded values

# Line ~254 - params_text list
- ADD: Display lines for MOG2 params

# Line ~294 - handle_key method
- ADD: Key handlers for MOG2 settings
  - mog2_history: o/l keys, ±30 (range: 30-300)
  - mog2_var_threshold: comma/period keys, ±5 (range: 10-100)

# IMPORTANT: MOG2 requires reinitialization when params change
- ADD: self.init_bg_subtractor() call after MOG2 param changes
```

**VALIDATE**:
```bash
# Test MOG2 param loading from config
grep -A5 "mog2:" config.yaml
```

**IF_FAIL**: Ensure config.yaml has reflector.mog2 section

---

#### Task 1.4: Update save_config for New Parameters

**ACTION** `calibrate_reflector.py` lines 329-376:

```python
# In save_config method, add:
- max_area to blob_detector section
- mog2_history to mog2 section
- mog2_var_threshold to mog2 section
```

**VALIDATE**:
```bash
# After running calibrator and pressing Q
grep -E "max_area|mog2" config.yaml
```

---

### Phase 2: Improve Parameter Adjustment UX (Priority: High)

#### Task 2.1: Implement Variable Step Sizes

**ACTION** `calibrate_reflector.py`:

```python
# Add shift key modifier for fine adjustments
# OpenCV key codes:
#   - Shift+key: Different scan code on different OS
#   - Alternative: Use number keys 1-3 to select step size mode

# Proposed approach - Step size multiplier:
# Line ~55 - Add to __init__:
self.step_multiplier = 1  # 1=fine, 2=normal, 5=coarse

# Line ~272 - handle_key method:
# Add mode switching:
elif key == ord('1'):
    self.step_multiplier = 1
    print("Fine adjustment mode (1x)")
elif key == ord('2'):
    self.step_multiplier = 2
    print("Normal adjustment mode (2x)")
elif key == ord('3'):
    self.step_multiplier = 5
    print("Coarse adjustment mode (5x)")

# Modify existing adjustments to use multiplier:
# Example for brightness_threshold:
elif key == ord('w'):
    self.params['brightness_threshold'] = min(255,
        self.params['brightness_threshold'] + 10 * self.step_multiplier)
```

**VALIDATE**: Run calibrator, press 1/2/3 to switch modes, verify step sizes change

---

#### Task 2.2: Add Visual Step Size Indicator

**ACTION** `calibrate_reflector.py` draw_overlay method:

```python
# Line ~263 - Add step size indicator near bottom
mode_names = {1: "FINE", 2: "NORMAL", 5: "COARSE"}
mode_text = f"[1/2/3] Step: {mode_names.get(self.step_multiplier, '?')} ({self.step_multiplier}x)"
cv2.putText(display, mode_text, (w - 200, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
```

---

#### Task 2.3: Improve Key Layout Documentation

**ACTION** `calibrate_reflector.py`:

```python
# Update docstring (lines 8-26) with complete key map:
"""
Controls:
    q - Quit and save settings
    ESC - Quit without saving

    Step size modes:
        1 - Fine mode (1x step)
        2 - Normal mode (2x step)
        3 - Coarse mode (5x step)

    Detection thresholds:
        w/s - Brightness threshold (±10)
        e/d - Min blob threshold (±10)

    Blob size:
        r/f - Min area (±5)
        u/j - Max area (±50)

    Blob shape:
        i/k - Min circularity (±0.05)

    Background subtraction:
        o/l - MOG2 history (±30)
        ,/. - MOG2 variance threshold (±5)

    Tracking:
        t/g - Max jump distance (±10)
        y/h - Required frames (±1)

    Other:
        SPACE - Reset to defaults
        p - Print current settings
        v - Cycle debug views
        m - Toggle mask overlay
"""
```

---

### Phase 3: Enhance Visual Feedback (Priority: High)

#### Task 3.1: Add Multiple Debug Views

**ACTION** `calibrate_reflector.py`:

```python
# Line ~55 - Add to __init__:
self.debug_view_mode = 0  # 0=combined, 1=fg_mask, 2=bright_mask, 3=gray

# Line ~161 - Modify detect_wand to return intermediate masks:
def detect_wand(self, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    fg_mask = self.bg_subtractor.apply(gray)
    _, bright_mask = cv2.threshold(gray, self.params['brightness_threshold'], 255, cv2.THRESH_BINARY)
    combined = cv2.bitwise_and(fg_mask, bright_mask)
    # ... rest of detection

    # Return all masks for debug display
    return gray, fg_mask, bright_mask, combined, best_point, valid_detection

# Line ~272 - handle_key:
elif key == ord('v'):
    self.debug_view_mode = (self.debug_view_mode + 1) % 4
    view_names = ["Combined", "FG Mask (MOG2)", "Brightness Mask", "Grayscale"]
    print(f"Debug view: {view_names[self.debug_view_mode]}")
```

**VALIDATE**: Run calibrator, press 'v' repeatedly, verify view cycling

---

#### Task 3.2: Implement Multi-Window Debug Display

**ACTION** `calibrate_reflector.py` run method (line ~378):

```python
# Replace single "Detection Mask" window with switchable views

# In run() method, modify display logic:
view_names = ["Combined", "FG Mask", "Bright Mask", "Grayscale"]
debug_masks = [combined, fg_mask, bright_mask, gray]
current_debug = debug_masks[self.debug_view_mode]

# Update window title to show current mode
cv2.setWindowTitle("Detection Mask", f"Debug: {view_names[self.debug_view_mode]}")
cv2.imshow("Detection Mask", current_debug)
```

---

#### Task 3.3: Add Mask Overlay Toggle

**ACTION** `calibrate_reflector.py`:

```python
# Line ~55 - Add to __init__:
self.show_mask_overlay = False

# Line ~272 - handle_key:
elif key == ord('m'):
    self.show_mask_overlay = not self.show_mask_overlay
    print(f"Mask overlay: {'ON' if self.show_mask_overlay else 'OFF'}")

# Line ~228 - draw_overlay method, add overlay rendering:
if self.show_mask_overlay and mask is not None:
    # Create semi-transparent overlay
    mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
    mask_rgb = cv2.cvtColor(mask_colored, cv2.COLOR_BGR2RGB)
    display = cv2.addWeighted(display, 0.7, mask_rgb, 0.3, 0)
```

---

#### Task 3.4: Add Detection Statistics Display

**ACTION** `calibrate_reflector.py`:

```python
# Line ~55 - Add tracking stats to __init__:
self.stats = {
    'detections_total': 0,
    'detections_valid': 0,
    'false_starts': 0,  # Detections that didn't reach required_frames
    'fps': 0.0,
    'last_frame_time': time.time()
}

# Update stats in detect_wand:
if best_point:
    self.stats['detections_total'] += 1
if valid_detection:
    self.stats['detections_valid'] += 1

# Calculate FPS:
now = time.time()
self.stats['fps'] = 1.0 / (now - self.stats['last_frame_time'] + 0.001)
self.stats['last_frame_time'] = now

# Draw stats in draw_overlay (bottom right area):
stats_text = [
    f"FPS: {self.stats['fps']:.1f}",
    f"Valid: {self.stats['detections_valid']}",
    f"Total: {self.stats['detections_total']}",
]
y = h - 80
for text in stats_text:
    cv2.putText(display, text, (w - 120, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
    y += 15
```

---

### Phase 4: Improve Detection Sensitivity (Priority: Medium)

#### Task 4.1: Add Adaptive Brightness Suggestion

**ACTION** `calibrate_reflector.py`:

```python
# Add method to analyze frame brightness:
def suggest_brightness_threshold(self, gray):
    """Analyze frame and suggest optimal brightness threshold."""
    mean_brightness = np.mean(gray)
    max_brightness = np.max(gray)

    # Suggest threshold at 80% of max brightness
    suggested = int(max_brightness * 0.8)

    return suggested, mean_brightness, max_brightness

# In draw_overlay, show suggestion:
suggested, mean_br, max_br = self.suggest_brightness_threshold(gray)
cv2.putText(display, f"Suggested brightness: {suggested} (mean:{mean_br:.0f} max:{max_br})",
            (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 255), 1)
```

---

#### Task 4.2: Add Auto-Calibrate Feature

**ACTION** `calibrate_reflector.py`:

```python
# Add to handle_key:
elif key == ord('a'):
    self.auto_calibrate()

def auto_calibrate(self):
    """Attempt automatic brightness calibration."""
    print("Auto-calibrating... Wave wand now!")

    # Collect 30 frames of data
    brightness_samples = []
    for _ in range(30):
        frame = self.camera.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        fg_mask = self.bg_subtractor.apply(gray)

        # Find bright moving pixels
        moving_bright = cv2.bitwise_and(fg_mask, gray)
        if np.any(moving_bright > 0):
            bright_pixels = moving_bright[moving_bright > 50]
            if len(bright_pixels) > 0:
                brightness_samples.append(np.mean(bright_pixels))

        time.sleep(0.05)

    if brightness_samples:
        # Set threshold to 70% of detected brightness
        suggested = int(np.percentile(brightness_samples, 30))
        self.params['brightness_threshold'] = max(50, min(255, suggested))
        print(f"Auto-calibrated brightness_threshold: {self.params['brightness_threshold']}")
    else:
        print("No wand movement detected - try waving wand more actively")
```

---

#### Task 4.3: Add Noise Floor Analysis

**ACTION** `calibrate_reflector.py`:

```python
# Add noise floor tracking to detect_wand or as separate method:
def analyze_noise_floor(self, combined_mask):
    """Count non-zero pixels when nothing should be detected."""
    noise_pixels = np.count_nonzero(combined_mask)
    noise_percentage = (noise_pixels / combined_mask.size) * 100
    return noise_pixels, noise_percentage

# Display in overlay if noise is high:
noise_px, noise_pct = self.analyze_noise_floor(combined)
if noise_pct > 1.0:  # More than 1% noise
    cv2.putText(display, f"WARNING: High noise ({noise_pct:.1f}%)",
                (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
```

---

### Phase 5: Final Integration & Testing (Priority: High)

#### Task 5.1: Update load_current_config

**ACTION** `calibrate_reflector.py` lines 64-98:

```python
# Add loading for all new parameters:
def load_current_config(self):
    # ... existing code ...

    # Add MOG2 loading
    mog2 = reflector.get('mog2', {})
    if 'history' in mog2:
        self.params['mog2_history'] = mog2['history']
    if 'var_threshold' in mog2:
        self.params['mog2_var_threshold'] = mog2['var_threshold']
```

---

#### Task 5.2: Sync save_config with All Parameters

**ACTION** `calibrate_reflector.py` save_config method:

```python
# Ensure all params save correctly:
def save_config(self):
    # ... existing structure creation ...

    # Add blob_detector params
    reflector['blob_detector']['max_area'] = self.params['max_area']
    reflector['blob_detector']['min_circularity'] = self.params['min_circularity']
    reflector['blob_detector']['min_inertia_ratio'] = self.params['min_inertia_ratio']

    # Add mog2 section if not exists
    if 'mog2' not in reflector:
        reflector['mog2'] = {}
    reflector['mog2']['history'] = self.params['mog2_history']
    reflector['mog2']['var_threshold'] = self.params['mog2_var_threshold']
```

---

#### Task 5.3: Validate Config Compatibility

**VALIDATE** compatibility with production detector:

```bash
# Test that saved config works with ReflectorDetector
python3 -c "
from utils.reflector_detector import ReflectorDetector
from config_loader import get_config
config = get_config()
detector = ReflectorDetector(config)
detector.initialize()
print('ReflectorDetector loaded config successfully')
"
```

**IF_FAIL**:
- Check parameter names match between calibrator and detector
- Ensure nested config structure is identical

---

#### Task 5.4: Update Documentation

**ACTION** `docs/REFLECTOR_CALIBRATOR.md`:

- Update keyboard controls table with new keys
- Document debug view cycling
- Add auto-calibrate instructions
- Document step size modes

**VALIDATE**:
```bash
# Ensure doc reflects actual controls
grep -E "[WASD]|Step|Debug|Auto" docs/REFLECTOR_CALIBRATOR.md
```

---

## Validation Strategy

### Unit Validation

After each task:
```bash
# Syntax check
python3 -m py_compile calibrate_reflector.py

# Import test
python3 -c "from calibrate_reflector import ReflectorCalibrator; print('OK')"
```

### Integration Validation

After Phase completion:
```bash
# Full round-trip test (requires Pi with camera)
# 1. Run calibrator
python3 calibrate_reflector.py

# 2. Adjust params
# 3. Press Q to save

# 4. Verify config updated
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
refl = cfg.get('detection', {}).get('reflector', {})
print('brightness_threshold:', refl.get('brightness_threshold'))
print('blob_detector:', refl.get('blob_detector'))
print('mog2:', refl.get('mog2'))
"

# 5. Verify production detector loads config
python3 -c "
from utils.reflector_detector import ReflectorDetector
from config_loader import get_config
config = get_config()
detector = ReflectorDetector(config)
detector.initialize()
"
```

### Performance Validation

```bash
# Monitor FPS during calibration (should be displayed on screen)
# Target: 25+ FPS for smooth interaction
```

---

## Rollback Strategy

```bash
# Per-file rollback
git checkout calibrate_reflector.py

# Full rollback
git checkout HEAD -- calibrate_reflector.py config.yaml docs/REFLECTOR_CALIBRATOR.md
```

---

## Summary

### New Keyboard Layout

| Key | Parameter | Step | Range |
|-----|-----------|------|-------|
| W/S | brightness_threshold | ±10×mult | 50-255 |
| E/D | min_threshold | ±10×mult | 20-200 |
| R/F | min_area | ±5×mult | 3-100 |
| U/J | max_area | ±50×mult | 100-2000 |
| I/K | min_circularity | ±0.05×mult | 0.1-1.0 |
| O/L | mog2_history | ±30×mult | 30-300 |
| ,/. | mog2_var_threshold | ±5×mult | 10-100 |
| T/G | max_jump_distance | ±10×mult | 20-300 |
| Y/H | required_frames | ±1 | 1-10 |
| 1/2/3 | step_multiplier | mode | 1x/2x/5x |
| V | debug_view | cycle | 0-3 |
| M | mask_overlay | toggle | on/off |
| A | auto_calibrate | action | - |
| SPACE | reset | action | defaults |
| P | print | action | console |
| Q | save_quit | action | - |
| ESC | quit | action | no save |

### Files Modified

- `calibrate_reflector.py` - Main calibrator (major changes)
- `config.yaml` - Will have expanded reflector section
- `docs/REFLECTOR_CALIBRATOR.md` - Documentation update

### Dependencies

- OpenCV (cv2) - already installed
- NumPy - already installed
- PyYAML - already installed
- picamera2 - Pi-only, already required

---

## Quality Checklist

- [x] All new parameters exposed with keyboard controls
- [x] Step size multiplier working (1/2/3 keys)
- [x] Debug view cycling working (V key)
- [x] Mask overlay toggle working (M key)
- [x] Auto-calibrate feature working (A key)
- [x] Noise floor warning displayed when high
- [x] FPS and detection stats shown
- [x] All params save to config.yaml correctly
- [x] Config loads into ReflectorDetector without errors
- [x] Documentation updated with new controls
- [x] No regressions in existing functionality

## Execution Summary

**Completed:** 2026-01-09

All phases implemented successfully:
- Phase 1: Added max_area, min_circularity, min_inertia_ratio, mog2_history, mog2_var_threshold
- Phase 2: Added step multiplier (1/2/3 keys), improved UX
- Phase 3: Added debug view cycling (V), mask overlay (M), stats display
- Phase 4: Added auto-calibrate (A), noise analysis, brightness suggestions
- Phase 5: Updated docs/CONFIGURATION.md with comprehensive keyboard reference
