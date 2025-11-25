# Interactive Wand

Wave a wand, cast real spells with LED effects and sound!

> **Original project by [Andrew Congdon (Gloworm72)](https://github.com/Gloworm72/InteractiveWand)**
> | [Project Webpage](https://andrewcongdon14.wixsite.com/andrew-congdon/interactive-wand)

This project uses a Raspberry Pi 5, camera, and machine learning to recognize wand gestures and trigger magical effects.

---

## What You Need

**Required:**
- Raspberry Pi 5 (4GB+ recommended)
- Raspberry Pi Camera Module 3 NoIR (Wide Angle)
- WS2812B LED Strip (30+ LEDs)
- IR Illuminator (850nm)
- A wand with an IR LED tip

**Optional:**
- Servo motor (for physical box opening effect)

For detailed hardware specs and where to buy, see the [Technical Guide](docs/TECHNICAL_GUIDE.md#hardware-requirements).

---

## Quick Setup

### 1. Clone the repository
```bash
git clone https://github.com/qfogarty/Interactive-Wand-Gesture-Recognition.git
cd Interactive-Wand-Gesture-Recognition
```

### 2. Run the installer
```bash
./install.sh
```

### 3. Configure your hardware
```bash
python3 setup_wizard.py
```

### 4. Train your spell gestures
```bash
cd DatasetCreation
python3 train_spell_classifier.py
cd ..
```

### 5. Cast spells!
```bash
python3 harry_potter_wand_cv.py
```

Press **q** to quit.

---

## See It In Action

[![Watch the video](https://img.youtube.com/vi/IFpQFHPK7W4/0.jpg)](https://www.youtube.com/watch?v=IFpQFHPK7W4)

*Click to watch the demo video*

---

## How It Works

1. The camera tracks the bright IR LED on your wand tip
2. As you draw a gesture, it traces your movement
3. When you hold still, an ML model recognizes the spell
4. LEDs flash, sounds play, and magic happens!

**Default spells:**
- **Alohamora** (unlock) - Purple LED animation
- **Colloportus** (lock) - Blue LED animation

---

## Add Your Own Spells

Want to create new spells? It's easy:

```bash
cd DatasetCreation

# 1. Draw your new spell gesture 50-100 times
python3 draw_spell_data.py

# 2. Convert drawings to training data
python3 convert_to_training_data.py

# 3. Train the model
python3 train_spell_classifier.py
```

That's it! The new spell will be recognized. To add custom LED colors and sounds, see the [Custom Spells Guide](docs/TRAINING_CUSTOM_SPELLS.md).

---

## Common Issues

| Problem | Quick Fix |
|---------|-----------|
| LEDs not working | Run `ls /dev/spidev0.0` - if missing, enable SPI in `raspi-config` |
| Wand not detected | Check the "Gray Feed" window - wand tip should be a bright white dot |
| No sound | Run `speaker-test -t wav -c 2` to test audio output |
| Spell not recognized | Draw gestures more deliberately, hold still at the end |

For more help, see the [full troubleshooting guide](docs/TECHNICAL_GUIDE.md#troubleshooting).

---

## Learn More

- **[Technical Guide](docs/TECHNICAL_GUIDE.md)** - Full hardware setup, wiring diagrams, architecture
- **[Configuration Guide](docs/CONFIGURATION.md)** - All settings explained
- **[Custom Spells Guide](docs/TRAINING_CUSTOM_SPELLS.md)** - Add your own spells with custom LED colors
- **[Wiring Diagrams](docs/research/WIRING_DIAGRAMS.md)** - Visual circuit diagrams

---

## Contributing

Contributions welcome! Please read the technical guide first to understand the architecture.

## License

See the original project for license details.
