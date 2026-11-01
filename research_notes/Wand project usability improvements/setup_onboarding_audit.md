# Interactive Wand: Setup and Onboarding Audit

Audited at commit `7e21647`. All paths are relative to the repo root, and citations are `file:line`.

**Evidence labels**
- **[R]**: verified by reading the code.
- **[X]**: executed on macOS (Python 3.9.6) against a throwaway `git archive` copy in a scratch directory. The real tree was not touched.
- **[W]**: external web or PyPI source.
- **[I]**: my inference, not verified. No Pi, camera, SPI, LEDs or wand were available.

**Not run:**
- `install.sh`, because it needs apt and would upgrade the host.
- Docker targets.
- `harry_potter_wand_cv.py` past its imports, because `picamera2` cannot be installed on a Mac.
- `calibrate_reflector.py`, `test_led_demo.py` and `draw_spell_data.py`, which need hardware or a GUI.

## Walking README Quick Setup literally: does each step exist and feed the next?

### Takeaway
Every referenced script exists, and steps 1 to 4 chain mechanically, so the suspected missing `train_spell_classifier.py` is a false alarm. The walk breaks in other places:
- No step covers wiring.
- A shipped `config.yaml` makes step 3's default answer cancel the wizard.
- No pre-trained model ships.
- Step 5 never says what gesture to draw, and the only doc that describes the gestures does not match the training data.

### Cited Findings

**Step by step**

| README step | Exists? | Actual behaviour | Output for next step |
|---|---|---|---|
| 1. Clone (`README.md:83-84`) | Not tested (no network clone) | - | - |
| (missing) Wire hardware | **No step** | `README.md:81-107` goes from clone to casting with no wiring step. `docs/TECHNICAL_GUIDE.md:148-153,196` treats wiring as a prerequisite to install. | - |
| 2. `./install.sh` (`README.md:89`) | Yes, mode 100755 [X] | See the next section. May end by offering a reboot and printing no next steps (`install.sh:218-229`). | Dependencies, SPI, groups |
| 3. `python3 setup_wizard.py` (`README.md:94`) | Yes | `config.yaml` is tracked, so the first prompt is always "Overwrite existing configuration? [y/N]". Pressing Enter prints "Setup cancelled." and exits 0 (`setup_wizard.py:242-246`) [X]. The README diagram says the wizard "Creates" `config.yaml` (`README:73`). | Nothing needed: the shipped config is valid |
| 4. `cd DatasetCreation; python3 train_spell_classifier.py` (`README.md:99-101`) | **Yes**, tracked | Trained on the shipped data: 402 samples, 201 per class, 784 features. Test accuracy 0.9901, 29 s wall on a Mac, model saved to the repo root [X]. The grid is 180 candidates x 5 folds = 900 fits (`train_spell_classifier.py:42-51`). | `new_custom_classifier.pkl` |
| 5. `python3 harry_potter_wand_cv.py` (`README.md:106`) | Yes | Needs camera, audio and a display at startup (next section). The model is not checked until the first cast. | First spell |

**Specific references**
- **`classifier.pkl` is the wrong name.** `README.md:74` says `classifier.pkl`. Everything else uses `new_custom_classifier.pkl` (`config.yaml:98`, `config_loader.py:74`, `train_spell_classifier.py:24`) [R].
- **No pre-trained model ships.** `.gitignore` has `*.pkl` with the comment "each user should train their own", and `git ls-files` finds no `.pkl` [X].
- **Docs disagree on whether training is needed:**
  - `install.sh:233` says "Train your model (optional)".
  - `docs/TECHNICAL_GUIDE.md:172-178` routes "Train custom spells? No" straight to run.
  - `docs/TECHNICAL_GUIDE.md:1062-1066` calls it a "pre-trained model".
  - `README.md:97` correctly makes it mandatory.
- **Training data does ship**: `DatasetCreation/X_spells.npy`, `y_spells.npy`, `spells_dataset.csv`, and 402 tracked PNGs in `DatasetCreation/spells_dataset/` [X]. This refuted my own hypothesis that the conversion step would wipe the data.
- **Missing model fails late.** `MODEL_PATH` is only loaded lazily in the prediction thread (`harry_potter_wand_sklearn.py:17-21,35`, `harry_potter_wand_cv.py:258`), with no startup check. The `try/finally` has no `except` (`harry_potter_wand_cv.py:251-273`) [R].
- **Doc links, checked by reading the targets [R]:**
  - README links and anchors resolve: `#hardware-requirements` and `#troubleshooting` exist in the Technical Guide.
  - Broken: `docs/CONFIGURATION.md:807-809` links `TRAINING_GUIDE.md` (the file is `TRAINING_CUSTOM_SPELLS.md`) and two reports at `docs/` rather than `docs/research/`.
  - Broken: `docs/TRAINING_CUSTOM_SPELLS.md:819` links `README.md#troubleshooting` (the README heading is "Common Issues").
  - Broken: the `docs/CONFIGURATION.md:14` table of contents links `#ir-illuminator-optional` (the heading at `:331` is "IR Illuminator").
- **Tests do not catch these.** `tests/test_documentation.py:135-165` only checks `docs/*.md` links from the README, with no anchors and no script references [R]. `make test-local` passes 7/7 on macOS and then prints "The codebase is ready for deployment" [X].
- **Gesture instructions:**
  - The README lists spell names and colours but no shapes (`README.md:147-149`).
  - `docs/TECHNICAL_GUIDE.md:786` says "upward swirl for Alohamora, downward swirl for Colloportus".
  - I rendered the shipped samples. Class 0 (open) is a **circle with a vertical stroke through it (a phi shape)**. Class 1 (close) is a **square hook, like a "P" or a flag** [X]. Neither is an up or down swirl.
  - The classifier sees only a static 28x28 image (`harry_potter_wand_cv.py:254-258`), so stroke direction cannot be a feature [R].
- **First-cast state:** `lastMove` starts at 0, and "close" only fires when `lastMove == 1` (`harry_potter_wand_cv.py:203,261-270`). Casting Colloportus first prints `Prediction: 1` and nothing else [R].
- **Default feedback is thin.** `led.enabled: false` ships (`config.yaml:13`). `screen_flash_feedback` is defined but never called (`harry_potter_wand_cv.py:220`; grep finds no caller) [R]. A successful spell therefore produces only sound and console text.

### Inferences
- [I] A user who follows the README gets the error for a missing model only at the first cast, as a thread traceback, if they skip step 4 because `install.sh` called it optional.
- [I] A user following the "swirl" text will mostly get wrong or random predictions and blame detection, because the SVM was trained on very different shapes. This may be the largest gap between a "working install" and a "first spell".
- [I] The runtime mirrors the frame (`harry_potter_wand_cv.py:283`), so what the user should physically draw needs checking against the on-screen trace. Doc images should be labelled "as seen on screen".
- [I] Pi 5 training time will be longer than the Mac's 29 s, and the README gives no warning about it or about the verbose `verbose=2` output (`train_spell_classifier.py:51`).

### Gaps
- Actual Pi 5 training time.
- Whether a live wand trace resembles the shipped samples closely enough. That belongs with the runtime and training researcher.

## What do install.sh, setup_wizard.py, test_setup.py, config_loader.py, config_builder.py, hardware_checks.py and the Makefile do, and how do they handle failure, re-runs, missing hardware and non-Pi machines?

### Takeaway
The tools have sensible guards, such as a root check, idempotent `config.txt` edits and an overwrite prompt. They are weak in five ways:
- The installer mixes apt and pip with no pins.
- Reboot detection checks the wrong thing.
- The wizard asks many questions that have no effect.
- The validator cannot express "optional", and it passes broken imports.
- The main script hard-crashes on missing peripherals.

### Cited Findings

**install.sh**
- `set -e`; warns on non-Pi and asks `y/N` (`install.sh:6,27-34`); refuses root (`:37-41`) [R]. Good.
- Runs an unprompted `apt-get upgrade -y` on every run (`:50-51`) [R], so re-runs are slow and change the system.
- Installs `python3-opencv` and `python3-numpy` from apt (`:61-62`) **and** `numpy`, `opencv-python`, `pandas`, `scikit-learn>=1.6.0`, `pi5neo` from pip with `--break-system-packages` and no pins, plus a pip self-upgrade (`:87-98`) [R]. There is no `requirements.txt` in the repo [X].
- PyPI: the current `opencv-python` is 5.0.0.93, requires `numpy>=2` on Python >= 3.9, and publishes aarch64 wheels ([PyPI JSON](https://pypi.org/pypi/opencv-python/json)) [W, X]. Users report picamera2 failing on import inside `simplejpeg` with "numpy.dtype size changed" after pip pulled in numpy 2 ([Ultralytics thread](https://community.ultralytics.com/t/installation-of-yolo-creates-problems-with-dronekit-python-flight-scripts-on-raspberry-pi/1283), [SunFounder forum](https://forum.sunfounder.com/t/valueerror-numpy-dtype-size-changed-may-indicate-binary-incompatibility-expected-96-from-c-header-got-88-from-pyobject/2899)) [W]. These are user reports, not official documentation.
- SPI and camera lines are grep-guarded and appended to `/boot/firmware/config.txt` (`:109-124`), which makes them idempotent [R]. The path is hard-coded, so an OS without that path fails at `tee`.
- **Reboot detection only checks group membership** (`:213-216`), not whether SPI was just enabled (`:109-112`). If the user is already in `spi`, the script prints next steps with no reboot prompt, though SPI needs one [R].
- **The reboot path prints no next steps**, and Enter means reboot (`:222-226`) [R].
- `install.sh:237` advertises `./install.sh --help`. The script has **no argument parsing**, so that command runs the full install, including the upgrade [R].
- There is no `cd "$PROJECT_DIR"`. The heredoc Python imports `config_loader` from the current directory (`:147-157,166-172`). Run from elsewhere, the import fails: I confirmed `ModuleNotFoundError` with the same stdin-script pattern [X]. The script then prints "Configuration error" and exits.
- `:198-199` makes the main scripts executable, but neither has a shebang (`harry_potter_wand_cv.py:1` is `import math`) [X]. `./harry_potter_wand_cv.py` will not run as Python.
- `rpicam-apps`, `pigpio` and `gpiozero` are not installed by the script (grep finds none) [X], yet `test_setup.py:66` requires `rpicam-hello`, and the servo path needs `gpiozero` and `pigpio` (`harry_potter_wand_cv.py:66-69`).
- `README` and the Technical Guide do not mention logging, resume or a dry run, and the script has none [R].

**setup_wizard.py and utils/config_builder.py**
- Hardware failures warn, and "Continue anyway?" defaults to yes (`setup_wizard.py:254-258`) [R]. Good for non-Pi use. It ran to completion on macOS [X].
- A full default run is **25 prompts** (counted by a scripted run) [X].
- **7 of those 25 have no effect on the main script** [R]:
  - Camera width, height, exposure, gain and brightness (`setup_wizard.py:62-66`), because `harry_potter_wand_cv.py:53-57` hard-codes 640x480 and never calls `set_controls`.
  - Spell volume (`setup_wizard.py:218`), because `audio.spell_volume` is never read outside tests [X].
  - IR type (`setup_wizard.py:105`), whose only effect is on those unused camera values. `ir_type` is not even written by `config_builder.py:95-99`.
- **IR choice silently overrides answers.** Exposure and gain are overwritten after being asked (`setup_wizard.py:69-71`). I entered exposure 5000 with camera-mounted IR, and the saved file has 12000 and gain 8.0 [X].
- **No question asks whether LEDs exist.** The generated config has no `led.enabled` (`config_builder.py:77-82`) [X]. The main script then defaults it to True (`harry_potter_wand_cv.py:90`), while `test_led_demo.py:33` defaults it to False and warns "LEDs disabled". The same config means opposite things [R].
- It rewrites `config.yaml` with **0 comment lines** (shipped file has 21) [X]. It also drops any calibrated reflector values, resetting them to constants (`config_builder.py:30-54`). If `wand_type` is LED, it omits the `reflector` section altogether [X].
- `config.yaml` is tracked (`git ls-files`) [X]. Wizard and calibrator both overwrite it.

**test_setup.py and utils/hardware_checks.py**
- Runs 9 sections with no notion of optional hardware. `test_led_strip` ignores `led.enabled` (`test_setup.py:157-193`) [R], so a camera-only user can never see "All tests passed".
- On macOS: 0/9 passed, with exit 1 [X]. The missing model fails both "Configuration" and "ML Model" (`test_setup.py:89-94,246`) [R, X].
- **Python checks use `importlib.util.find_spec` without importing** (`test_setup.py:20`) [R], so a binary-incompatible picamera2 or numpy would still show a green tick.
- It never checks for a display or a real captured frame, and it cannot check the wand or IR (`test_setup.py:293-303`) [R].
- `except FileNotFoundError` (`test_setup.py:99`) is dead code: `config_loader.py:49-52` calls `sys.exit(1)`, and `SystemExit` is not caught by `except Exception` (`:103,125,318`) [R]. A missing config aborts the whole validator instead of showing the wizard hint.
- `check_camera_available` reports "Camera Module 3 NoIR detected" for any `imx708` string (`hardware_checks.py:31-32`) [R], so a standard, non-NoIR Module 3 would get a false positive. A user who bought the wrong camera, which would see little IR, is told the opposite of what they need to know.
- Messages are partly actionable: "add user to 'spi' group and reboot" (`:59`) names the fix, but "install rpicam-apps" (`:40`) and "enable with sudo raspi-config" (`:35`) give no command or menu path, and "Camera test timed out" (`:38`) gives no next step. `No camera detected` never mentions the ribbon cable.

**config_loader.py**
- `Run install.sh to create default config` (`config_loader.py:51`) is false: `install.sh:138-142` errors out if the config is missing.
- Nearly every consumer wraps it in `except (ImportError, SystemExit)` and prints "config.yaml not found, using hardcoded paths" (`harry_potter_wand_cv.py:19-22`) [R]. This misreports **invalid YAML** (`config_loader.py:58-60`) and **missing PyYAML** as a missing file.
- Fallback mode at `harry_potter_wand_cv.py:29-34,90` silently disables the servo and LEDs [R].

**Main script at startup**
- `picamera2` import at module top (`harry_potter_wand_cv.py:8`), `mixer.init()` (`:37`), sound loads (`:39-41`), and `Picamera2()` (`:53`) are all outside any `try` [R].
- Servo and LED init are wrapped and degrade to warnings (`:64-85,92-108`) [R]. Good, and the pattern could be reused.
- `cv2.imshow` (`:376-377`) is unconditional [R].

**Makefile**
- Test and demo wrappers only. **No `install`, `setup`, `train`, `run` or `doctor` target** (`Makefile:1`) [R].
- `make test-local` passes on a Mac [X]. Docker targets were not run.

### Inferences
- [I] On Raspberry Pi OS Bookworm, whose apt numpy is 1.x per the versions in the reports above, `pip install opencv-python` would put numpy 2 in `~/.local` ahead of apt's. That matches the reported picamera2 import failure. **This is the highest-value thing to test on a real Pi.** It may not occur on newer OS releases whose apt numpy is already 2.x, or where `simplejpeg` has been rebuilt.
- [I] pip's `cv2` will also shadow apt's, and the OpenCV major version installed will be 5.x. I confirmed the APIs the app uses exist on 4.10 only [X], since Python 3.9 on my Mac resolved to that. 5.x is untested.
- [I] The first user created by Raspberry Pi Imager is normally already in `spi`, `gpio` and `video`. If so, the common case is the wrong one: no reboot prompt, SPI off, and `/dev/spidev0.0` missing until the next reboot. `raspi-config`-free users would hit "SPI device not found" with a message pointing them at the wrong fix.
- [I] On non-Pi Linux, step 2 fails at `python3-picamera2` *after* `apt-get upgrade -y` has already run, since Debian and Ubuntu stock repositories generally lack it. On macOS it dies at `sudo apt-get`. In both cases the "Continue anyway?" prompt offers no useful outcome.
- [I] A tracked `config.yaml` means user edits will dirty the tree and can conflict on `git pull`.

### Gaps
- Actual install.sh behaviour on Bookworm and Trixie, including whether `libtiff5-dev` still resolves. packages.debian.org returned no usable result to my requests.
- Whether the 3-second `rpicam-hello` timeout (`hardware_checks.py:26`) gives false negatives on a Pi 5.
- Default group membership on a fresh image.

## Are the docs consistent with the code and config.yaml?

### Takeaway
No. The docs have clearly accumulated over several refactors. The most damaging contradictions are the camera settings that do nothing, the gesture descriptions, and the LED, IR and wand prerequisites. Stale line-number references and removed-code instructions are the most common type.

### Cited Findings

**Settings documented as working that the runtime ignores [R]**
- `hardware.camera.*`:
  - Documented with tuning advice at `docs/CONFIGURATION.md:266-300` and required manual exposure at `docs/TECHNICAL_GUIDE.md:411-431`.
  - The main script uses hard-coded size and no controls (`harry_potter_wand_cv.py:53-57`).
  - The only code using these values is `calibrate_reflector.py:174-178`, and it **hard-codes** 8000/6.0/-0.3, ignoring the config.
  - So the calibrator tunes under different exposure from runtime, and "No blob detected: increase `exposure_time`" (`docs/CONFIGURATION.md:779`) does nothing.
- `hardware.ir_illuminator.*`: PWM documented at `docs/TECHNICAL_GUIDE.md:518-538` and `docs/CONFIGURATION.md:370-393`. No code drives it. `enabled` only triggers a permission check (`config_loader.py:120`).
- `audio.spell_volume`: `docs/CONFIGURATION.md:618,627,633`. Never read.
- `lastframe.jpg`: `docs/TECHNICAL_GUIDE.md:977,1068-1070` says it holds the latest trace. The runtime predicts from an array and never writes it (`harry_potter_wand_cv.py:27,258`).

**Referenced things that do not exist [R, X]**
- `config.yaml.example` (`docs/CONFIGURATION.md:748`).
- `CONFIG_PATH` environment variable (`docs/CONFIGURATION.md:700`). `config_loader.py:37-44` never reads the environment.
- `./install.sh --help` (`install.sh:237`).
- `TRAINING_GUIDE.md` (`docs/CONFIGURATION.md:807`).
- "Backward Compatible: Falls back to sensible defaults" (`docs/CONFIGURATION.md:34`) is only partly true: the fallback disables LEDs and the servo (`harry_potter_wand_cv.py:62,90`).
- "Reset to defaults: Run setup_wizard" (`docs/CONFIGURATION.md:798`): the wizard's output differs from the shipped file (no `led.enabled`, no `reflector` for LED wands, no comments) [X].

**Stale code references [R]**
- `docs/TECHNICAL_GUIDE.md:652,986`: "comment out servo lines (11, 40-43, 112-151, 178, 183, 301) or the script will error". The servo is now config-gated (`harry_potter_wand_cv.py:61-85`).
- `docs/TECHNICAL_GUIDE.md:744-752,956-957,978-979,988`: "lines 50-62", "line 51", "line 38", "line 74/75", "edit line 33". All are outdated, and all tell users to edit code rather than config.
- `docs/TECHNICAL_GUIDE.md:684-688,769`: uses `~/WandProject` paths where the README uses the repo name.
- `docs/TRAINING_CUSTOM_SPELLS.md:245-249,296,376` tells users to edit `spell_fade_out` and `move_servo_smoothly` in `harry_potter_wand_cv.py` at given lines, with old signatures. `:110-129` of the same file says they moved to `utils/animations.py`.
- `docs/TRAINING_CUSTOM_SPELLS.md:234-239`: "Wave your wand" with `harry_potter_wand_sklearn.py`. That script opens no camera and classifies `lastframe.jpg` once; it printed `1` [X].

**Custom-spell claims (detail left to the training researcher) [R]**
- `README.md:224` says "The new spell will be recognized". `convert_to_training_data.py:32` labels everything 0 or 1, and `harry_potter_wand_cv.py:261-270` only handles "0" and "1".
- `draw_spell_data.py:21` hard-codes `LABEL = "close"`, with no class prompt, unlike `docs/TRAINING_CUSTOM_SPELLS.md:94`.
- `draw_spell_data.py:33` starts `counter` at 0, so new drawings **overwrite** shipped samples. Writing `close_0..29.png` left the count at 402 [X].
- `docs/TRAINING_CUSTOM_SPELLS.md:190-195` says conversion centres, normalises and smooths. The script only flattens (`convert_to_training_data.py:36-41`).

**LED-wand versus reflector-wand path**
- Reflector setup is a late README section (`README.md:153-203`), though the wizard asks earlier (`setup_wizard.py:132-147`). The wizard never mentions the calibrator.
- `docs/TECHNICAL_GUIDE.md:25` lists only an IR LED wand under required hardware; its `:88` diagram likewise. Reflector appears only at `:617,904`.
- `README.md:18` lists the IR illuminator as **required** for all, and its diagram has it illuminate the wand (`:46`). An IR LED wand emits its own light. `docs/TECHNICAL_GUIDE.md:797` warns about reflections causing false detections.
- **Default mismatch:** the README says `brightness_threshold` defaults to 180 (`README.md:200`). With no `reflector` section, as the wizard writes for LED wands, the code default is **120** (`utils/reflector_detector.py:86`). A user following `README.md:161-165` after an LED-mode wizard run gets different tuning from the table.
- Calibrator keys: the README lists 5 settings (`README.md:184-190`). `docs/CONFIGURATION.md:472-505` lists 10, plus modes, and has auto-calibrate (`A`), which is arguably the most useful key for a beginner and is missing from the README.
- The wand itself: "850nm IR LED + coin battery works well" (`docs/TECHNICAL_GUIDE.md:25`). No build instructions, resistor or switch guidance is given in the guide.

**IR illuminator placement**
- Number of options: three in `docs/TECHNICAL_GUIDE.md:439-445`, two in `docs/CONFIGURATION.md:333` and `setup_wizard.py:102-103` (no 5V board).
- Range for Option B: "2-5m" (`docs/TECHNICAL_GUIDE.md:444`) versus "5-10m" (`:20,43,492`; `docs/CONFIGURATION.md:366`).
- Placement guidance sits only under Option B (`docs/TECHNICAL_GUIDE.md:540-543`) and `README.md:159` (reflector only). There is no aiming or distance guide for the first run.
- "Connect to camera module's 5V and GND pins" and "powered by camera" (`docs/TECHNICAL_GUIDE.md:20,42,458,461`). [I] I could not confirm the Camera Module 3 has such pins, and this should be checked against the real part before beginners rely on it.

**Power and wiring contradictions**
- LED 5V: "NEVER use Pi 5V pins" (`docs/TECHNICAL_GUIDE.md:368`) versus "NOT from Pi 5V pins for >10 LEDs" (`docs/CONFIGURATION.md:250`).
- Servo: Pi 5V is acceptable (`docs/TECHNICAL_GUIDE.md:630`) versus "must be powered by external 5V source (not Pi pins)" (`docs/CONFIGURATION.md:329`).
- Pi 4: "may work" (`docs/TECHNICAL_GUIDE.md:17`), "not directly compatible" (`:70`), "Pi 4 compatible with different LED wiring" (`:1017`).
- `config.yaml:17` and `docs/CONFIGURATION.md:73` say config files use BCM numbers, but LED `gpio_pin: 19` is a physical pin number, flagged only as "for reference".

**Missing prerequisites**
- **Speaker or audio output:** absent from `README.md:14-22` and `docs/TECHNICAL_GUIDE.md:15-25`. A Pi 5 has no 3.5mm jack; audio is HDMI, USB or Bluetooth ([overview](https://raspberry.tips/en/raspberrypi-tutorials/raspberry-pi-sound-cards-audio-hat)) [W, secondary source]. `docs/TECHNICAL_GUIDE.md:987` still says "HDMI/headphone".
- **Monitor and desktop session:** nowhere stated, yet `cv2.imshow` is unconditional. `docs/TECHNICAL_GUIDE.md:344` recommends SSH, with no warning that the app needs a display.
- **venv:** no mention in any of the four docs [X grep]. The installer uses `--break-system-packages` with no explanation beyond the comment (`install.sh:86`).
- **sudo:** not explained in the README; handled by the script, and the root guard is correct (`install.sh:37-41`).
- **pigpio on Pi 5:**
  - `docs/TECHNICAL_GUIDE.md:636-638,676-677,1035` and `docs/CONFIGURATION.md:327` instruct pigpio; `harry_potter_wand_cv.py:67-69` depends on it.
  - pigpio's own issue tracker reports it does not run on a Pi 5 ([pigpio #589](https://github.com/joan2937/pigpio/issues/589)) [W]. The issue may be dated, so check the current status.
  - The failure degrades to a warning, so the optional servo is probably dead on the target board.
- `docs/TECHNICAL_GUIDE.md:351-358` says enable "I1 Camera" in raspi-config, and `hardware_checks.py:35` and `docs/CONFIGURATION.md:766-768` repeat the idea. [I] Current OS releases auto-detect cameras and this menu item may not exist. Needs checking on a Pi.
- **Install-method divergence:** `docs/TECHNICAL_GUIDE.md:667-669` uses apt `python3-sklearn` and `python3-joblib`; `install.sh:90-98` uses pip.

### Inferences
- [I] Because exposure is not applied, the runtime likely runs on picamera2's automatic exposure, so `min_threshold: 180` is being evaluated against an auto-exposed image. Results could vary with room lighting and explain inconsistent LED-mode detection.

### Gaps
- `docs/research/*.md` were not audited beyond link and grep checks.
- Whether a WS2812B strip works reliably from 3.3V data with no level shifter on the first attempt. I did not find guidance in the sections I read; check `docs/research/WS2812B_RaspberryPi5_Integration_Report.md`.

## Can the software be tried without the hardware?

### Takeaway
Only the offline ML and test parts can. There is no webcam mode, no recorded-video mode and no mock LED run path, although the pieces needed for one largely already exist.

### Cited Findings
- **No alternative input:** grep for `VideoCapture`, `--video`, `--mock`, `argparse`, `headless` across project Python files finds nothing outside `docs/research` and PRPs [X].
- **Main script hard dependency:** `picamera2` import at `harry_potter_wand_cv.py:8` [R]. On my Mac it failed one line earlier on `cv2`, which was not yet installed [X].
- **LED demo:** cannot run without a strip ("Cannot run demo without LED strip", `test_led_demo.py:308-311`), or without `pi5neo` (`:49-51`) [R].
- **Mocks exist but are test-only:** `tests/mocks/mock_pi5neo.py`, `tests/mocks/mock_gpiozero.py` [X]. The animation code already treats `neo=None` as printing "[SPELL EFFECT]" (`utils/animations.py:65-79`) [R].
- **What does work with no hardware [X]:**
  - `make test-local` (7/7).
  - `train_spell_classifier.py` (99.01% test accuracy).
  - `harry_potter_wand_sklearn.py` on the tracked `lastframe.jpg` (prints `1`).
  - `config_loader.py` (reports its results cleanly).
  - The wizard (completes with warnings).
- `draw_spell_data.py` should also work given a GUI and full `cv2` [R]. Not run; I installed headless OpenCV.
- **The detection loop is only lightly coupled:** the camera is used only in `picam2.capture_array()` (`harry_potter_wand_cv.py:282`) and setup (`:53-57`) [R].

### Inferences
- [I] A small `FrameSource` abstraction (Picamera2, `cv2.VideoCapture(index_or_file)`), a `--no-audio` flag and a `try` around `mixer.init` would let anyone try the whole pipeline on a laptop. A webcam mode could use a phone torch or mouse pointer, or even a bright dot in a recorded clip. With `neo=None` already supported, I estimate this at under about 100 lines. That is an estimate, not a spike.
- [I] A bundled short clip would also become a regression test for the whole trace-to-prediction path, which currently has no coverage.

### Gaps
- Whether a colour webcam works well without IR, given `min_threshold: 180` and `min_circularity: 0.75`. It may need a separate preset.

## Which config settings must a user understand before anything works, and could they be defaulted or detected?

### Takeaway
Very few. Only three decisions are really needed: wand type, whether LEDs are connected, and LED count. Everything else can be defaulted, detected or removed. The wizard currently asks 25 questions and misses one of the three (LEDs connected).

### Cited Findings

| Setting | Must user decide? | Read by runtime? | Suggestion |
|---|---|---|---|
| `detection.wand_type` (`config.yaml:43`) | **Yes** | Yes (`harry_potter_wand_cv.py:137`) | Keep as the first wizard question. |
| `hardware.led.enabled` (`config.yaml:13`) | **Yes** | Yes (`:90`), with conflicting defaults | Ask in the wizard, or prompt with a test flash. Unify the default. |
| `hardware.led.count` | **Yes**, if LEDs | Yes (`:98`) | Keep. |
| `hardware.led.timing` | No | Yes | Fixed for WS2812B: 800. Drop from the wizard. |
| `hardware.led.spi_device` | No | Yes | Default, or detect by listing `/dev/spidev*`. Drop from the wizard. |
| `hardware.led.gpio_pin` | No | No ("for reference only", `config.yaml:17`) | Remove it, and put the pin in docs only. |
| `hardware.camera.*` | Not today | **No** in main; ignored by calibrator | Apply it or remove it. Then default it, with the calibrator writing it. |
| `hardware.ir_illuminator.*` | No | **No** beyond a permission check | Remove until implemented. |
| `hardware.servo.enabled` | Optional | Yes | Default false. Hide under "advanced". |
| `detection.blob_detector.*` (6) | No | Yes (LED mode only) | Default. Replace with a calibrator for LED mode. |
| `detection.gesture.*` (3) | No | Yes | Default. |
| `detection.reflector.*` | No | Yes (reflector mode) | Default. Tune with `calibrate_reflector.py`. |
| `audio.background_volume` | No | Yes | Default. Tell users to adjust it after first success. |
| `audio.spell_volume` | No | **No** | Implement or remove. |
| `paths.*` | No | Partly | Remove from wizard flow (already not asked). |

All "Read by runtime?" entries are from [R] plus the [X] grep.

Detection candidates, from existing checks:
- SPI availability (`hardware_checks.py:43-61`).
- Camera model, from the output parsed at `:31`.
- Pi model, from `/proc/cpuinfo` (`install.sh:27`).

### Inferences
- [I] Shipping a working config with `led.enabled: false` is a sensible safe default, but it conflicts with the README listing the strip as required (`README.md:17`). A user who wires LEDs, cancels the wizard and runs the app sees only one console line, "LED strip disabled in config" (`harry_potter_wand_cv.py:108`).
- [I] A better layout is a tracked `config.defaults.yaml` plus an untracked `config.yaml` containing only overrides. Then the wizard can stay short, comments survive, and `git pull` will not conflict. This would need a small deep-merge in `config_loader.py`.

### Gaps
- Whether LED presence can be detected. [I] WS2812B has no return channel, so software cannot confirm a strip is attached. A "did it flash?" prompt is the realistic option. This also means `test_setup.py:173,184` reports "LED test complete" whether or not a strip is attached.

## Top onboarding blockers ranked by severity, with concrete fixes

### Takeaway
A user can complete every documented step and still not get a spell, because the gesture is misdescribed, the first-cast rule is undocumented, and feedback is silent. Fix those first: they are cheap and certain. Then test the install on a real Pi, because the numpy conflict could stop users before they reach anything else.

### Cited Findings
Evidence for each is cited in the sections above. "Confidence" is how sure I am that the problem occurs.

| # | Severity | Confidence | Blocker | Key evidence | Concrete fix |
|---|---|---|---|---|---|
| 1 | Critical | Verified in code and data | **User is not told the right gesture.** The README has no shapes, and the Technical Guide's "swirl" text contradicts the dataset. Colloportus as a first cast silently does nothing, and with the default LED-off config success is sound and console text only. | `README.md:147-149`; `TECHNICAL_GUIDE.md:786`; rendered samples; `harry_potter_wand_cv.py:220,261-270` | Add a gesture image (generated from the shipped PNGs, as seen on screen) to the README. Replace the swirl text. Add on-screen overlay: "Draw: phi for Alohamora". Print "Already open: cast Colloportus" on a state no-op, and draw the prediction and result in the OpenCV window from the main thread. |
| 2 | Critical, if confirmed | Probable; **needs a Pi test** | **apt and pip mix may break picamera2.** Unpinned pip `opencv-python` requires numpy >= 2 next to apt picamera2 and numpy. `test_setup` cannot see the failure because it does not import. | `install.sh:61-62,87-98`; PyPI metadata; forum reports; `test_setup.py:20` | Test on Bookworm and Trixie. Drop pip `numpy` and `opencv-python` and use apt. Add a pinned `requirements.txt` for the rest, ideally in a `python3 -m venv --system-site-packages` environment. Change `check_python_package` to actually import. |
| 3 | High | Code verified; effect on Pi inferred | **Camera config is not applied**, so documented tuning does nothing, wizard answers are discarded, and the calibrator uses different hard-coded values. | `harry_potter_wand_cv.py:53-57`; `calibrate_reflector.py:174-178`; `CONFIGURATION.md:286-300` | Add one shared `utils/camera.py` that builds the camera from `hardware.camera` (including `AeEnable: False`), and use it in both scripts. Validate the result on a Pi, because this will change detection behaviour and defaults may need retuning. |
| 4 | High | Code verified; default-group behaviour inferred | **Reboot logic is wrong.** The script tracks groups but not SPI. Enter on the prompt reboots, and that path prints no next steps. | `install.sh:109-112,213-229` | Set `REBOOT_NEEDED=true` whenever `config.txt` changes or `/dev/spidev0.0` is missing. Print next steps before the prompt, and write them to a `NEXT_STEPS` file or a `make doctor` hint. |
| 5 | High | Code verified; runtime failure inferred | **Unlisted prerequisites crash startup.** No audio device kills the app at `mixer.init()`, before the camera. `imshow` needs a display, and the docs recommend SSH. Neither speaker nor monitor is in the parts list. | `harry_potter_wand_cv.py:37,376`; `README.md:14-22`; `TECHNICAL_GUIDE.md:344` | Add both to "What You Need". Wrap the mixer in `try`, and degrade to silence with a warning, as is done for LEDs. Check `DISPLAY`/`WAYLAND_DISPLAY` at startup with a clear message, and add both to `test_setup`. |
| 6 | High | Verified by running | **Step 3 wizard misleads.** Enter cancels, since a config ships. It then asks 25 questions, 7 with no effect, overrides answers, never asks about LEDs, and erases comments and calibration. | `setup_wizard.py:62-71,242-246`; `config_builder.py:77-82` | Reduce to wand type, LEDs yes/no, LED count, then a flash test. Add "advanced" for the rest. Merge into the existing config rather than replacing it. Rephrase the first prompt: "Reconfigure? [Y/n]". |
| 7 | High | Verified in code | **LEDs off by default while listed as required**, and `enabled` is interpreted differently across scripts (True versus False when absent). | `config.yaml:13`; `harry_potter_wand_cv.py:90`; `test_led_demo.py:33`; `config_builder.py:77` | Have the wizard write `enabled` and put a single default in `config_loader`. Add a startup summary: "LEDs: OFF (set hardware.led.enabled)". Add a README line. |
| 8 | Medium-high | Verified in code | **Missing wiring step and missing-model late failure.** Wiring is absent from Quick Setup. The model error appears only in a thread at the first cast, and the docs call training "optional" or the model "pre-trained". | `README.md:81-107`; `harry_potter_wand_cv.py:258`; `install.sh:233`; `TECHNICAL_GUIDE.md:172-178,1066` | Add a README wiring step linking to the guide. Fail at startup: "Model not found. Run: make train". Correct the three doc statements. Alternatively, have install or the wizard offer to train from the shipped data, or generate the model automatically on first run. |
| 9 | Medium | Verified by running | **`test_setup` gives no clear go/no-go.** It cannot treat LEDs as optional, double-counts failures, gives false greens on imports, and never captures a frame. | `test_setup.py:20,89-94,157-193,293-303`; 0/9 run | Respect `enabled`. Group as Required, Optional and Next action. Actually import modules and capture one frame. Print only one suggested fix per failure. Add `make doctor`. |
| 10 | Medium | Verified by reading and grep | **No way to try without hardware**, so no safe way to evaluate before buying parts, and no debugging path for a suspected camera problem. | `harry_potter_wand_cv.py:8,53-57,282` | Add `--source picamera|webcam:N|file.mp4` and `--no-audio`, and a mock `neo` for the LED path. Bundle a short test clip. Move `tests/mocks` behind a `--mock-leds` flag. |
| 11 | Medium | Verified by reading | **Doc rot** erodes trust and sends users to edit the wrong code: nonexistent files and variables, old line numbers, servo comment-out instructions, inconsistent IR options and power advice. | Section on doc consistency | Sweep the listed items. Remove every code line-number reference. Consolidate the IR options into one table. Extend `tests/test_documentation.py` to check links in all docs, anchors, and every referenced file and script. |
| 12 | Medium | Verified in code | **Reflector path is second-class:** a late section, defaults that differ (180 versus 120), and the calibrator is not suggested by the wizard. Illuminator placement is scattered, and the "required" status for LED wands is unclear. | `README.md:18,153-203`; `reflector_detector.py:86`; `TECHNICAL_GUIDE.md:25,540-543` | Split Quick Setup into "Choose your wand" with two paths. Have the wizard offer `make calibrate` at the end. Unify the default in one place. State plainly when an illuminator is needed. |
| 13 | Low-medium | Verified in code | **Installer rough edges:** `--help` runs a full install; `apt upgrade -y` runs on every re-run; depends on the current directory; `chmod +x` on scripts with no shebang; `install.sh` fails late on non-Pi. | `install.sh:50-51,147,198-199,237` | Add arg parsing (`--help`, `--no-upgrade`), `cd "$PROJECT_DIR"`, and shebangs. Make non-Pi exit immediately with a pointer to the no-hardware mode. |
| 14 | Low | Verified in code | **Misleading error text**: "Run install.sh to create default config"; "config.yaml not found" for bad YAML or missing PyYAML; "NoIR detected" for any IMX708; `config.yaml.example`. | `config_loader.py:51`; `harry_potter_wand_cv.py:19-22`; `hardware_checks.py:31-32`; `CONFIGURATION.md:748` | Correct the text. Stop catching `SystemExit` as fallback. Add camera tuning-file or filename detail, and a "verify NoIR yourself" hint. |
| 15 | Low (optional hardware) | Web source; not tested | **Servo path relies on pigpio**, which reportedly does not run on a Pi 5. | `harry_potter_wand_cv.py:67-69`; [pigpio #589](https://github.com/joan2937/pigpio/issues/589) | Verify on a Pi. If confirmed, move to the lgpio pin factory and update the docs. |

**Already good, worth keeping:**
- Root guard and idempotent `config.txt` edits (`install.sh:37-41,109-124`).
- Graceful LED and servo degradation (`harry_potter_wand_cv.py:64-85,92-108`).
- Dataset shipped, so training works first time [X].
- Dynamic path resolution (`config_loader.py:62-75`).
- Wizard's overwrite guard and tolerance of missing hardware.

### Inferences
- [I] Items 1, 4, 7, 8 and 14 are mostly small text or logic changes that could land together, ahead of the larger pieces (2, 3, 6, 10). Item 3 will change detection behaviour, so it should be coordinated with the runtime researcher's recommendations.
- [I] The suggested minimum first-run path: install with an accurate reboot flow, a 3-question wizard, `make train`, `make doctor`, then run with an on-screen gesture hint.

### Gaps
- All Pi-side behaviour is unverified: installer outcome, `mixer.init()` without an audio device, `imshow` on the default desktop or over SSH, auto-exposure effects, and pi5neo behaviour with no strip attached. A single clean-image test on a Pi 5 would settle items 2, 4 and 5, plus the camera menu and default-group questions.
- No real new-user observations exist. Severity reflects code evidence and my judgement, not measured drop-off.
