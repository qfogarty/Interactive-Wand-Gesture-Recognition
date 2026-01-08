# IR Illuminator Wiring Diagrams
## Supplementary Document for Hardware Assembly

**Project:** Interactive Wand Gesture Recognition
**Component:** 850nm IR Illuminator Boards (5V and 12V Options)
**Date:** 2025-11-22
**Updated:** 2026-01-09

---

## IR Illuminator Options Summary

| Option | Voltage | Complexity | Best For |
|--------|---------|------------|----------|
| **Option A: 5V IR Board** | DC 5V | Simple | Beginners, 1-2m range |
| **Option B: 12V IR Board** | DC 12V | Moderate | Larger spaces, 2-5m range |

---

## Option A: 5V IR Board (Simple Setup)

### Recommended Board
- **Specs:** 850nm, DC 5V, 90° beam angle
- **Example:** CCTV IR illuminator boards (commonly available on AliExpress)
- **Effective range:** 1-2 meters

### Diagram A1: Always-On 5V IR (Simplest)

```
Raspberry Pi 5                          5V IR LED Board
┌────────────────────┐                  ┌──────────────────┐
│                    │                  │   ●  ●  ●  ●     │
│  5V Power (Pin 2) ─┼──────────────────┤── IR+ (Red)      │
│         or Pin 4   │                  │                  │
│                    │                  │   850nm LEDs     │
│  GND (Pin 6, 9,   ─┼──────────────────┤── IR- (Black)    │
│   14, 20, 25, 30)  │                  │                  │
│                    │                  └──────────────────┘
└────────────────────┘

Connections:
1. Pi 5V (Pin 2 or 4) → IR Board + (Red wire)
2. Pi GND (any GND pin) → IR Board - (Black wire)

Notes:
- No external power supply needed
- IR LEDs always on when Pi is powered
- Simple 2-wire connection
- Best for reflector wand tracking at close range
```

### Diagram A2: GPIO-Controlled 5V IR (On/Off Switching)

```
Raspberry Pi 5                          5V IR LED Board
┌────────────────────┐                  ┌──────────────────┐
│                    │                  │   ●  ●  ●  ●     │
│  5V Power (Pin 2) ─┼──────────────────┤── IR+ (Red)      │
│                    │                  │                  │
│  GPIO 18 (Pin 12) ─┼──[1kΩ]──┐        │   850nm LEDs     │
│                    │         │        │                  │
│  GND (Pin 6) ──────┼────┬────┘        │                  │
│                    │    │             └────────┬─────────┘
└────────────────────┘    │                      │
                          │                      │ IR- (Black)
                    ┌─────▼─────┐                │
                    │    NPN    │                │
                    │ Transistor│◄───────────────┘
                    │ (2N2222)  │
                    └─────┬─────┘
                          │
                         GND

Component Details:
- Q1: NPN transistor (2N2222A, BC547, or similar)
- R1: 1kΩ resistor (current limiting for base)

Connections:
1. Pi 5V (Pin 2) → IR Board + (Red)
2. Pi GPIO18 (Pin 12) → 1kΩ resistor → Transistor Base
3. IR Board - (Black) → Transistor Collector
4. Transistor Emitter → GND
5. Pi GND → Transistor Emitter (common ground)

Python Control:
  import RPi.GPIO as GPIO
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(18, GPIO.OUT)
  GPIO.output(18, GPIO.HIGH)  # IR ON
  GPIO.output(18, GPIO.LOW)   # IR OFF
```

### Diagram A3: Raspberry Pi 5 GPIO Pinout (5V IR Relevant Pins)

```
Raspberry Pi 5 GPIO Header (40-pin)
Relevant pins for 5V IR illuminator

     3.3V  [ 1] [ 2]  5V      ← Use for IR+ (up to ~300mA)
           [ 3] [ 4]  5V      ← Alternate 5V
           [ 5] [ 6]  GND     ← Use for IR-
           [ 7] [ 8]
       GND [ 9] [10]
           [11] [12]  GPIO18  ← Use for switching control
           [13] [14]  GND
           [15] [16]
           [17] [18]
           [19] [20]  GND
           ...

Power Budget Note:
- Pi 5 can supply ~1A total from 5V pins (with proper PSU)
- Typical 5V IR board draws 100-300mA
- Safe for direct connection if using official 27W PSU
```

### 5V IR Board Configuration

```yaml
# config.yaml for 5V IR board

hardware:
  ir_illuminator:
    enabled: true      # Set to true for GPIO control
    gpio_pin: 18       # GPIO18 (Pin 12)
    voltage: 5         # 5V board indicator

  camera:
    exposure_time: 10000   # May need slightly higher for 5V boards
    analogue_gain: 6.0     # Adjust based on IR brightness
```

---

## Option B: 12V IR Board (Higher Power)

For larger spaces requiring more IR illumination power.

---

## Diagram 1: Basic MOSFET Control Circuit (12V)

```
Raspberry Pi 5                              12V Power Supply
┌────────────────┐                          ┌──────────────┐
│                │                          │   AC/DC      │
│    GPIO 18 ────┼──┬─[1kΩ]───┬───────> G  │   Adapter    │
│    (3.3V PWM)  │  │          │         a  │   12V 2A     │
│                │  │          │         t  │              │
│      GND ──────┼──┼──────────┼───┬───> S  │  (+) ────────┼─── +12V (Red)
│                │  │          │   │     o  │              │
│                │  │      [10kΩ]  │     u  │  (-) ────────┼─── GND (Black)
│                │  │          │   │     r  │              │
└────────────────┘  │          │   │     c  └──────────────┘
                    │          │   │     e              │
                    │          └───┴────────────┐       │
                    │                       │   │       │
                    │                 N-Ch MOSFET       │
                    │                 (IRLZ34N)         │
                    │                       │           │
                    │                       D           │
                    │                       r           │
                    │                       a           │
                    │                       i ───────┐  │
                    │                       n        │  │
                    │                                │  │
IR LED Board        │                                │  │
┌──────────────┐   │                                │  │
│              │   │                                │  │
│   LED Array  │   │                                │  │
│   42 LEDs    │   │                                │  │
│              │   │                                │  │
│   (+) ───────┼───┴────────────────────────────────┘  │
│              │                                        │
│   (-) ───────┼────────────────────────────────────────┘
│              │
└──────────────┘

Component Values:
- R1 (Gate protection): 1kΩ, 1/4W
- R2 (Pull-down, optional): 10kΩ, 1/4W
- Q1: IRLZ34N or IRLZ44N (logic-level N-channel MOSFET)
- Fuse: 2A fast-blow (recommended, not shown)
```

---

## Diagram 2: Complete System with Fuse Protection

```
12V Power Supply
┌─────────────────────┐
│  AC/DC Adapter      │
│  Input: 100-240VAC  │
│  Output: 12V 2A DC  │
│                     │
│  (+) ───────────────┼───┬─── +12V Rail (Red)
│                     │   │
│  (-) ───────────────┼───┴─── GND Rail (Black)
└─────────────────────┘   │
                          │
         ┌────────────────┴────────────────┐
         │                                  │
    [2A Fuse]                              │
         │                                  │
         │  ┌──────────────────────────┐   │
         └──┤  IR LED Board            │   │
            │  850nm, 42 LEDs          │   │
            │  LED+ (Red)              │   │
            │                          │   │
            │  LED- (Black) ───────────┼───┼─── To MOSFET Drain
            └──────────────────────────┘   │
                                            │
                                            │
Raspberry Pi 5                              │
┌───────────────────┐                       │
│                   │                       │
│  GPIO 18 ─────────┼── [1kΩ] ─── MOSFET Gate
│  (BCM numbering)  │                  │
│                   │              [10kΩ]
│  GND Pin 6 ───────┼──────┬────────┴─── MOSFET Source
│                   │      │                    │
└───────────────────┘      └────────────────────┴─── GND Rail
                                                      (Common Ground)
```

---

## Diagram 3: Optional - Dual Power Supply System

For powering both Raspberry Pi 5 and IR board from single source:

```
Single 12V 5A Power Supply
┌────────────────────────┐
│   AC/DC Adapter        │
│   Input: 100-240VAC    │
│   Output: 12V 5A (60W) │
│                        │
│   (+) ─────────────────┼──┬─── +12V Rail
│                        │  │
│   (-) ─────────────────┼──┴─── GND Rail
└────────────────────────┘  │
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         │            [2A Fuse]                │
         │                  │                  │
         │             IR LED Board            │
         │             LED+ ────┐              │
         │             LED- (to MOSFET)        │
         │                      │              │
    ┌────▼──────┐               │              │
    │ DC-DC Buck│               │              │
    │ Converter │               │              │
    │ 12V → 5V  │               │              │
    │ 5A Output │               │              │
    │           │               │              │
    │ IN+ ──────┴───────────────┘              │
    │ IN- ──────────────────────────────────────┘
    │           │
    │ OUT+ ─────┼──── To Raspberry Pi 5 GPIO Pin 2 (5V)
    │ OUT- ─────┼──── To Raspberry Pi 5 Pin 6 (GND)
    └───────────┘

CRITICAL: This method bypasses USB-PD negotiation
         Add PSU_MAX_CURRENT=5000 to /boot/config.txt
         Use buck converter rated for continuous 5A
         Example: LM2596 adjustable step-down module
```

---

## Diagram 4: Breadboard Layout (Top View)

```
Breadboard Layout:
═══════════════════════════════════════════════════════════
Power Rails:
(+) ─────────────────────────────────────────────── +12V
(-) ───────────────────────────────────────────────  GND

                Component Area
  j ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  i └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  h ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  g └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  f ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  e └─┴G┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  d ┌─┬a┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  c └─┴t┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  b ┌─┬e┬─┬1┬k┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  a └─┴─┴─┴k┴Ω┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
═══════════════════════════════════════════════════════════
  - ┌─┬D┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴r┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬a┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴i┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬n┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴─┴─┴1┴0┴k┴Ω┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴S┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬o┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴u┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬r┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┴─┴─┴─┴─┴─┴─┴─┴─┴─┐
  - └─┴c┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
  - ┌─┬e┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  - └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

═══════════════════════════════════════════════════════════
Power Rails:
(+) ─────────────────────────────────────────────── +12V
(-) ───────────────────────────────────────────────  GND

Connections:
1. MOSFET (TO-220 package, legs facing you):
   - Left leg (Gate) → Row e2
   - Middle leg (Drain) → Row d2
   - Right leg (Source) → Row c2

2. 1kΩ resistor (brown-black-red):
   - One end → Row b4 (connects to Gate via row b2-e2)
   - Other end → Jumper wire to GPIO 18

3. 10kΩ resistor (brown-black-orange):
   - One end → Row b5 (connects to Gate)
   - Other end → GND rail (connects to Source)

4. Jumper wires:
   - GPIO 18 → Breadboard b4 (via 1kΩ resistor)
   - Pi GND → Breadboard GND rail
   - 12V+ rail → IR Board LED+
   - MOSFET Drain (d2) → IR Board LED-
   - MOSFET Source (c2) → GND rail
   - 12V GND → Breadboard GND rail
```

---

## Diagram 5: Raspberry Pi 5 GPIO Pinout (Relevant Pins)

```
Raspberry Pi 5 GPIO Header (40-pin)
View from top (USB ports facing down)

     3.3V  [ 1] [ 2]  5V      ← Power (do not use for IR)
     GPIO2 [ 3] [ 4]  5V
     GPIO3 [ 5] [ 6]  GND     ← Connect to 12V GND (common ground)
     GPIO4 [ 7] [ 8]  GPIO14
       GND [ 9] [10]  GPIO15
    GPIO17 [11] [12]  GPIO18  ← Use for IR PWM control
    GPIO27 [13] [14]  GND
    GPIO22 [15] [16]  GPIO23
      3.3V [17] [18]  GPIO24
    GPIO10 [19] [20]  GND
     GPIO9 [21] [22]  GPIO25
    GPIO11 [23] [24]  GPIO8
       GND [25] [26]  GPIO7
     GPIO0 [27] [28]  GPIO1
     GPIO5 [29] [30]  GND
     GPIO6 [31] [32]  GPIO12
    GPIO13 [33] [34]  GND
    GPIO19 [35] [36]  GPIO16
    GPIO26 [37] [38]  GPIO20
       GND [39] [40]  GPIO21

Recommended Pins for IR Control:
- GPIO 18 (Pin 12): Hardware PWM0 ← PRIMARY CHOICE
- GPIO 12 (Pin 32): Hardware PWM0 (alternative)
- GPIO 13 (Pin 33): Hardware PWM1 (alternative)

Ground Options (any):
- Pin 6, 9, 14, 20, 25, 30, 34, 39

Note: Use BCM numbering in Python (GPIO.setmode(GPIO.BCM))
```

---

## Diagram 6: MOSFET Package Pinout (TO-220)

```
IRLZ34N / IRLZ44N / IRL540N Package

View from front (metal tab facing away):

    ┌─────────────┐
    │             │  ← Metal heatsink tab (connected to Drain)
    │   IRLZ34N   │
    │             │
    └──┬───┬───┬──┘
       │   │   │
       │   │   │
       G   D   S     ← Pin identification
       a   r   o
       t   a   u
       e   i   r
           n   c
               e

Connection Summary:
- Gate   → 1kΩ resistor → GPIO 18
- Drain  → IR LED Board (-)
- Source → GND (common ground with Pi and 12V supply)

CRITICAL: Verify pinout with datasheet for your specific MOSFET.
         Some MOSFETs have different pin arrangements!
```

---

## Diagram 7: IR LED Board Connection Detail

```
Typical 42-LED IR Board (Top View)

┌───────────────────────────────────────┐
│  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  │
│                                       │
│  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  │
│                                       │
│  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  │  ← 850nm IR LEDs
│                                       │
│  ●  ●  ●  ●  ●  ●                    │
│                                       │
│  (+) ──────────────────────  LED+    │  ← Red wire to +12V
│                                       │
│  (-) ──────────────────────  LED-    │  ← Black wire to MOSFET Drain
│                                       │
└───────────────────────────────────────┘

Typical Specifications:
- Voltage: DC 12V
- Current: 150-400mA (depending on LED type)
- Power: 2-5W (typical for standard LEDs)
- Wavelength: 850nm ±10nm
- Beam Angle: 60-120 degrees

Polarity Check:
- Use multimeter in diode test mode
- Red probe to (+), black to (-): LEDs should emit (faint red glow)
- Reverse: No glow
- If incorrect: LEDs will not light and may be damaged
```

---

## Diagram 8: Camera Mounting Configurations

### Configuration A: Ring Mount (Optimal)

```
Side View:

        IR LED Board (ring/circular)
              ____
          ___/    \___
         /   Camera   \
        |  ┌────────┐  |
        |  │ NoIR   │  |
        |  │ Camera │  |
        |  └────────┘  |
         \___  Lens  __/
             \______/

Top View:

    ●       ●       ●       ●
        ┌───────────┐
    ●   │           │   ●
        │  Camera   │
    ●   │   Lens    │   ●
        │           │
    ●   └───────────┘   ●
    ●       ●       ●       ●

Advantages:
- Even illumination (no shadows)
- Co-axial with optical axis
- Minimal reflections
- Professional appearance

Distance: 2-5cm from lens center
```

### Configuration B: Top Mount

```
Side View:

        ┌──────────────┐
        │ IR LED Board │  ← 15-30 degree angle
        │ (42 LEDs)    │
        └───────┬──────┘
                │
             20-30cm
                │
                ▼  Illumination direction
         ┌────────────┐
         │  Camera    │
         │  (NoIR)    │
         └────────────┘

Advantages:
- Reduces direct lens flare
- Good for overhead mounting
- Easy to adjust angle

Disadvantages:
- May create shadows
- Less uniform than ring mount
```

### Configuration C: Side Mount

```
Top View:

    ┌──────────────┐
    │ IR LED Board │ ───┐
    │ (42 LEDs)    │    │ 15-30°
    └──────────────┘    │
                        │
        10-20cm         │
                        ▼
               ┌────────────┐
               │  Camera    │
               │  (NoIR)    │
               └────────────┘

Advantages:
- Simple mounting
- Reduces on-axis reflections
- Cost-effective

Disadvantages:
- Creates slight shadows
- Less even illumination
```

---

## Diagram 9: Fuse Protection Circuit

```
Detailed Fuse Protection:

12V Power Supply                  IR LED Board
┌──────────────┐                 ┌──────────────┐
│   (+) 12V    │                 │              │
│              ├─────┬───────────┤ LED+ (Red)   │
│              │     │           │              │
│   (-) GND    │   ┌─▼─┐         │ LED- (Black) ├──> To MOSFET
│              │   │   │         │              │
└──────────────┘   │ F │  2A Fast-blow Fuse     │
                   │ U │  (5mm x 20mm glass)    │
                   │ S │                         │
                   │ E │  ┌──────────────┐      │
                   └─┬─┘  │ Fuse Holder  │      │
                     │    │ Panel Mount  │      │
                     │    │ or Inline    │      │
                     └────┤              │      │
                          └──────────────┘      │
                                                 │
                                          ┌──────▼──────┐
                                          │   MOSFET    │
                                          │   Control   │
                                          └─────────────┘

Fuse Selection:
- Type: Fast-blow (F) or Fast-acting
- Rating: 2A @ 12V DC
- Package: 5x20mm glass cartridge (common)
- Response: Blows in <1 second at 2x rated current (4A)

Where to Install:
- On +12V line before IR board
- After power supply, before load
- Use inline holder or panel-mount fuse block

Why Fuse is Important:
- Protects against short circuits
- Prevents wire overheating/fire
- Low cost insurance (<$1)
```

---

## Diagram 10: Testing Setup with Multimeter

```
Testing Continuity (Power OFF):

Step 1: Check for Shorts
         ┌─────────────┐
         │ Multimeter  │
         │   Ω Mode    │
         └──┬──────┬───┘
            │      │
      Red   │      │  Black
      Probe │      │  Probe
            │      │
         ┌──▼──────▼──┐
         │  12V+ to   │
         │  12V GND   │
         └────────────┘
Expected: >10kΩ (open circuit or high resistance)
If <10Ω: SHORT CIRCUIT - Do not power on!


Step 2: Check MOSFET Gate Resistance
         ┌─────────────┐
         │ Multimeter  │
         │   Ω Mode    │
         └──┬──────┬───┘
            │      │
            │      │
         ┌──▼──────▼──┐
         │ GPIO Pin   │
         │ to Source  │
         └────────────┘
Expected: ~1kΩ (gate resistor value)


Testing Voltage (Power ON):

Step 3: Measure 12V Supply
         ┌─────────────┐
         │ Multimeter  │
         │   V DC Mode │
         └──┬──────┬───┘
            │      │
      Red   │      │  Black
      Probe │      │  Probe
            │      │
         ┌──▼──────▼──┐
         │  12V+ to   │
         │  12V GND   │
         └────────────┘
Expected: 11.5V - 12.5V


Step 4: Measure IR Board Voltage (GPIO HIGH)
         ┌─────────────┐
         │ Multimeter  │
         │   V DC Mode │
         └──┬──────┬───┘
            │      │
            │      │
         ┌──▼──────▼──┐
         │ LED+ to    │
         │ LED- (on   │
         │ board)     │
         └────────────┘
Expected: 11.5V - 12.5V (when GPIO HIGH)
          0V - 0.5V (when GPIO LOW)


Step 5: Measure Current Draw (optional)

    12V+ ───┬─── [Fuse] ─── IR Board LED+
            │
         ┌──▼────────────┐
         │  Multimeter   │
         │   A DC Mode   │
         │  (10A range)  │
         └───────────────┘
            │
    IR Board LED- ───> To MOSFET

Expected: 150mA - 500mA (depending on LED type and PWM duty cycle)

CAUTION: Some multimeters have low current limits in A mode.
         Check manual before measuring high current!
```

---

## Diagram 11: Common Wiring Errors (Avoid These!)

### Error 1: No Common Ground

```
WRONG - No common ground connection:

Raspberry Pi 5              12V Supply
    GND ─────X (not connected) ────X───── 12V GND
                                   │
    GPIO ────> MOSFET Gate         │
                     │             │
                  Drain ───────────┴───── IR LED-
                     │
                  Source ──────────────── 12V GND

Problem: GPIO signal has no reference to 12V circuit
Result: MOSFET may not switch properly or at all
```

```
CORRECT - Common ground established:

Raspberry Pi 5              12V Supply
    GND ─────────────────────────────── 12V GND
                                   │
    GPIO ────> MOSFET Gate         │
                     │             │
                  Drain ───────────┴───── IR LED-
                     │
                  Source ──────────────── 12V GND

Result: GPIO signal properly referenced, MOSFET switches correctly
```

### Error 2: GPIO Connected to Drain (Wrong Pin)

```
WRONG - GPIO connected to Drain:

    GPIO ────> MOSFET Drain ───── IR LED-
                     │
                  Source ──────── GND

Problem: Drain voltage can be high (12V), may damage GPIO
Result: Raspberry Pi GPIO pin damaged or destroyed
```

```
CORRECT - GPIO connected to Gate:

    GPIO ──[1kΩ]──> MOSFET Gate
                            │
                         Drain ───── IR LED-
                            │
                         Source ──── GND

Result: Gate safely isolated, low current (<1mA) from GPIO
```

### Error 3: Reversed Power Supply Polarity

```
WRONG - Swapped +/- on IR board:

    12V+ ──────────────> IR LED- (Black wire)
    12V GND ───────────> IR LED+ (Red wire)

Problem: Reverse polarity on LEDs
Result: LEDs will not light, may be permanently damaged
```

```
CORRECT - Proper polarity:

    12V+ ──────────────> IR LED+ (Red wire)
    12V GND ───────────> IR LED- (Black wire) via MOSFET

Result: LEDs operate correctly
```

### Error 4: Missing Gate Resistor

```
WRONG - No gate protection resistor:

    GPIO ───────────> MOSFET Gate (direct connection)

Problem: Inrush current can damage GPIO pin
Result: Possible GPIO pin damage, unreliable switching
```

```
CORRECT - Gate resistor installed:

    GPIO ──[1kΩ]──> MOSFET Gate

Result: Current limited to safe level (<3.3mA), GPIO protected
```

---

## Diagram 12: Physical Installation Example

```
Desk/Table Setup (Side View):

          Wall/Background
          (Matte Black)
               │
               │
    ┌──────────▼────────────┐
    │                       │
    │   Tracking Area       │
    │   (1-2.5m range)      │
    │                       │
    │         ╱│\           │  ← Performer with IR wand
    │        ╱ │ \          │
    │       ╱  │  \         │
    │      ╱  IR  \         │
    │        Wand           │
    │                       │
    └───────────────────────┘
               │
               │ ~1.5-2m
               │
         ┌─────▼──────┐
         │  ┌──────┐  │
         │  │Camera│  │  ← Camera + IR ring mount
         │  │+IR   │  │     at eye level or slightly above
         │  └──────┘  │
         │            │
         └────┬───────┘
              │
         Tripod/Mount


Equipment Layout (Top View of Desk):

    Wall
    ═══════════════════════════════════════════

              Tracking Area
                  ▲
                  │ 1.5-2m
                  │
              ┌───┴───┐
              │Camera │  ← Position camera centered
              │ +IR   │     facing tracking area
              └───┬───┘
                  │
              ┌───▼───────────────────────────┐
              │  Desk/Table                   │
              │                               │
              │  ┌──────────┐  ┌───────────┐ │
              │  │Raspberry │  │ 12V Power │ │
              │  │ Pi 5     │  │ Supply    │ │
              │  └────┬─────┘  └─────┬─────┘ │
              │       │              │       │
              │       └──────┬───────┘       │
              │              │               │
              │         Breadboard           │
              │         with MOSFET          │
              │                               │
              └───────────────────────────────┘

Cable Management:
- Keep power cables separated from GPIO wires
- Use cable ties to organize wires
- Label all connections for future maintenance
```

---

## Safety Checklist

Before powering on, verify ALL of the following:

### Visual Inspection
- [ ] All wire connections are secure (no loose wires)
- [ ] No exposed wire strands (risk of short circuit)
- [ ] Correct polarity: Red to +12V, Black to GND
- [ ] MOSFET pins correct: Gate, Drain, Source
- [ ] Gate resistor (1kΩ) installed between GPIO and MOSFET Gate
- [ ] Common ground wire connects Pi GND to 12V GND
- [ ] No wire crossings that could short
- [ ] Fuse installed on +12V line (if using)

### Multimeter Tests (Power OFF)
- [ ] Resistance between 12V+ and 12V- is >10Ω (no short)
- [ ] Resistance from GPIO to Source through gate resistor is ~1kΩ
- [ ] Continuity from Pi GND to 12V GND (common ground)
- [ ] No continuity between 12V+ and Pi 5V pins (isolation verified)

### First Power-Up Protocol
- [ ] Power on 12V supply first (Pi OFF)
- [ ] Measure voltage at IR board: 11.5-12.5V expected
- [ ] Check for smoke, smell, or excessive heat
- [ ] Verify IR LEDs light up (view with smartphone camera)
- [ ] Feel IR board temperature: warm is OK, too hot to touch is problem
- [ ] Power on Raspberry Pi 5
- [ ] Run GPIO test script to verify control

### Ongoing Monitoring
- [ ] Check IR board temperature after 10 minutes of operation
- [ ] Monitor for any unusual smells or sounds
- [ ] Verify MOSFET is not overheating (should be cool to touch)
- [ ] Test GPIO control: LEDs should turn on/off cleanly

---

## Troubleshooting Reference

| Symptom | Likely Cause | Check This | Solution |
|---------|--------------|------------|----------|
| IR LEDs don't light | No power to board | Measure voltage at LED+ and LED- | Check 12V supply, fuse, connections |
| IR LEDs always on | MOSFET shorted or GPIO stuck HIGH | Measure voltage at MOSFET Gate | Replace MOSFET, check GPIO code |
| IR LEDs always off | MOSFET not conducting | Check Gate voltage when GPIO HIGH | Use logic-level MOSFET (IRLZ34N) |
| GPIO control doesn't work | No common ground | Verify Pi GND connected to 12V GND | Add common ground wire |
| Dim IR illumination | Insufficient Gate voltage | Measure Gate voltage | Use logic-level MOSFET, check resistor value |
| IR flickers | Loose connection | Wiggle wires while powered | Re-seat all connections, solder if needed |
| MOSFET gets very hot | Wrong MOSFET or shorted Drain | Check MOSFET part number | Replace with correct logic-level MOSFET |
| Raspberry Pi won't boot | 12V on GPIO pin | Measure GPIO pin voltage | Disconnect immediately, check for wiring error |
| Fuse blows immediately | Short circuit | Measure resistance 12V+ to GND (power OFF) | Find and fix short circuit |
| PWM doesn't dim LEDs | Wrong GPIO pin or bad MOSFET | Verify GPIO 18 used, check MOSFET | Use hardware PWM pin, replace MOSFET |

---

## Additional Resources

For more detailed information, refer to the main research document:
`IR_ILLUMINATOR_INTEGRATION_RESEARCH.md`

Sections:
1. Hardware Setup (detailed component specifications)
2. Optimal Configuration (positioning and tuning)
3. Safety (eye safety, electrical safety, thermal management)
4. Computer Vision Integration (camera settings, SimpleBlobDetector)
5. Documentation URLs (datasheets, tutorials, forums)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-22
**Companion to:** IR_ILLUMINATOR_INTEGRATION_RESEARCH.md

**WARNING:** Working with 12V DC and GPIO pins requires careful attention to wiring.
Double-check all connections before applying power. When in doubt, ask for help.

**DISCLAIMER:** These diagrams are provided as guidance. Always verify connections
with component datasheets and test with multimeter before applying power.
