# TASK PRP: Verify LED Setup & GPIO Documentation

**Task:** Verify we have everything needed to run LEDs and clarify GPIO pin documentation for LEDs and IR lights.

**Reference:** https://core-electronics.com.au/guides/raspberry-pi/fully-addressable-rgb-raspberry-pi/

---

## Context

### External Reference Findings

From the Core Electronics guide:
- **GPIO Options for WS2812B:** GPIO 18 (PWM), GPIO 21, GPIO 12, GPIO 10 (SPI)
- **Libraries:** `rpi_ws281x`, `adafruit-circuitpython-neopixel`, `adafruit-blinka`
- **Critical Limitation:** "Due to changes in GPIO controls, Neopixels are not currently working with the Raspberry Pi 5" using traditional methods
- **Power:** <30 LEDs can power from Pi; >30 LEDs require external 5V 4A PSU with common ground

### Current Project Approach (Pi 5 Compatible)

This project correctly uses the **SPI method** via `pi5neo` library, which IS compatible with Raspberry Pi 5.

```yaml
# Current config.yaml
hardware:
  led:
    enabled: false
    count: 30
    timing: 800                    # WS2812B timing
    spi_device: "/dev/spidev0.0"   # SPI0 interface
    gpio_pin: 19                   # GPIO10/MOSI (Pin 19)
```

---

## Codebase Analysis

### GPIO Pin Assignments

| Function | Physical Pin | GPIO (BCM) | Config Key | Status |
|----------|-------------|------------|------------|--------|
| LED Strip Data (SPI MOSI) | **Pin 19** | GPIO10 | `hardware.led.gpio_pin` | Correct |
| Servo PWM | Pin 32 | GPIO12 | `hardware.servo.gpio_pin` | Optional |
| IR Illuminator PWM | **Pin 12** | GPIO18 | `hardware.ir_illuminator.gpio_pin` | Optional |

### Files Referencing GPIO

| File | LED GPIO | IR GPIO | Servo GPIO |
|------|----------|---------|------------|
| `config.yaml` | Pin 19 (GPIO10) | Pin 12 (GPIO18) | GPIO12 |
| `config_builder.py` | Pin 19 hardcoded | GPIO18 | GPIO12 |
| `TECHNICAL_GUIDE.md` | GPIO10 (MOSI) | GPIO18 (Pin 12) | GPIO12 (Pin 32) |
| `CONFIGURATION.md` | GPIO10/MOSI | GPIO18 | GPIO12 |
| `WIRING_DIAGRAMS.md` | Pin 19 | GPIO18 (Pin 12) | - |

---

## Identified Documentation Gaps

### 1. Pin Numbering Confusion
**Issue:** Mixed use of GPIO numbers and physical pin numbers without clear mapping.

**Example Confusion:**
- `gpio_pin: 19` in config → This is GPIO10/MOSI at Physical Pin 19
- `gpio_pin: 18` for IR → This is GPIO18 at Physical Pin 12
- Config uses GPIO BCM numbers but stores physical pin for LED

**Fix Required:** Add clear pin reference table to documentation.

### 2. SPI Method Not Explained
**Issue:** Config says `gpio_pin: 19` but note says "documentation only - uses MOSI".

**Reality:** The SPI method doesn't use direct GPIO control. The physical pin 19 (GPIO10) is the MOSI line for SPI0.

**Fix Required:** Clarify that LED control uses SPI, not GPIO PWM.

### 3. Pi 5 Specificity Not Highlighted
**Issue:** Documentation mentions Pi 5 but doesn't explicitly warn that traditional rpi_ws281x methods won't work.

**Fix Required:** Add clear compatibility notice.

### 4. Missing Dependencies Check
**Issue:** No verification that `pi5neo` is installed before LED operations.

**Current State:** `install.sh` line 97 installs it: `pip3 install pi5neo --break-system-packages`

---

## Requirements Verification

### LED Strip Requirements Checklist

| Requirement | Status | Location |
|-------------|--------|----------|
| `pi5neo` library installed | Check install.sh line 97 | `pip3 install pi5neo` |
| SPI enabled in config.txt | Check install.sh line 109-115 | `dtparam=spi=on` |
| User in `spi` group | Check install.sh line 128 | `usermod -a -G spi` |
| SPI device exists | Check hardware_checks.py | `/dev/spidev0.0` |
| External 5V PSU for >30 LEDs | Documentation only | TECHNICAL_GUIDE.md |
| Common ground between Pi and PSU | Documentation only | TECHNICAL_GUIDE.md |

### IR Illuminator Requirements Checklist

| Requirement | Status | Location |
|-------------|--------|----------|
| `gpiozero` installed | Check install.sh | System package |
| User in `gpio` group | Check install.sh line 128 | `usermod -a -G gpio` |
| MOSFET circuit for PWM control | Documentation only | WIRING_DIAGRAMS.md |
| 12V PSU for external IR board | Documentation only | TECHNICAL_GUIDE.md |

---

## Task Breakdown

### Task 1: Create GPIO Reference Table
**Action:** Add clear GPIO reference to `CONFIGURATION.md`

**Changes:**
```markdown
## GPIO Pin Reference

| Function | Physical Pin | GPIO (BCM) | Interface | Config Key |
|----------|-------------|------------|-----------|------------|
| LED Strip Data | 19 | GPIO10 | SPI0 MOSI | `hardware.led.spi_device` |
| Servo Motor | 32 | GPIO12 | PWM | `hardware.servo.gpio_pin` |
| IR Illuminator | 12 | GPIO18 | PWM | `hardware.ir_illuminator.gpio_pin` |

**Note:** LED strip uses SPI interface, not direct GPIO. The `gpio_pin` setting is informational only.
```

**Validate:** Read updated doc, verify pin mappings are correct
**Rollback:** Git revert

---

### Task 2: Update LED Section in CONFIGURATION.md
**Action:** Clarify SPI method and remove misleading gpio_pin reference

**File:** `docs/CONFIGURATION.md` lines 161-178

**Current:**
```yaml
gpio_pin: 19                 # GPIO10/MOSI for Pi 5 (Pin 19)
```
**Proposed:**
```yaml
# Note: LED uses SPI interface (Pin 19 = GPIO10/MOSI)
# The gpio_pin field is for documentation only
```

**Validate:** Ensure config still loads correctly
**Rollback:** Git revert

---

### Task 3: Add Pi 5 Compatibility Notice
**Action:** Add explicit warning about Pi 5 requirements

**File:** `docs/TECHNICAL_GUIDE.md` (new section or update existing)

**Content:**
```markdown
### Raspberry Pi 5 Compatibility

**Important:** This project uses the SPI-based `pi5neo` library for LED control.
Traditional PWM methods (`rpi_ws281x`, `adafruit-neopixel`) do NOT work on Pi 5
due to RP1 chipset changes.

**Required:**
- Raspberry Pi 5 with SPI enabled (`dtparam=spi=on`)
- LED strip connected to Pin 19 (GPIO10/MOSI)
- `pi5neo` library (installed automatically by install.sh)

**Not Compatible:**
- Raspberry Pi 4 and earlier (requires different wiring and libraries)
- Traditional GPIO18 PWM method
```

**Validate:** Review technical accuracy
**Rollback:** Git revert

---

### Task 4: Update config.yaml Comments
**Action:** Add clarifying comments to config

**File:** `config.yaml` lines 9-16

**Current:**
```yaml
hardware:
  # LED Strip Configuration
  led:
    enabled: false
    count: 30
    timing: 800
    spi_device: "/dev/spidev0.0"
    gpio_pin: 19
```

**Proposed:**
```yaml
hardware:
  # LED Strip Configuration (WS2812B via SPI)
  # Pi 5 uses SPI method - connect DIN to Pin 19 (GPIO10/MOSI)
  # Traditional GPIO18 PWM method does NOT work on Pi 5
  led:
    enabled: false  # Set to true when LED strip is connected
    count: 30       # Number of LEDs in your strip
    timing: 800     # 800 for WS2812B, 400 for WS2811
    spi_device: "/dev/spidev0.0"  # SPI0 device path
    gpio_pin: 19    # Physical Pin 19 = GPIO10/MOSI (documentation only)
```

**Validate:** `python3 -c "from config_loader import get_config; print(get_config().hardware.led)"`
**Rollback:** Git revert

---

### Task 5: Verify Installation Script
**Action:** Confirm all LED requirements are installed

**File:** `install.sh`

**Check Items:**
1. Line 97: `pi5neo` installation
2. Line 109-115: SPI enablement
3. Line 128: User group membership (spi, gpio)

**Validation Command:**
```bash
# Check SPI device exists
ls -la /dev/spidev0.0

# Check user groups
groups $USER | grep -E "(spi|gpio)"

# Check pi5neo installed
python3 -c "from pi5neo import Pi5Neo; print('OK')"
```

**Status:** APPEARS COMPLETE - verify on actual Pi 5

---

## Summary: Do We Have Everything?

### For LED Strip: YES (on Raspberry Pi 5)

| Component | Status | Notes |
|-----------|--------|-------|
| Library (`pi5neo`) | Installed by install.sh | SPI-based, Pi 5 native |
| SPI Enabled | Configured by install.sh | `dtparam=spi=on` |
| Permissions | Configured by install.sh | User in `spi` group |
| Wiring | Documented | Pin 19 (GPIO10/MOSI) → DIN |
| Power | Documented | External 5V PSU for >30 LEDs |

### For IR Illuminator: YES (optional feature)

| Component | Status | Notes |
|-----------|--------|-------|
| Library (`gpiozero`) | System package | PWM control |
| Permissions | Configured by install.sh | User in `gpio` group |
| Wiring | Documented | GPIO18 (Pin 12) via MOSFET |
| Power | Documented | 12V external PSU |

### Documentation Improvements Needed

1. **Add GPIO reference table** - Map physical pins to GPIO numbers
2. **Clarify SPI vs GPIO** - LED uses SPI, not direct GPIO
3. **Add Pi 5 warning** - Traditional methods don't work
4. **Update config comments** - Make gpio_pin purpose clear

---

## GPIO Quick Reference (Final)

### LED Strip (WS2812B)
```
Physical Pin 19 → GPIO10 (MOSI) → LED Strip DIN

Interface: SPI0 (/dev/spidev0.0)
Library: pi5neo
NOT GPIO-controlled - uses SPI data stream
```

### Servo Motor (Optional)
```
Physical Pin 32 → GPIO12 → Servo Signal Wire

Interface: Hardware PWM
Library: gpiozero + pigpio
```

### IR Illuminator (Optional)
```
Physical Pin 12 → GPIO18 → MOSFET Gate → IR Board

Interface: Software PWM
Library: gpiozero
Requires: MOSFET circuit + 12V PSU
```

---

## Implementation Priority

1. **Task 4** - Update config.yaml comments (immediate clarity)
2. **Task 1** - Add GPIO reference table (user documentation)
3. **Task 3** - Add Pi 5 compatibility notice (prevent confusion)
4. **Task 2** - Update CONFIGURATION.md (comprehensive docs)
5. **Task 5** - Verify installation (testing)

---

## Acceptance Criteria

- [x] Users can determine which pin to use for LED strip from documentation
- [x] Users understand Pi 5 uses SPI method, not GPIO PWM
- [x] GPIO/Pin number confusion is resolved with clear reference table
- [x] IR illuminator pin (GPIO18/Pin 12) is clearly documented
- [x] All references in code match documentation

---

## Execution Summary (Completed 2026-01-08)

### Tasks Completed

1. **Task 4: config.yaml** - Added detailed comments explaining SPI method, Pi 5 requirements, and GPIO/Pin mappings
2. **Task 1: GPIO Reference Table** - Added comprehensive GPIO pin reference section to CONFIGURATION.md with visual pin layout
3. **Task 3: Pi 5 Compatibility** - Added dedicated section in TECHNICAL_GUIDE.md explaining why SPI is required
4. **Task 2: LED Section Update** - Enhanced LED configuration section with wiring diagram and troubleshooting
5. **Task 5: Installation Verification** - Confirmed install.sh includes all requirements (pi5neo, SPI enablement, group permissions)

### Files Modified

- `config.yaml` - Enhanced comments for all GPIO-related settings
- `docs/CONFIGURATION.md` - Added GPIO Pin Reference section and updated LED section
- `docs/TECHNICAL_GUIDE.md` - Added Raspberry Pi 5 Compatibility section
