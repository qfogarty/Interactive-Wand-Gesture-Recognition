# Runtime Experience and Spell-Authoring Workflow Audit

**Evidence labels used throughout.**
- **[CODE]**: verified by reading the cited lines at commit 7e21647.
- **[SIM]**: verified by running real project code on a Mac (scikit-learn 1.6.1, OpenCV 4.10 headless build), with camera, audio and display stubbed and synthetic frames on a fake clock. This shows logic behaviour, not real-world optical performance.
- **[INFERRED]**: reasoning from the evidence; not observed. No Pi, camera, wand, LED strip or IR source was available, so nothing here was tested on hardware.

Links are relative to the repo root. Experiment scripts are `exp1.py`, `exp3.py` and `harness.py` in the session scratchpad (`/private/tmp/claude-501/-Users-qcatch-Sites-Interactive-Wand-Gesture-Recognition/f0cac43d-c7c5-4a85-9f06-a07e0143bca5/scratchpad/`). That directory is temporary, so key outputs are reproduced below. `harness.py` executes the unmodified `harry_potter_wand_cv.py`. No tracked project file was changed.

## How is a gesture started and ended, what feedback does the caster get, is there rejection, and what is hardcoded?

### Takeaway
Every trace that reaches the classifier maps to one of two classes, because there is no confidence check or "unknown" path. The caster gets almost no outcome feedback: the status text only ever says "Ready..." or "Tracing...", and the on-screen spell flash is dead code. The trigger is based on per-frame speed and frame counts rather than time, and the most serious defect is that the live trace is not normalised for size or position. In simulation the stock model's accuracy fell from 99% to about 44% as the gesture shrank.

### Cited Findings

**Start and end of a trace**
- [CODE] Start needs a blob present for longer than `presence_duration` (0.6 s) and a single-frame jump above `movement_threshold` (6 px) — [harry_potter_wand_cv.py:312-316](harry_potter_wand_cv.py#L312).
- [CODE] Completion is `stillness_timer > stillness_duration / 0.05`, which is 21 consecutive frames rather than 1.0 s. The 0.05 assumes 20 fps — [harry_potter_wand_cv.py:186-192](harry_potter_wand_cv.py#L186). The config and docs describe this value as seconds — [config.yaml:57](config.yaml#L57), [docs/CONFIGURATION.md:587](docs/CONFIGURATION.md#L587).
- [SIM] The hold-still time therefore scales with frame rate. The same cast ended about 0.7 s after stopping at 30 fps, about 1.4 s at 15 fps, and 21 frames (0.35 s) at 60 fps — `harness.py` S1, S1b, S1c.
- [CODE] "Still" means less than 6 px between consecutive frames, with no anchor position — [harry_potter_wand_cv.py:194-199](harry_potter_wand_cv.py#L194). At 30 fps, anything slower than about 180 px/s counts as still.
- [SIM] Continuous motion at 4 px/frame (120 px/s) never starts a trace and gives no feedback (S2). A gesture that slows to 4 px/frame part-way is cut off while the wand is still moving, and the half-drawn shape fired Alohamora (S3).
- [SIM] The presence gate clips the start of the gesture. At 60 fps with a 0.42 s lead-in, the trace began about 0.2 s after motion began (S1c). In reflector mode, a wand held still is absorbed by MOG2 and the timer restarts when motion begins: motion began at about 2.83 s and tracing started at 3.60 s, so about 0.77 s of the gesture was lost (S9).
- [SIM] In reflector mode, holding still does not trigger the stillness path. The run ended through "Tracing Done (Wand Left Frame)" about 1.3 s after stopping (S9). The stated "hold still" mechanism and the actual mechanism differ.
- [CODE] There is a second end path: if the blob is absent for longer than `stillness_duration`, prediction runs with no minimum-points check — [harry_potter_wand_cv.py:356-362](harry_potter_wand_cv.py#L356).
- [CODE] There is no maximum trace duration, so a moving wand traces indefinitely. All points are also redrawn every frame — [harry_potter_wand_cv.py:320-324](harry_potter_wand_cv.py#L320). The docs' "less than 3 seconds" advice has no implementation — [docs/TECHNICAL_GUIDE.md:979](docs/TECHNICAL_GUIDE.md#L979).

**Logic defects in the trace state machine**
- [CODE + SIM] The "Canceled trace — likely a reflection" branch is unreachable through stillness. A point is added on every frame, including still frames ([harry_potter_wand_cv.py:319](harry_potter_wand_cv.py#L319)), so `len(points) < 10 and stillness_timer > 20` cannot be true ([harry_potter_wand_cv.py:186-188](harry_potter_wand_cv.py#L186)). A single 15 px twitch followed by stillness went to prediction instead of being cancelled (S12).
- [SIM] App crash: on the first trace of a session in LED mode, if the wand vanishes right after the trace starts, `last_valid_output_frame` is `None` and `cv2.inRange` raises. The process exits (S4) — [harry_potter_wand_cv.py:158](harry_potter_wand_cv.py#L158), [harry_potter_wand_cv.py:358](harry_potter_wand_cv.py#L358).
- [CODE + SIM] Stale prediction: `reset_trace` never clears `last_valid_output_frame` ([harry_potter_wand_cv.py:160-167](harry_potter_wand_cv.py#L160)). The same early-vanish case on a later cast classifies the previous trace (S5 produced a prediction from a one-frame trace).
- [CODE] A trace finishing while the previous prediction thread is still running is dropped with no message beyond "Tracing Done!!" — [harry_potter_wand_cv.py:343-347](harry_potter_wand_cv.py#L343). The main thread also sleeps for 1 s after each trace, freezing the window — [harry_potter_wand_cv.py:350](harry_potter_wand_cv.py#L350).

**Feedback by stage** [CODE]

| Stage | Window | Console | LEDs / sound |
|---|---|---|---|
| Wand seen | Red circle on the keypoint ([:298](harry_potter_wand_cv.py#L298)) | Nothing | Nothing |
| Waiting out presence gate | No progress cue | Nothing | Nothing |
| Tracing | "Tracing...", blinking border, cyan line ([:371-374](harry_potter_wand_cv.py#L371)) | "Start Tracing!!" ([:179](harry_potter_wand_cv.py#L179)) | Nothing |
| Hold-still countdown | No cue | Nothing | Nothing |
| Trace complete | Freezes 1 s, returns to "Ready..." | "Tracing Done!!" | Nothing |
| Recognised and fired | No spell name; only two status strings exist ([:157](harry_potter_wand_cv.py#L157), [:178](harry_potter_wand_cv.py#L178)) | "Prediction: 0", "Alohamora!!" | Sound, LED and servo if enabled |
| Recognised but wrong state | Nothing | "Prediction: N" only | Nothing |
| Rejected / unknown | Does not exist | Does not exist | Does not exist |

- [CODE] `screen_flash_feedback` has no callers since commit 7e21647 removed the calls to fix a GUI freeze — [harry_potter_wand_cv.py:220](harry_potter_wand_cv.py#L220). LEDs ship disabled ([config.yaml:13](config.yaml#L13)), so a default install shows nothing in the window for a successful spell.
- [CODE] The LEDs are used only for the final effect, so someone watching the LEDs instead of a monitor gets no cue for wand-seen or tracing — [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261).

**No rejection, and a state lock that causes silence**
- [CODE] The classifier returns `clf.predict` directly — [harry_potter_wand_sklearn.py:35-39](harry_potter_wand_sklearn.py#L35). The pipeline is a plain `SVC()` — [DatasetCreation/train_spell_classifier.py:38](DatasetCreation/train_spell_classifier.py#L38).
- [SIM] The trained pipeline has no `predict_proba`, but `decision_function` is available. Results on non-spell input through the real preprocessing:

| Input | Predicted class | Decision value |
|---|---|---|
| Empty mask | 1 | +0.08 |
| Horizontal line | 1 | +0.13 |
| Vertical line | 1 | +0.01 |
| Tiny jitter | 1 | +0.09 |
| Circle | 0 | -0.31 |
| X | 0 | -0.07 |
| Zigzag | 1 | +0.02 |
| 300 random scribbles | 154 class 0, 146 class 1, none rejected | see below |

- [SIM] End to end, an X-shaped trace fired Alohamora (S10). Waving the wand around gave a prediction of 1 (S11).
- [SIM] A margin threshold alone would be weak. Held-out |decision| was 0.44 / 0.84 / 1.22 at the 5th / 50th / 95th percentiles, while random scribbles were 0.04 / 0.54 / 74. These distributions overlap heavily — `exp1.py`.
- [CODE + SIM] Spells are locked to alternate: `"0"` fires only when `lastMove == 0`, and `"1"` only when `lastMove == 1` — [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261). Repeating a correct cast does nothing except print the prediction (S6). The state is not persisted across restarts, and the comment on its meaning reads inverted compared with its use ([harry_potter_wand_cv.py:203](harry_potter_wand_cv.py#L203)).

**Train and live preprocessing differ (most serious finding)**
- [CODE] Training: a 300×300 canvas with a 7 px stroke, where the drawing fills the canvas, resized isotropically to 28×28 — [DatasetCreation/draw_spell_data.py:28](DatasetCreation/draw_spell_data.py#L28), [:45](DatasetCreation/draw_spell_data.py#L45), [:70](DatasetCreation/draw_spell_data.py#L70).
- [CODE] Live: the entire 640×480 frame is blurred, thresholded and squeezed to 28×28 with no crop, centring or aspect correction — [harry_potter_wand_cv.py:252-255](harry_potter_wand_cv.py#L252).
- [SIM] `cv2.dilate(mask, (3, 3))` passes a tuple, not a kernel. A single pixel dilates to 2 pixels, against 9 with `np.ones((3,3))` — `exp1.py`.
- [SIM] 101 held-out training samples were re-rendered as 7 px traces (skeletonised, redrawn) at different sizes and positions in a 640×480 frame, then run through the live preprocessing. The stock retrained model scores 99.0% on its own held-out data.

| Trace size | Position | Stock pipeline accuracy | Share predicted class 0 | Retrained on bounding-box-normalised traces |
|---|---|---:|---:|---:|
| 450 px | centre | 0.990 | 0.55 | 1.000 |
| 300 px | centre | 0.683 | 0.49 | 1.000 |
| 200 px | centre | 0.446 | 0.01 | 1.000 |
| 120 px | centre | 0.436 | 0.00 | 1.000 |
| 300 px | upper left | 0.871 | 0.53 | 1.000 |
| 300 px | lower right | 0.703 | 0.86 | 1.000 |
| 200 px | upper left | 0.594 | 0.89 | 1.000 |
| 200 px | lower right | 0.723 | 0.78 | 1.000 |

- [SIM] Live strokes are also fainter and sparser: 23 to 92 non-zero pixels at mean intensity about 71 to 77, against 111 pixels at about 110 in training data — `exp1.py`.
- Caveat on the table: the traces are synthetic re-renderings of mouse drawings, so wand jitter, blob dropouts and lens distortion are not modelled. The 1.000 column uses the same data source and is optimistic. It shows that size and position sensitivity can be removed, not that real-world accuracy would be 100%.

**Parameters hardcoded rather than in config.yaml** [CODE]
- `harry_potter_wand_cv.py`: resolution 640×480 ([:54](harry_potter_wand_cv.py#L54)); sound filenames ([:39-41](harry_potter_wand_cv.py#L39)); background loop always on ([:49-50](harry_potter_wand_cv.py#L49)); LED-mode blob flags ([:127-131](harry_potter_wand_cv.py#L127)); 10-point minimum and 0.05 frame period ([:188](harry_potter_wand_cv.py#L188)); trace thickness 7 ([:324](harry_potter_wand_cv.py#L324)); preprocessing values ([:252-255](harry_potter_wand_cv.py#L252)); post-trace sleeps ([:336](harry_potter_wand_cv.py#L336), [:350](harry_potter_wand_cv.py#L350)); the class-to-spell map ([:261-270](harry_potter_wand_cv.py#L261)).
- [SIM] LED mode leaves OpenCV's default convexity filter on at 0.95 and exposes it nowhere. A hard-edged synthetic disc was rejected until blurred — `dbg.py`. Whether real saturated LED blobs are affected is unknown.
- `utils/reflector_detector.py`: minimum convexity 0.5 ([:186](utils/reflector_detector.py#L186)), threshold step ([:169](utils/reflector_detector.py#L169)), 10-frame loss limit ([:267](utils/reflector_detector.py#L267)).
- `utils/animations.py`: duration, step counts and all colours ([:30-49](utils/animations.py#L30), [:82-113](utils/animations.py#L82)). `utils/audio.py`: duck ratio and 0.1 s duck time ([:18-22](utils/audio.py#L18)).
- `DatasetCreation/draw_spell_data.py`: `LABEL`, canvas size, stroke ([:21-28](DatasetCreation/draw_spell_data.py#L21)).

**Config keys that do nothing at runtime** [CODE, by grep across non-test Python]
- `hardware.camera.*`: `set_controls` appears only in the calibrator ([calibrate_reflector.py:174](calibrate_reflector.py#L174)), and the main script configures only size and format ([harry_potter_wand_cv.py:53-57](harry_potter_wand_cv.py#L53)). Yet the wizard prompts for these values ([setup_wizard.py:62-66](setup_wizard.py#L62)) and the docs prescribe changing them to fix detection ([docs/CONFIGURATION.md:288-296](docs/CONFIGURATION.md#L288)).
- `audio.spell_volume`: no `Sound.set_volume` call exists, contradicting [docs/CONFIGURATION.md:633](docs/CONFIGURATION.md#L633).
- `hardware.ir_illuminator.*`: read only by the wizard, tests and a permissions check ([config_loader.py:120](config_loader.py#L120)). No code drives the pin.
- `paths.lastframe_file`: `LASTFRAME_PATH` is assigned and never used in the main script ([harry_potter_wand_cv.py:27](harry_potter_wand_cv.py#L27)).

### Inferences
- [INFERRED] Using the repo's stated 120° field of view ([docs/research/CAMERA_MODULE_3_NOIR_RESEARCH.md:32](docs/research/CAMERA_MODULE_3_NOIR_RESEARCH.md#L32)) and casting distance of 1 to 2 m ([docs/TECHNICAL_GUIDE.md:486](docs/TECHNICAL_GUIDE.md#L486)), and treating 120° as the diagonal of a rectilinear 4:3 view, a 60 cm arm gesture spans roughly 70 to 140 px. That is the band where the simulated model predicts class 1 for nearly everything.
- [INFERRED] Combined with the state lock, this predicts the likely first experience: Alohamora is required first, the model answers class 1, and nothing happens with no explanation. The README's "draw more deliberately" advice ([README.md:270](README.md#L270)) would not help. This needs confirming on hardware.
- [INFERRED] The default Picamera2 path probably runs with auto-exposure, because no controls are set. The docs recommend disabling it ([docs/TECHNICAL_GUIDE.md:423](docs/TECHNICAL_GUIDE.md#L423)), so blob brightness at runtime may vary with the scene.

### Gaps
- Real achieved frame rate on a Pi 5 with two `imshow` windows was not measurable, so the real hold-still time is unknown.
- Real wand gesture sizes and real classification accuracy were not measured.

## Does it need a display, and how does it behave headless, at boot, on failure and on crash?

### Takeaway
The main script is a desktop foreground program. It calls `imshow` unconditionally on every frame, has no CLI flags, no logging and no service or autostart, and audio and camera failures at startup are unguarded. It cannot be run as an appliance without code changes.

### Cited Findings
- [CODE] `cv2.imshow` is called unconditionally for two windows on every frame, and exit depends on `waitKey` seeing `q` — [harry_potter_wand_cv.py:376-381](harry_potter_wand_cv.py#L376). The script has no `argparse` or `sys.argv` use (grep across the main script, calibrator and dataset scripts returned no hits).
- [CODE] No systemd unit, autostart or `logging` usage exists in the repo. Output is `print` only. The original install plan's "Optional systemd service setup" remains unchecked — [PRPs/tasks/automated-installation-setup.md:35](PRPs/tasks/automated-installation-setup.md#L35).
- [CODE] Failure handling at startup and during a run:

| Failure | Behaviour | Source |
|---|---|---|
| No audio device or missing mp3 | Unguarded module-level call; startup aborts | [harry_potter_wand_cv.py:37-50](harry_potter_wand_cv.py#L37) |
| No camera or camera busy | Unguarded; startup aborts | [harry_potter_wand_cv.py:53-57](harry_potter_wand_cv.py#L53) |
| Camera error mid-run | `finally` cleans up and the process exits; no retry | [harry_potter_wand_cv.py:279-392](harry_potter_wand_cv.py#L279) |
| LED init fails | Warning printed, continues with no LEDs | [harry_potter_wand_cv.py:104-106](harry_potter_wand_cv.py#L104) |
| Servo init fails | Warning printed, continues with no servo | [harry_potter_wand_cv.py:81-83](harry_potter_wand_cv.py#L81) |
| Invalid YAML | Caught as `SystemExit`; prints "config.yaml not found" and silently falls back to defaults (LED, servo and reflector mode off) | [harry_potter_wand_cv.py:15-22](harry_potter_wand_cv.py#L15), [config_loader.py:58-60](config_loader.py#L58) |

- [SIM] Missing model: the app starts normally and only fails on the first cast, with a traceback from the prediction thread. It then keeps running and fails again on every cast (S7). `validate_assets` exists but only `test_setup.py` and the module's own `__main__` call it — [config_loader.py:77](config_loader.py#L77), [test_setup.py:89](test_setup.py#L89).
- [CODE] Cleanup in `finally` does not stop the camera — [harry_potter_wand_cv.py:383-392](harry_potter_wand_cv.py#L383). No SIGTERM handler exists.
- [CODE] `pigpio` is the only servo pin factory — [harry_potter_wand_cv.py:66-69](harry_potter_wand_cv.py#L66), and the docs instruct users to enable it ([docs/TECHNICAL_GUIDE.md:636-638](docs/TECHNICAL_GUIDE.md#L636)). A pigpio collaborator states "pi5 is not supported by pigpio" and calls a port a "non starter" without hardware-interface assurances — [pigpio issue #589](https://github.com/joan2937/pigpio/issues/589).
- [CODE] Paths are resolved from the project root, so running from another working directory is fine, which helps a future service — [config_loader.py:38](config_loader.py#L38), [config_loader.py:62-75](config_loader.py#L62).

**Stray and stale artefacts**
- [CODE] `lastframe.jpg` is a tracked 28×28 greyscale image last changed in the first commit (24d7414), showing the "close" shape. Writing to it stopped in 6a364c3, so it is a frozen fixture, not a debug output.
- [CODE] Docs still present it as live: "Check last saved trace: `lastframe.jpg`" ([docs/TECHNICAL_GUIDE.md:977](docs/TECHNICAL_GUIDE.md#L977)) and "Temp file for predictions" ([docs/CONFIGURATION.md:645](docs/CONFIGURATION.md#L645)). Running `harry_potter_wand_sklearn.py` directly only classifies this one file — [harry_potter_wand_sklearn.py:68-84](harry_potter_wand_sklearn.py#L68).
- [CODE] As a result, a user currently has no way to see the 28×28 image the classifier actually received.
- [CODE] `__pycache__/HarryPotterWandsklearn.cpython-311.pyc` is tracked despite the ignore rule, under an old module name (`git ls-files`).
- [CODE] `*.pkl` is ignored, so a fresh clone has no model — [.gitignore](.gitignore), commit 115bfb8.

### Inferences
- [INFERRED] With pip `opencv-python` ([install.sh:92](install.sh#L92)) and no `DISPLAY`, the Qt backend typically aborts the process, which would skip the `finally` cleanup. Starting at boot would need a logged-in desktop session.
- [INFERRED] Because servo init falls back to a printed warning, a Pi 5 user who enables the servo would likely see it silently do nothing, since the pigpio daemon cannot run on that board. gpiozero's lgpio factory is the probable replacement.
- [INFERRED] A systemd stop (SIGTERM) would skip `finally`, potentially leaving LEDs lit, since Python's default SIGTERM handling does not unwind.
- [INFERRED] The first cast probably has extra latency because `joblib.load` is lazy and pulls in scikit-learn at that moment — [harry_potter_wand_sklearn.py:19-20](harry_potter_wand_sklearn.py#L19).

### Gaps
- Actual headless behaviour on the Pi was not tested. The Mac "headless" wheel still includes a Cocoa GUI backend (`imshow` did not raise), so it says nothing about Linux.
- Exact exception types for audio and camera failures were not observed, because those modules were stubbed.

## How much tuning does the reflector calibrator require, what is automatic, and how do lighting and IR interference affect it?

### Takeaway
The calibrator exposes 10 hand-tuned knobs and automates only one of them, poorly. It also tests a different detection pipeline, at different camera settings, from the one used at runtime, so settings tuned in it are not guaranteed to transfer. It has a verified re-acquisition bug, and saving wipes all comments from `config.yaml`. LED mode has no calibrator at all.

### Cited Findings

**Knob count and automation**
- [CODE] 10 knobs in the calibrator — [calibrate_reflector.py:63-74](calibrate_reflector.py#L63). The README table documents only 5 — [README.md:184-190](README.md#L184).
- [SIM] `config.yaml` holds 14 reflector values, 6 LED blob values and 3 gesture values, out of 48 settings in total. Gesture thresholds, Kalman noise values and MOG2 learning rate cannot be tuned in the calibrator — `exp3.py`.
- [CODE] Auto-calibrate (`a`) sets only `brightness_threshold`, to 70% of the mean brightness of moving pixels above 50, over 60 frames with no countdown — [calibrate_reflector.py:326-358](calibrate_reflector.py#L326). Any moving object contributes, not only the wand.
- [CODE] The overlay shows a different "Suggested" number, 80% of the frame's maximum brightness, which includes static lamps and is not tied to the wand — [calibrate_reflector.py:318-324](calibrate_reflector.py#L318).
- [CODE] Positive points: the tool has useful views, a noise percentage, a detection counter and step sizes — [calibrate_reflector.py:386-450](calibrate_reflector.py#L386).

**Calibrator does not match runtime**
- [CODE] Camera: the calibrator hardcodes `ExposureTime` 8000, `AnalogueGain` 6.0, `Brightness` -0.3 and ignores config — [calibrate_reflector.py:174-178](calibrate_reflector.py#L174). The main app sets no controls — [harry_potter_wand_cv.py:53-57](harry_potter_wand_cv.py#L53).
- [CODE] Detection differences:

| Aspect | Calibrator | Runtime `ReflectorDetector` |
|---|---|---|
| Kalman filter | None | Yes ([:234-279](utils/reflector_detector.py#L234)) |
| Blob input | Inverted mask ([:270-271](calibrate_reflector.py#L270)) | Direct mask ([:218](utils/reflector_detector.py#L218)) |
| Colour filter | Off ([:234](calibrate_reflector.py#L234)) | On, 255 ([:189-190](utils/reflector_detector.py#L189)) |
| Convexity filter | Off ([:233](calibrate_reflector.py#L233)) | On, 0.5 ([:185-186](utils/reflector_detector.py#L185)) |
| Candidate choice | Brightest ([:277-283](calibrate_reflector.py#L277)) | Largest ([:223](utils/reflector_detector.py#L223)) |
| Morph kernel | Square ([:77](calibrate_reflector.py#L77)) | Ellipse ([:30](utils/reflector_detector.py#L30)) |
| Gesture trigger shown | No | n/a, trace logic in main script |

- [SIM] Same synthetic sequence fed to both (dot passes, disappears, reappears far away). Valid-detection frames:

| Phase | Runtime | Calibrator |
|---|---|---|
| Initial pass | 38/40 | 38/40 |
| Wand gone | 9/30 (Kalman ghost positions) | 0/30 |
| Reappears far away | 38/40 | **0/40** |

- [CODE + SIM] The 0/40 is a calibrator bug: `last_position` is not cleared when detection is lost, and a far-away reappearance is rejected as an outlier indefinitely — [calibrate_reflector.py:288-297](calibrate_reflector.py#L288). The overlay would read "NO DETECTION", inviting the user to tune thresholds for a problem thresholds cannot fix.
- [CODE] Default mismatch: the detector's fallback brightness is 120 after commit 75b79aa called 180 a regression ([utils/reflector_detector.py:42](utils/reflector_detector.py#L42)), while config, wizard and calibrator all use 180 ([config.yaml:79](config.yaml#L79), [utils/config_builder.py:45](utils/config_builder.py#L45), [calibrate_reflector.py:64](calibrate_reflector.py#L64)). In [SIM], a tip of brightness 150 produced no detection and no message at the shipped 180 (S9d).

**Saving and applying**
- [CODE] `q` saves immediately and forces `wand_type: reflector` — [calibrate_reflector.py:469-471](calibrate_reflector.py#L469), [:606](calibrate_reflector.py#L606).
- [SIM] Saving on a copy of `config.yaml` took it from 100 to 66 lines and from 44 `#` characters to 0, and flipped `wand_type` from led to reflector — `exp3.py`. The inline comments are the file's built-in documentation.
- [CODE] Settings apply on the next launch of the main script, since values are cached at init — [utils/reflector_detector.py:52-59](utils/reflector_detector.py#L52). There is no way to test a real cast inside the calibrator.
- [CODE] Re-running the wizard writes fixed reflector defaults — [utils/config_builder.py:31-54](utils/config_builder.py#L31).
- [CODE] Controls are inconsistent: the docstring says brightness is ±10 ([calibrate_reflector.py:18](calibrate_reflector.py#L18)), but the default multiplier of 2 makes it ±20 ([:88](calibrate_reflector.py#L88), [:489](calibrate_reflector.py#L489)). The README lists uppercase keys while the handler checks lowercase only ([README.md:186](README.md#L186), [calibrate_reflector.py:469](calibrate_reflector.py#L469)). Space resets everything without confirmation ([:569](calibrate_reflector.py#L569)).

**Lighting and IR interference**
- [SIM] LED mode has no background model and uses `points_array[0]`, the first blob — [harry_potter_wand_cv.py:296](harry_potter_wand_cv.py#L296), [:305](harry_potter_wand_cv.py#L305). A static bright spot low in the frame blocked tracing completely (S8b). A static spot high in the frame let tracing run but changed the result from class 0 to class 1, with no spell fired (S8).
- [SIM] Reflector mode handled the same static lamp correctly, giving the same result as with no lamp (S9b). This is a real strength of the MOG2 approach. It requires motion, however, so it conflicts with the hold-still design.
- [CODE] Thresholds are fixed values with no adaptation and no exclusion-zone option — [utils/reflector_detector.py:208](utils/reflector_detector.py#L208).
- [CODE] The docs put environment control on the user: "Ensure room has no other bright IR sources (sunlight, reflections)" ([docs/TECHNICAL_GUIDE.md:797](docs/TECHNICAL_GUIDE.md#L797)), plus a matte black backdrop and removing glass, glossy and metal surfaces ([docs/research/IR_ILLUMINATOR_INTEGRATION_RESEARCH.md:405-422](docs/research/IR_ILLUMINATOR_INTEGRATION_RESEARCH.md#L405)).
- [CODE] The project's own task file records the pain: "Wand not detected reliably, false positives, lighting issues" and "Keyboard controls awkward" — [PRPs/tasks/calibrate-reflector-fine-tuning.md:16-17](PRPs/tasks/calibrate-reflector-fine-tuning.md).

### Inferences
- [INFERRED] Fixed exposure in the calibrator against probable auto-exposure at runtime means a brightness threshold tuned in one may not hold in the other. The sequence of threshold reverts in git history is consistent with tuning being unstable, though it does not prove the cause.
- [INFERRED] In daylight, a NoIR sensor will likely see windows and sunlit surfaces as bright regions. LED mode would be the most affected, given S8 and S8b.

### Gaps
- No real IR data was available. Sunlight, IR remotes, glossy reflections, people moving and exposure drift could not be tested. The synthetic scenes show only logic behaviour.
- The time a person needs to reach a working calibration is unknown.

## Does the "Add Your Own Spells" flow work as documented?

### Takeaway
No. The README's three commands cannot create a new spell, and following them silently damages the existing "close" class, because the converter labels anything not containing "open" as class 1. `train_spell_classifier.py` exists and works, and retraining itself is quick. The real costs are mouse-only data capture, a hardcoded binary label, and code edits in 4 files. The training guide describes behaviour the scripts do not have.

### Cited Findings

**The flow against the code**
- [CODE] The README says "It's easy" and "That's it! The new spell will be recognized" — [README.md:209](README.md#L209), [README.md:224](README.md#L224).
- [CODE] Step 1 has no label argument: `LABEL = "close"` must be edited in source ([DatasetCreation/draw_spell_data.py:21](DatasetCreation/draw_spell_data.py#L21)). Neither guide mentions this; the training guide only says "label with class number" ([docs/TRAINING_CUSTOM_SPELLS.md:94](docs/TRAINING_CUSTOM_SPELLS.md#L94)).
- [CODE] Step 2 is binary: `label = 0 if "open" in file.lower() else 1` ([DatasetCreation/convert_to_training_data.py:32](DatasetCreation/convert_to_training_data.py#L32)).
- [SIM] Running that expression: `lumos_1.png` gives 1, `incendio_1.png` gives 1, `2_1.png` gives 1, `reopen_1.png` gives 0 — `exp3.py`. New samples merge into Colloportus with no warning, and the guide never mentions changing this line.
- [CODE] Step 3 trains normally, and the runtime only handles `"0"` and `"1"` — [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261).
- [CODE] Data loss: `counter = 0` on each launch, so re-running overwrites `label_0.png` onward — [DatasetCreation/draw_spell_data.py:33](DatasetCreation/draw_spell_data.py#L33), [:71](DatasetCreation/draw_spell_data.py#L71). Space also saves a blank canvas without checking — [:67-76](DatasetCreation/draw_spell_data.py#L67).

**Mouse versus wand**
- [CODE] Yes, drawing is mouse-only. It uses a mouse callback on a 300×300 window and never touches the camera, detector or wand — [DatasetCreation/draw_spell_data.py:36-53](DatasetCreation/draw_spell_data.py#L36). The guide confirms "Mouse or drawing tablet" ([docs/TRAINING_CUSTOM_SPELLS.md:30](docs/TRAINING_CUSTOM_SPELLS.md#L30)).
- [SIM] The mismatch is measurable, as shown in the size and position table in the first section. The reported 99% test accuracy is mouse-on-mouse, so it overstates live performance — `exp1.py`.
- [CODE] This also needs a desktop session and a mouse on, or forwarded to, the machine.

**Samples and retraining**
- [CODE] Guidance is 50 to 100 samples per spell ([README.md:214](README.md#L214)), with a 30 minimum ([docs/TRAINING_CUSTOM_SPELLS.md:156-157](docs/TRAINING_CUSTOM_SPELLS.md#L156)). The shipped dataset has 201 samples per class (402 total) — verified by counting `spells_dataset/` and `y_spells.npy`.
- [SIM] `train_spell_classifier.py` exists at `DatasetCreation/` and is tracked. Its grid is 180 combinations × 5 folds = 900 fits, which took 2.3 to 4.0 s on a 10-core Mac and scored 0.990 on held-out data. Best parameters were `poly`, C=0.1, gamma=0.01, degree=2 — `exp1.py`.
- [CODE] There is no per-class report in the converter, despite the guide promising one ([DatasetCreation/convert_to_training_data.py:56](DatasetCreation/convert_to_training_data.py#L56), [docs/TRAINING_CUSTOM_SPELLS.md:198](docs/TRAINING_CUSTOM_SPELLS.md#L198)). The split is unstratified ([DatasetCreation/train_spell_classifier.py:31-33](DatasetCreation/train_spell_classifier.py#L31)).

**Edits needed for one new spell** [CODE]

| # | File | Site | Documented? |
|---|---|---|---|
| 1 | `DatasetCreation/draw_spell_data.py` | `LABEL` ([:21](DatasetCreation/draw_spell_data.py#L21)) | No |
| 2 | `DatasetCreation/convert_to_training_data.py` | Label map ([:32](DatasetCreation/convert_to_training_data.py#L32)) | No, and this is the blocker |
| 3 | `utils/animations.py` | Fade colours ([:37-46](utils/animations.py#L37)) | Yes, but pointed at the wrong file and old signature |
| 4 | `utils/animations.py` | Animation colours ([:106-113](utils/animations.py#L106)) | Same |
| 5 | `utils/animations.py` | Servo direction ([:73](utils/animations.py#L73), [:97](utils/animations.py#L97)) | No |
| 6 | `harry_potter_wand_cv.py` | Sound load, in 2 branches ([:39-45](harry_potter_wand_cv.py#L39)) | Partly, with removed variables |
| 7 | `harry_potter_wand_cv.py` | Dispatch ([:261-270](harry_potter_wand_cv.py#L261)) | Yes, with an outdated snippet |
| 8 | `config_loader.py` (optional) | Asset check ([:82-87](config_loader.py#L82)) | No |

- That is **4 files and 7 to 8 edit sites**, plus an mp3 and 50 to 100 mouse samples. Site 2 is required for correct training at all.
- [CODE] In the real animation code, any spell other than "open" uses blue colours, and the servo moves for every spell. The guide's snippet shows a gate `if target_func in ["open", "close"]` that does not exist — [utils/animations.py:97](utils/animations.py#L97), [:110](utils/animations.py#L110), [docs/TRAINING_CUSTOM_SPELLS.md:316](docs/TRAINING_CUSTOM_SPELLS.md#L316).

**Guide statements that are false or stale** [CODE]
- Claims the converter "Centers all drawings, Normalizes size, Smooths paths, Resamples" ([docs/TRAINING_CUSTOM_SPELLS.md:190-195](docs/TRAINING_CUSTOM_SPELLS.md#L190)). It only flattens pixels ([DatasetCreation/convert_to_training_data.py:36-41](DatasetCreation/convert_to_training_data.py#L36)).
- Says `python3 harry_potter_wand_sklearn.py` lets you "Wave your wand" ([docs/TRAINING_CUSTOM_SPELLS.md:236-239](docs/TRAINING_CUSTOM_SPELLS.md#L236)). It classifies the frozen `lastframe.jpg` once.
- Tells users to edit `spell_fade_out` and `move_servo_smoothly` in `harry_potter_wand_cv.py` at "Line ~88" and "Line ~112" ([docs/TRAINING_CUSTOM_SPELLS.md:245-249](docs/TRAINING_CUSTOM_SPELLS.md#L245)), though these moved to `utils/animations.py`. The same guide says so at [:114](docs/TRAINING_CUSTOM_SPELLS.md#L114).
- Its snippets use `PROJECT_DIR` and `cv2.imwrite(LASTFRAME_PATH...)`, which no longer exist ([docs/TRAINING_CUSTOM_SPELLS.md:388-391](docs/TRAINING_CUSTOM_SPELLS.md#L388), [:443](docs/TRAINING_CUSTOM_SPELLS.md#L443)).
- Quick Start runs the main script from inside `DatasetCreation/` without `cd ..` ([docs/TRAINING_CUSTOM_SPELLS.md:92-105](docs/TRAINING_CUSTOM_SPELLS.md#L92)).
- Expected training output does not match the script's prints ([docs/TRAINING_CUSTOM_SPELLS.md:218-222](docs/TRAINING_CUSTOM_SPELLS.md#L218), [DatasetCreation/train_spell_classifier.py:57-60](DatasetCreation/train_spell_classifier.py#L57)).
- The stock gestures are described as "upward swirl" and "downward swirl" ([docs/TECHNICAL_GUIDE.md:786](docs/TECHNICAL_GUIDE.md#L786)). Viewing the dataset, "open" is a circle with a vertical stroke through it, and "close" is a P or flag shape. The README does not show the shapes at all, so a new user is not told what to draw.

**Model loading and versioning**
- [SIM] The model is a plain `Pipeline(StandardScaler, SVC)` with no custom classes, and it saved and loaded correctly via joblib in the same environment. The file is about 351 KB — `exp1.py`.
- [CODE] There is no versioning. It overwrites one fixed path ([DatasetCreation/train_spell_classifier.py:63](DatasetCreation/train_spell_classifier.py#L63)) and saves no class names, training date, sample counts or library versions. The guide tells users to back it up manually ([docs/TRAINING_CUSTOM_SPELLS.md:812](docs/TRAINING_CUSTOM_SPELLS.md#L812)).
- [CODE] The project already removed a shipped model because it was version-bound (commit 115bfb8), yet the pin is an open-ended `scikit-learn>=1.6.0` — [install.sh:93](install.sh#L93).
- scikit-learn states loading across versions is "entirely unsupported and inadvisable" and may give wrong results or crash, and recommends saving training-data references, code, dependency versions and CV score — [scikit-learn model persistence](https://scikit-learn.org/stable/model_persistence.html).
- [CODE] `test_setup.py` checks only that the file loads — [test_setup.py:238-243](test_setup.py#L238).
- [CODE] No test covers `GestureState`, `ReflectorDetector`, prediction or the converter; only a syntax test references the scripts — [tests/test_syntax.py:38](tests/test_syntax.py#L38). This is how the defects above persisted.

### Inferences
- [INFERRED] A user following the README would train successfully, see high accuracy, and then find Colloportus worse with no new spell, giving a confusing failure that points nowhere.
- [INFERRED] Retraining on a Pi 5 should take seconds to perhaps a minute given the small dataset, so data capture rather than compute is the bottleneck.

### Gaps
- Pi 5 training time was not measured.
- Loading across scikit-learn versions was not tested directly; the finding relies on the upstream docs and the project's commit message.

## How are effects configured, and could a user trigger something other than LEDs without changing code?

### Takeaway
No. Spell-to-effect mapping is hardcoded in Python, there is no `spells` section in config, and no hook, plugin, command or network mechanism exists. Only global settings such as LED count, volume and on/off flags can be changed without code.

### Cited Findings
- [CODE] The whole mapping is one `if/elif` in the prediction thread — [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261).
- [CODE] `config.yaml` has no per-spell settings; its sections are project, hardware, detection, audio and paths — [config.yaml:4-100](config.yaml#L4).
- [CODE] Colours are inline branches in two functions, with `else` falling through to blue — [utils/animations.py:37-46](utils/animations.py#L37), [:106-113](utils/animations.py#L106). `move_servo_smoothly` bundles LED and servo together, so they cannot be selected independently per spell — [utils/animations.py:55](utils/animations.py#L55).
- [CODE] Sounds are fixed filenames, so swapping the mp3 under the same name is the only no-code customisation — [harry_potter_wand_cv.py:39-41](harry_potter_wand_cv.py#L39).
- [CODE] Ducking lasts just 0.1 s rather than the length of the spell sound — [utils/audio.py:18-22](utils/audio.py#L18), against [docs/CONFIGURATION.md:631](docs/CONFIGURATION.md#L631). The background loop has no off switch, though `background_volume: 0` should silence it — [harry_potter_wand_cv.py:49-50](harry_potter_wand_cv.py#L49).
- [CODE] A grep of non-test Python for `mqtt`, `webhook` and `requests` found nothing. `subprocess` appears only in `test_setup.py` and `setup_wizard.py`.
- [CODE] Existing tools: `test_led_demo.py` lets users preview LEDs ([README.md:236-240](README.md#L236)), but its effects are not tied to spells.

### Inferences
- [INFERRED] The only no-code route to a smart-home action is scraping stdout from a wrapper ("Alohamora!!"). That is fragile, would need unbuffered output, and still needs a display. In practice users must edit `threaded_predict`.
- [INFERRED] Adding actions directly in `threaded_predict` is safe in terms of threads, since it is already off the main loop, but a slow network call would extend the `predicting` window and cause more dropped casts.

### Gaps
- Whether users actually want smart-home triggers is not evidenced in the repo; no issue tracker data was reviewed.

## Ranked pain points and concrete fixes

### Takeaway
The top priority is recognition: normalise traces in one shared function and capture training data with the wand, because no amount of tuning or UI can compensate for a classifier fed a differently shaped input. Next come rejection and visible outcomes, then a data-driven spell registry, then headless operation. Several high-value fixes are only a few lines.

### Cited Findings

Severity reflects user impact. Effort is my estimate, not a measurement.

| # | Severity | Pain point | Evidence | Concrete fix | Effort |
|---|---|---|---|---|---|
| 1 | Blocker | Live trace not normalised; accuracy depends on size and position | [SIM] 0.99 to 0.44; [harry_potter_wand_cv.py:252-255](harry_potter_wand_cv.py#L252) | Add one `preprocess_trace(points)` used by training and runtime: bounding-box crop, square pad, re-render from the point list at fixed stroke. Fix the `dilate` kernel. Retrain. [SIM] gave 1.000 across tested sizes and positions (optimistic) | Low |
| 2 | Blocker | README's add-spell flow silently corrupts class 1 and cannot add a spell | [DatasetCreation/convert_to_training_data.py:32](DatasetCreation/convert_to_training_data.py#L32), [README.md:224](README.md#L224) | Use a `spells.yaml` registry and `spells_dataset/<name>/` folders; derive labels from them; fail on unknown labels. Correct the README now, even before the code changes | Medium |
| 3 | High | Training uses a mouse, not the wand | [DatasetCreation/draw_spell_data.py:36-53](DatasetCreation/draw_spell_data.py#L36) | Add `capture_spell.py --label lumos` using the real detector and trace logic: prompts, auto-save, undo last, next-free index. Keep the mouse tool as a supplement. Fixes the overwrite bug at [:33](DatasetCreation/draw_spell_data.py#L33) | Medium |
| 4 | High | No rejection; every trace becomes a spell | [SIM] 300 of 300 scribbles classified, X fired Alohamora; [harry_potter_wand_sklearn.py:38](harry_potter_wand_sklearn.py#L38) | Add a trained "none" class of scribbles, plus a `min_confidence` config using `decision_function` or calibrated probabilities. Margin alone overlaps, per [SIM], so the negative class is needed. Add a trace-quality gate (minimum path length and bounding box) | Medium |
| 5 | High | Outcome is invisible, and wrong-state casts are silent | [harry_potter_wand_cv.py:220](harry_potter_wand_cv.py#L220), [:261-270](harry_potter_wand_cv.py#L261); [SIM] S6 | Send events from the thread to the main loop via a queue; overlay the spell name, confidence and 28×28 input; show "already open". Make the lock optional per spell | Low |
| 6 | High | Requires a display; no service, logs or appliance mode | [harry_potter_wand_cv.py:376-381](harry_potter_wand_cv.py#L376), [PRPs/tasks/automated-installation-setup.md:35](PRPs/tasks/automated-installation-setup.md#L35) | Add `--headless` (or auto-detect), `logging` to journald, a shipped systemd unit with restart, a SIGTERM handler, and camera and audio retries | Medium |
| 7 | High | Camera config is a no-op, yet the wizard and docs rely on it; the calibrator uses different settings | [harry_potter_wand_cv.py:53-57](harry_potter_wand_cv.py#L53), [calibrate_reflector.py:174-178](calibrate_reflector.py#L174), [docs/CONFIGURATION.md:288-296](docs/CONFIGURATION.md#L288) | Create one `open_camera(config)` used by both, applying size and controls, with `AeEnable: False` | Low |
| 8 | High | Crash and wrong-trace bugs; cancellation is dead code | [SIM] S4, S5, S12; [harry_potter_wand_cv.py:186-188](harry_potter_wand_cv.py#L186), [:358](harry_potter_wand_cv.py#L358) | Clear the frame on reset, guard `None`, apply a minimum check on both end paths, and count only points that moved. Add unit tests by extracting `GestureState` into a module | Low |
| 9 | Medium | Trigger depends on frame rate and per-frame speed; presence gate clips the gesture; reflector hold-still does not fire | [SIM] S1b, S2, S3, S9; [harry_potter_wand_cv.py:188](harry_potter_wand_cv.py#L188) | Use real timestamps. Define "still" as staying inside a radius of about 15 px for `stillness_duration`. Keep a ring buffer so the pre-start path is included. Add a max trace time. Show a shrinking ring as a countdown | Medium |
| 10 | Medium | No ambient feedback for screen-free use | [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261) | Add LED states in a small state machine: dim glow when wand seen, pulse when tracing, red blink on reject | Low to medium |
| 11 | Medium | Calibrator differs from runtime and can get stuck | [SIM] 0/40; [calibrate_reflector.py:288-297](calibrate_reflector.py#L288) | Make the calibrator call `ReflectorDetector` directly, clear `last_position` on loss, and add a test-cast mode showing the gesture trigger | Medium |
| 12 | Medium | Too many manual knobs, with weak automation | [calibrate_reflector.py:63-74](calibrate_reflector.py#L63), [:326-358](calibrate_reflector.py#L326) | Guided wizard: capture 3 s of empty scene to set noise floor and mask static sources, then 5 s of waving to measure tip brightness and size, then derive thresholds. Hide the raw knobs under "advanced" | Medium |
| 13 | Medium | Static IR sources block or corrupt LED mode | [SIM] S8, S8b; [harry_potter_wand_cv.py:305](harry_potter_wand_cv.py#L305) | Choose the blob nearest the tracked position, ignore blobs static for several seconds, and add a config exclusion mask | Low to medium |
| 14 | Medium | Effects are hardcoded; no non-LED actions | [harry_potter_wand_cv.py:261-270](harry_potter_wand_cv.py#L261) | Make the registry data-driven: `spells: lumos: {sound, led: {palette}, servo, actions: [{http}, {mqtt}, {shell}]}`. Run actions in a worker with a timeout, and separate LED and servo functions | Medium |
| 15 | Medium | Failures surface late or misleadingly | [SIM] S7; [harry_potter_wand_cv.py:15-22](harry_potter_wand_cv.py#L15), [:37](harry_potter_wand_cv.py#L37) | Run a startup preflight: call `validate_assets`, load the model up front, degrade to silent if audio fails, and stop misreporting invalid YAML as missing | Low |
| 16 | Medium | Servo path uses pigpio, unsupported on Pi 5 | [harry_potter_wand_cv.py:66-69](harry_potter_wand_cv.py#L66), [pigpio #589](https://github.com/joan2937/pigpio/issues/589) | Switch to gpiozero's lgpio factory and test on hardware. Update the docs at [docs/TECHNICAL_GUIDE.md:636-638](docs/TECHNICAL_GUIDE.md#L636) | Low |
| 17 | Low to medium | Calibrator save wipes config comments and flips mode | [SIM] 44 to 0; [calibrate_reflector.py:606](calibrate_reflector.py#L606), [:641](calibrate_reflector.py#L641) | Save with `ruamel.yaml` or to a separate `calibration.yaml` overlay. Keep a backup, and don't change `wand_type` | Low |
| 18 | Low to medium | Model has no version or metadata | [DatasetCreation/train_spell_classifier.py:63](DatasetCreation/train_spell_classifier.py#L63), [install.sh:93](install.sh#L93) | Save `{model, classes, sklearn_version, cv_score, trained_at, sample_counts}`, keep timestamped copies, and at load time warn and offer retraining on mismatch | Low |
| 19 | Low to medium | Docs are stale and sometimes false; stale artefacts remain | [docs/TRAINING_CUSTOM_SPELLS.md:190-195](docs/TRAINING_CUSTOM_SPELLS.md#L190), [docs/TECHNICAL_GUIDE.md:977](docs/TECHNICAL_GUIDE.md#L977), [:786](docs/TECHNICAL_GUIDE.md#L786) | Rewrite the guide after #2. Show gesture images in the README. Replace `lastframe.jpg` with a real debug output under an ignored directory. Remove the tracked `.pyc` | Low |

**Suggested order.** Quick wins are #8, #1, #7, #5 and the README correction from #2. Then #3 and #4 (both depend on #1's shared function), followed by #2 and #14 as one registry piece, then #6 and #10. #9 should be retested after #1, since the trigger timing affects the trace shape.

### Inferences
- [INFERRED] Items 1 and 3 should be done together: a wand-captured dataset passed through the same normaliser removes most of the train and live mismatch, and it also makes the 50 to 100 sample burden more meaningful.
- [INFERRED] Normalising removes absolute size and position, so a small flick would look like a full gesture. This is the main reason #4's quality gate should ship alongside #1.
- [INFERRED] Raw 28×28 pixel SVMs discard stroke order. Point-sequence recognisers, such as a $1-style template matcher, could reduce the sample requirement to a handful and give a natural distance-based rejection. This is worth a spike, but I did not test it.

### Gaps
- All severities rest on code and simulation. A short hardware session should confirm #1 first: log real traces at 1 m and 2 m, and measure stock accuracy with the wand. It would also capture real frame rate, exposure behaviour and IR interference, none of which could be measured here.
- No user reports or issue-tracker data were reviewed, so rankings reflect expected rather than observed user pain.
