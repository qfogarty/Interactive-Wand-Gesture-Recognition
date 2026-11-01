# Recognition, Segmentation, Calibration and Feedback Techniques for a Single-Point IR Wand on Raspberry Pi 5

Evidence labels used below:

- **[STYLUS/TOUCH]**, **[MOUSE]**, **[KINECT]**, **[GAZE]**: the input modality of the study. Almost none of the numeric evidence comes from a single-point air-wand tracker.
- **[REPO]**: read directly from this project's code on 2026-11-01. Not a measurement on the Pi.
- **[SNIPPET]**: taken from a search summary or project page. I did not read the full text.
- **[LOW QUALITY]**: vendor page, forum post or blog, with no stated method.

## Q1. Few-shot and template recognisers vs. SVM-on-image vs. small CNN/TCN

### Takeaway
Template recognisers on the ordered trajectory are the only option here with published evidence for adding a gesture from 1-10 examples, and they should comfortably run on a Pi 5. All of the strong numbers come from stylus or touch input, so expect lower accuracy in air and measure it. I found no comparable few-sample evidence for SVM-on-image or small CNN/TCN.

### Cited Findings

**$1 unistroke [STYLUS/TOUCH]**
- Study: 10 subjects, 16 gesture types, 10 entries each at 3 speeds (4,800 gestures), plastic stylus on an HP iPAQ Pocket PC, tested within-user (user-dependent) — [Wobbrock et al., UIST 2007](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- Error by templates per gesture: $1 fell from 2.73% (SD 2.38) at 1 template to 0.45% (0.64) at 9. DTW fell from 2.14% (1.76) to 0.54% (0.84). Rubine (statistical features) fell from 16.03% (5.98) at 2 examples to 4.70% (3.03) at 9 and cannot train on 1 — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- Overall recognition was 99.02% for $1 and 99.15% for DTW, not significantly different. Rubine had 7.17% errors — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- Mean gesture durations were 1761 ms (slow), 1153 ms (medium) and 668 ms (fast), with errors of 2.84%, 2.46% and 3.22% — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- By default $1 is rotation, scale and position invariant, so it cannot separate up-arrows from down-arrows or circles from ovals, and it ignores time. Rotation invariance can be removed per template by skipping the indicative-angle rotation — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- End users can handle variation by adding more templates under one name. A failed gesture can simply be added as a new template, and it "will be recognized from then on", subject to what else is loaded — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)

**Protractor [STYLUS/TOUCH] [SNIPPET]**
- With 9 samples for each of 16 gestures, recognition took 24 ms against 1405 ms for $1, on a T-Mobile G1 phone. Each template is a 32-element vector, a quarter of earlier storage. It was as accurate as $1 on the 4,800-sample set and significantly more accurate on a 10,888-sample, 26-category, 100-user set — [Li, CHI 2010](https://research.google.com/pubs/archive/36269.pdf) (figures via excerpts)
- **Conflict:** an independent test on the $1 dataset got 95.56% for $1 and 92.87% for Protractor, so the accuracy claim depends on dataset and setup — [Squiggle paper](https://arxiv.org/pdf/1109.5323). That paper's $1 score is also below the 99% in Wobbrock, and I did not check its protocol.

**$P and $Q point-cloud [STYLUS/TOUCH]**
- $P reaches 99% user-dependent accuracy at 4 templates per gesture type, and 99.1% user-independent from 32 templates (participants × templates) — [Vatavu et al., MobileHCI 2018](http://faculty.washington.edu/wobbrock/pubs/mobilehci-18.pdf)
- $Q moved averages from 98.0% to 98.7% (user-dependent) and 95.7% to 96.7% (user-independent) relative to original $P — [Vatavu et al.](http://faculty.washington.edu/wobbrock/pubs/mobilehci-18.pdf)
- Speed for the high-accuracy test case (1,024-template scale, 16 gestures, Java on Android): 82 ms on Cortex-A53 (against $P's 5838 ms), 156 ms on A9, 192 ms on A7, 200 ms on A5. On average 46× faster than $P, up to 142× on a 600 MHz low-end CPU — [Vatavu et al.](http://faculty.washington.edu/wobbrock/pubs/mobilehci-18.pdf)
- Point-cloud methods ignore stroke number, order and direction — [$-family page](https://depts.washington.edu/acelab/proj/dollar/index.html)

**DTW and Jackknife [multi-modal] [SNIPPET]**
- Jackknife is a DTW recogniser evaluated on pen/touch, Wii Remote, Kinect, Leap Motion and sound-sensed gestures plus continuous data, and is claimed to achieve "high accuracy" across them — [Taranta et al., CHI 2017 abstract](https://stars.library.ucf.edu/scopus2015/7463)
- The project page says it is designed for one or two samples per class and ships in C++, C# and JavaScript. That is a design claim. I could not read the accuracy tables — [Jackknife project page](https://www.eecs.ucf.edu/isuelab/research/jackknife)

**SVM and the current system**
- [REPO] The classifier is a two-class `SVC` on a 784-dimensional 28×28 image, tuned with a grid search over 4×5×3×3 parameter combinations — [train_spell_classifier.py](../../DatasetCreation/train_spell_classifier.py)
- [REPO] There are 201 images per class. They are drawn with the mouse (`cv2.setMouseCallback`), not captured with the wand — [draw_spell_data.py](../../DatasetCreation/draw_spell_data.py)
- libsvm training scales between O(features × n²) and O(features × n³) — [scikit-learn SVM docs](https://scikit-learn.org/stable/modules/svm.html)

**CNN inference cost on Pi 5**
- MobileNet v2 takes 23.5 ms and v1 takes 16.9 ms with TensorFlow Lite on a Pi 5, against 148.9 ms and 66.2 ms with full TensorFlow. The table does not name the exact model variants — [Allan, benchmarking-ml-on-the-edge](https://github.com/aallan/benchmarking-ml-on-the-edge) [SNIPPET]
- Active cooling was used to avoid throttling, and TFLite was almost 5× faster than on a Pi 4 — [Hackster, Pi 5 benchmark](https://hackster.io/news/benchmarking-tensorflow-and-tensorflow-lite-on-raspberry-pi-5-b9156d58a6a2) [SNIPPET]

**Prior wand builds**
- Hobby builds use the same long-exposure-image approach or an SVM on letters. Only specific letters trigger actions in one build. None report accuracy or false triggers — [Hackaday](https://hackaday.com/tag/noir/), [DFRobot](https://community.dfrobot.com/makelog-312881.html)

### Inferences
- **Which recogniser to pick:** an ordered-path template matcher (Protractor or $1 with rotation sensitivity on, resampled to about 32-64 points) looks like the best first choice. Spells usually depend on orientation, and possibly on direction. Rendering to an image discards direction and timing, as do point clouds. Ordered paths keep direction, which adds separating power, but they also make users' stroke-direction habits matter. Use $Q only if you need multi-stroke or direction-free matching, which a continuous wand stroke mostly does not.
- **Rotation:** do not use the default rotation invariance. It would make orientation-dependent spells collide.
- **Examples per spell:** plan on 5 at enrolment (range 3-10). The stylus curves flatten quickly after about 3-4 templates, so that range is likely adequate, but the numbers should not be transferred to air gestures. Air traces lack a pen-up and have more tremor and tracking noise.
- **User adds a spell on a Pi:** this is trivially feasible for templates, since enrolment just stores resampled points with no training step. At 5-10 spells × 5-10 templates (25-100 templates), matching should take single-digit milliseconds or less in NumPy. This is an estimate scaled from the phone numbers above, not a measurement.
- **SVM retraining:** an SVM can retrain quickly at this data size, but it needs examples of every class and gives no principled "none of these" outcome. It also has a train/serve mismatch today, because it is trained on mouse drawings and fed wand traces.
- **Small CNN/TCN:** inference is not the constraint. A 28×28 CNN should be far below the MobileNet timings. Data is the constraint, so these models only become sensible after real wand traces have been logged, and more so if the user base or spell set grows. They are unlikely to beat templates at 3-10 examples without heavy augmentation or a pretrained embedding.
- **Hybrid:** Rubine's weak few-sample results suggest statistical classifiers need more data than templates, though Rubine is not an SVM or CNN.

### Gaps
- No published accuracy for $-family or DTW on single-point IR camera traces. A small benchmark on recorded wand data is needed. Log raw `(x, y, t)` per attempt.
- Jackknife's per-sample accuracy tables were not read, because the PDF host refused the connection or failed TLS verification.
- No head-to-head of SVM-on-image, small CNN or TCN at 3-10 examples per class for stroke-like air gestures. No Pi 5 numbers for on-device CNN training.
- No Pi 5 benchmark of $1, Protractor or $Q, in Python or otherwise. Python cost relative to the Java timings is unknown.

## Q2. Rejecting unintended input: thresholds, open-set and gesture spotting

### Takeaway
The current system has no way to say "not a spell": any trace of 10+ points is forced into open or close. The evidence favours three layers: deliberate gesture design and delimiters, a calibrated score threshold, and testing against real non-gesture movement. Accuracy on deliberate gestures says little about false positives.

### Cited Findings
- [REPO] The app calls `clf.predict` only, so no score is used, and completion requires only ≥10 points plus stillness. There is no path-length or bounding-box check. An open/close state flag does gate which result acts — [harry_potter_wand_sklearn.py](../../harry_potter_wand_sklearn.py), [harry_potter_wand_cv.py](../../harry_potter_wand_cv.py)
- [REPO] A trace starts when a blob has been present >0.6 s and moves >6 px between frames. It ends on stillness or when the wand leaves frame for the stillness duration — [harry_potter_wand_cv.py](../../harry_potter_wand_cv.py)
- [REPO] **Probable bug:** the stillness test counts frames against `stillness_duration / 0.05`, so 20 frames regardless of frame rate. The nominal 1.0 s would be 0.67 s at 30 fps and 0.17 s at 120 fps. The `movement_threshold` of 6 px is also per-frame, so "still" means below 180 px/s at 30 fps but below 720 px/s at 120 fps — [harry_potter_wand_cv.py](../../harry_potter_wand_cv.py). These rates are arithmetic. The actual frame rate on the Pi was not measured.
- **False positives vs. accuracy [KINECT, whole-body]:** on 52 person-hours of natural living-room activity, an HMM recogniser with 99% test accuracy fell to 83% when a thresholding background model was added. It still produced 73,729 false positives, or one every 5.1 s per participant. Many of the 20 sampled per gesture traced to poor skeleton tracking — [Freeman et al., 2015](https://arxiv.org/pdf/1509.06109)
- **Gesture design [KINECT]:** redesigning gestures against that dataset (10 training examples each) reduced false positives 5.5× overall. Prefixing a swipe with a pause gave 15.2× fewer than plain Swipe. Circle gave 3.5× fewer than Point. Holding still was hard to separate from background — [Freeman et al.](https://arxiv.org/pdf/1509.06109)
- **Scores:** $1 returns an N-best list with [0..1] scores, and a rapid falloff from position 1 to 2 makes a non-recognition threshold easier to set [STYLUS/TOUCH] — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- **Synthetic thresholds [SNIPPET]:** Jackknife selects a rejection threshold by maximising F1 over synthetic distributions, with negatives from splicing templates and positives from stochastic path resampling — [Jackknife page](https://www.eecs.ucf.edu/isuelab/research/jackknife)
- **Threshold and sample size [SNIPPET]:** Voight-Kampff (CHI 2022) selects thresholds for custom gestures from synthetic score distributions. Its authors note the best threshold depends partly on training-set size, and negatives come from replacing trajectory parts with other classes' sub-trajectories — [VKM page](https://www.eecs.ucf.edu/isuelab/research/vkm/), [code](https://www.github.com/ISUE/VKM)
- **SVM confidence:** Platt-scaled `predict_proba` can disagree with `predict`, is known to have theoretical issues and needs an extra five-fold cross-validation. The docs advise `probability=False` and `decision_function` when you just need a confidence score — [scikit-learn SVM docs](https://scikit-learn.org/stable/modules/svm.html)
- **Delimiters:** always-available input is hard because a universal delimiter is itself a burden, while skipping it invites Midas-touch false positives — [Gunslinger](https://www.lri.fr/~anab/teaching/evaluation/papers/gunslinger.pdf) [SNIPPET]
- **Dwell [GAZE, SNIPPET]:** short dwell raises unintended activation — [IGI chapter](https://resources.igi-global.com/chapter/computer-control-gaze/60036). Pairing dwell with a gesture cut false selections from 41.39% to 21.37% in a gaze study — [GazeBlend](https://arxiv.org/pdf/2512.15491). A dwell-then-gesture sequence has also been proposed to avoid unintended commands — [GI 2020](https://graphicsinterface.org/wp-content/uploads/gi2020-26.pdf)
- **System-side errors [KINECT]:** an in-air recogniser (14 participants, 1,344 gestures) recognised 94%, and 80.3% of errors were the system's. The authors cite ≥97% as needed for users to find a gesture system useful (a secondary citation in their paper) — [Arif et al., CHI 2014 WIP](https://www.asarif.com/pub/Arif_CHI2014b.pdf)

### Inferences
- **The wand is an inherent delimiter.** Unlike hands or body, an IR tip is only visible when aimed and lit, so "tip appears, pauses briefly, moves" is a natural start gesture. This resembles Freeman's Pause Swipe. It is cheap to enforce with a short armed state and a visual "ready" cue.
- **Layered rejection:**
  1. Geometric gates: minimum path length, bounding-box size and duration, in pixels and seconds rather than frames.
  2. Best-template score threshold.
  3. Margin between the best and second-best spell.
  4. Per-spell thresholds from leave-one-out scores at enrolment, tightened with spliced synthetic negatives.
  5. A real negative set, logged from idle waving, walking across frame and reflections.
- **If the SVM stays:** use `decision_function` magnitude as a stopgap and add a "none" class trained on real wand non-gestures. This only partly helps, because a closed-set classifier's distance from a boundary is not distance from the training data, so an unusual trace can score confidently.
- **End-of-gesture:** a 1 s hold is comparable to the whole gesture (0.7-1.8 s for stylus strokes), which likely makes it the largest source of perceived delay. Time-based stillness measured in px/s, scaled to trace size and shortened to about 0.3-0.5 s, is worth testing. Too short risks firing on mid-stroke pauses, so tune it on logged traces. Those values are my starting points, not published ones.
- **Reject-on-uncertain should be quiet but visible.** A rejected attempt costs a retry while a misfire triggers a wrong effect, so favour rejection for high-consequence actions.

### Gaps
- No false-positive rate per hour for a wand or a single-point air tracker. Freeman's whole-body figures are not transferable in magnitude, because a wand must be aimed and lit.
- VKM and Jackknife rejection F1 numbers were not read. I also found no evaluation of them on IR point tracks.
- I did not retrieve the classic gesture-spotting threshold-model papers. Freeman provides the only HMM background-model figure in these notes.
- No published optimum for a stillness-based end-of-gesture delimiter in air.

## Q3. Automatic calibration of IR blob detection on picamera2 and Camera Module 3 NoIR

### Takeaway
Fixing exposure, gain, focus and frame rate is the clear first step, and the main script appears not to apply its configured exposure at all. Hardware-synchronised differencing is not documented as supported on the Camera Module 3, and it could only ever apply to a pulsed illuminator, not a free-running wand LED. Simple background capture and optical filtering are more practical.

### Cited Findings

**Current state [REPO]**
- `harry_potter_wand_cv.py` configures only a 640×480 RGB888 preview. Across non-test Python, the only `set_controls` call is in `calibrate_reflector.py` (ExposureTime 8000, AnalogueGain 6.0, Brightness -0.3). `exposure_time` and `analogue_gain` in `config.yaml` appear to be written by the config builder but not applied in the main loop — [harry_potter_wand_cv.py](../../harry_potter_wand_cv.py), [calibrate_reflector.py](../../calibrate_reflector.py), [config_builder.py](../../utils/config_builder.py)
- So the recognition run most likely uses auto exposure. Confirm by reading `ExposureTime` from frame metadata on the Pi.
- Reflector mode already uses MOG2 background subtraction, a brightness threshold, a Kalman filter and 3-frame temporal validation — [config.yaml](../../config.yaml)

**Hardware facts**
- Camera Module 3 uses the Sony IMX708, with 2304×1296 at 56 fps, 2304×1296 at 30 fps HDR and 1536×864 at 120 fps. Motorised focus ranges from about 10 cm to infinity. A NoIR version exists — [Raspberry Pi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html)
- The docs do not state the shutter type for this module and describe only the Global Shutter Camera as global — [Raspberry Pi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html). A rolling shutter is assumed below.
- Wired sync is documented for the HQ and Global Shutter cameras. The excerpt I read does not list the Camera Module 3. Software sync (`--sync`) aligns cameras with each other at frame level, not LEDs — [camera software docs](https://www.raspberrypi.com/documentation/computers/camera_software.html)

**Exposure and frame timing**
- Controls passed before start apply from the first frame. Set after start, they take several frames because of in-flight requests and sensor delay — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- `FrameDurationLimits` with equal min and max fixes frame rate, for example (33333, 33333) for 30 fps — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- `SensorTimestamp` gives per-frame nanosecond timing from read-out of the first pixel — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- `AeFlickerMode` and `AeFlickerPeriod` exist for lighting flicker — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- Preview configurations use 4 buffers. The queued frame can be up to a frame period old unless `queue=False` — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- On Pi 5, lores can be RGB or YUV, up to main-stream size — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)

**Autofocus**
- In Manual mode the lens never moves spontaneously. `LensPosition` is in dioptres (1/m), with 0 meaning infinity, and the reported position appears in metadata — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- Focus hunting has been reported on static low-contrast scenes (flat coins). Staff suggested debug logging and possible tuning-file changes — [RPi forum](https://forums.raspberrypi.com/viewtopic.php?t=352804) [LOW QUALITY, about 2023]
- Picamera2 reportedly does not enable AF by default, whereas rpicam apps default to continuous — [RPi forum thread](https://forums.raspberrypi.com/viewtopic.php?t=345325&start=25) [SNIPPET, 2023-24, verify on the installed version]
- Module calibration varies, and values above 10 were rejected in manual mode on some units in one Wide-module report — [picamera2 issue #1105](https://github.com/raspberrypi/picamera2/issues/1105), [camera software docs](https://www.raspberrypi.com/documentation/computers/camera_software.html)
- Daylight focus loss was seen on low-contrast sky scenes — [Geerling](https://www.jeffgeerling.com/blog/2023/raspberry-pis-camera-module-3-adds-autofocus-and-new-sony-sensor/). Vibration can also disturb AF — [Arducam](https://www.arducam.com/blog/official-camera-module-3-a-closer-look/)

**Differencing with pulsed IR**
- Alternating an IR LED per frame and subtracting cancels ambient light. Most sources here are patents, so they describe claimed methods rather than validated products — [US 9292109](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9292109), [core.ac.uk abstract](https://core.ac.uk/works/15263429)
- With a rolling shutter, the illuminator must stay on for the whole frame so all rows are lit evenly. Partially lit frames cannot be subtracted, and this wastes power — [US 10949647](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10949647), [US 2018/0131880](https://patents.justia.com/patent/20180131880)
- Bandpass filters help, but some ambient sources still have enough in-band power to compete, which is why subtraction is added — [core.ac.uk abstract](https://core.ac.uk/works/15263429)

**Wavelength and interference [LOW QUALITY, SNIPPET: these came from one search summary that did not map each claim to a URL, so the links below are best matches. Re-check before quoting.]**
- 850 nm gives better camera response with a faint red glow and more sunlight susceptibility. 940 nm is less visible and less affected by sunlight but with lower camera sensitivity — [Reolink](https://reolink.com/blog/infrarot-led-850nm-und-940nm-im-vergleich/), [Lumileds coverage](https://www.semiconductor-today.com/news_items/2017/aug/lumileds_080817.shtml)
- An IR-pass filter gives a large improvement — [NYCR thread](https://groups.google.com/g/nycresistormicrocontrollers/c/9Z8OjGQPOjE)
- Remotes typically modulate at about 38 kHz for 35-50 kHz receivers — [Parallax forum](https://forums.parallax.com/discussion/comment/516707). Common receivers are listed at 950 nm — [Vishay TSOP98638 listing](https://uk.rs-online.com/web/p/ir-receivers/2444818)

### Inferences
- **Do first:** pass fixed controls at configure time (`ExposureTime`, `AnalogueGain`, `FrameDurationLimits`, `AfMode: Manual`, `LensPosition`). For a 1.5-2.5 m working distance, `LensPosition` is about 0.4-0.7. A defocused tip makes a larger, dimmer blob, so a slightly defocused setting may be tolerable and even help sub-pixel centroiding. Test this rather than assuming it.
- **Exposure:** short exposures reduce both motion blur and ambient integration. A bright LED tolerates this better than a dim retroreflector, so the two wand modes likely need separate presets. The current 8 ms is about a quarter of the 30 fps frame period, and a fast stroke will streak.
- **Auto-calibration routine (about 5 s):** with the wand absent, grab a burst at fixed exposure and store a per-pixel background (max or high percentile) as a static mask, which removes lamps, window glints and shiny objects. Set threshold = background percentile + margin. Then ask the user to wave the wand, record tip brightness and area, and set blob limits between background and tip statistics. Warn if background is too close to tip level ("too much IR here, move the camera or close the blinds"). Re-run on large background drift.
- **Temporal filter vs. MOG2:** a static mask plus a lightweight drift update could be cheaper than MOG2 per frame, but MOG2 absorbs a stationary wand tip, which matters for a stillness-terminated gesture. Check this interaction in reflector mode, since MOG2 with a 120-frame history could fade a held tip before end-of-gesture. Hypothesis from reading the config, not observed.
- **Differencing is only partly practical:**
  - It applies to retroreflective mode, where the Pi controls the illuminator. A handheld LED wand has no link to the camera.
  - GPIO pulses would be open-loop against a free-running rolling-shutter sensor. Alignment would need software phase tracking from `SensorTimestamp`, with stale partial rows discarded.
  - It halves effective tracking rate, and a moving tip leaves a positive and a negative blob, which needs handling.
  - Treat it as an advanced later option, or run a spike. The configured 1 kHz MOSFET PWM may also band with short exposures on a rolling shutter.
- **Lower-effort sunlight rejection:** an 850 nm bandpass filter on the lens (or 940 nm if sunlight dominates, at reduced sensitivity), plus shape and motion gating. An 850 nm narrow bandpass should also attenuate remotes near 940-950 nm. This is reasoning from the listings above, not a tested result.
- **IR remote bursts** are not resolved as a 38 kHz flicker at camera rates. Expect a bright, stationary, intermittently modulated blob. A static-position or motion-continuity check should reject it, and the Kalman jump limit may partly do so already.
- **Frame rate:** 1536×864 at 120 fps with a fixed 640×480 or smaller output gives lower latency and denser traces, if CPU allows. Current RGB-to-gray conversion plus `SimpleBlobDetector` may be the bottleneck. A YUV420 lores Y-plane avoids colour conversion. Profile before changing.

### Gaps
- I found no source on the IMX708's NoIR focus shift under 850/940 nm or on AF behaviour specifically in dark IR scenes, and no measurement of a NoIR module's spectral response at those wavelengths in the docs I read.
- No authoritative statement on whether the Camera Module 3 exposes XVS/FSIN or strobe. The one IMX-family forum evidence was for other sensors and conflicting — [Arducam forum](https://forum.arducam.com/t/need-arducam-camera-schematics-xvs-pin-for-sync-on-jetson-orin-nx-b0251-imx477-imx519/10042), [INNO-MAKER](https://github.com/INNO-MAKER/CAM-IMX577). Absence from the docs does not prove it is impossible.
- No published sunlight-rejection figure for a specific bandpass filter in this setup.
- No Pi 5 per-frame CPU figures for MOG2 or `SimpleBlobDetector`, and no outdoor or sunlit test data. Forum evidence dates from 2023-24, so it may lag current libcamera behaviour.

## Q4. Feedback and learnability for air gestures

### Takeaway
Combined feedforward and live feedback improves learning, but the strongest studies use a mouse or stylus. The minimum useful set here is a live trace, a visible state machine (ready, tracing, recognising) and specific failure feedback, with latency kept low enough that the trace feels attached to the wand. No air-gesture latency threshold was found.

### Cited Findings
- **Definitions:** feedforward shows a gesture's shape and command before or during execution. Feedback reports how input is being interpreted, during or after — [Bau & Mackay, OctoPocus, UIST 2008](https://www.lri.fr/~mbl/FundHCI/papers/Octopocus-UIST2008.pdf)
- **OctoPocus [MOUSE]:** 16 participants, 15-inch display, 16 arbitrary gestures, Rubine recogniser. Overall input was 5.7 s against 5.9 s for a Help menu (p=0.024). During training, including unaided trials, error was 4% against 8% (p=0.008). In unaided expert trials it was 4% against 7% (p=0.010). Participants chose the guide more often (40% vs. 32%), saying it was "less risky" because they could hesitate and get a hint — [Bau & Mackay](https://www.lri.fr/~mbl/FundHCI/papers/Octopocus-UIST2008.pdf)
- The authors say it applies to a wide range of single-stroke gestures and recognisers, and that it improves on a two-level, four-item hierarchical marking menu in input time — [Bau & Mackay](https://www.lri.fr/~mbl/FundHCI/papers/Octopocus-UIST2008.pdf) [SNIPPET for the marking-menu result]
- **Errors in air [KINECT]:** block error rates were 7.44%, 8.33%, 5.06% and 3.27% (no significant block effect), and 80.3% of errors were the system's. Their second study found different error patterns when gestures were tied to concrete tasks — [Arif et al.](https://www.asarif.com/pub/Arif_CHI2014b.pdf)
- **Spatial feedback in air [SNIPPET]:** mid-air gestures are reported as hard to perform without spatial feedback — [ISS 2022 paper](https://yorku.ca/mack/iss2022.pdf). Haptics can compensate for lacking guidance in 3D curve gestures — [UCLouvain](https://research.dial.uclouvain.be/bitstreams/2c995a30-f31d-4b38-b0a0-b4ea50dc65d5/download). Wristband guidance using a "pull" cue beat "push" — [GI record](https://dl.gi.de/signposting/describedby/718165ac-9faa-49a7-9ecd-25a34082af31)
- **Latency [STYLUS/TOUCH]:**
  - Inking latency perception is about 50 ms against about 2-7 ms for non-inking tasks. It depends on the presence of a visual referent such as the hand or stylus rather than the nib-to-ink distance.
  - The same paper reports earlier work where participants could not discriminate 7 from 40 ms during scribbling, and earlier claims of about 100 ms as adequate.
  - It also cites 30 ms as sufficient for playing a Theremin without tactile feedback, the closest analogue to non-contact control in these notes — [Annett et al., GI 2014](https://sites.ualberta.ca/~wfb/publications/C-2014-GI-Latency.pdf)
- **Camera side:** frame period is 33 ms at 30 fps, 18 ms at 56 fps and 8.3 ms at 120 fps, calculated from documented modes — [Raspberry Pi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html). A queued frame can add up to one frame — [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf)
- **Recovery:** adding a failed attempt as a template gives a direct, understandable correction path [STYLUS/TOUCH] — [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf)
- [REPO] Today's trace overlay is drawn on an OpenCV output frame, and status text exists, so basic trace feedback is partly present — [harry_potter_wand_cv.py](../../harry_potter_wand_cv.py)

### Inferences
- **Latency budget (my synthesis):** aim for live trace under about 50-100 ms and spell effect under about 300-500 ms after the gesture actually ends. The trace is viewed on a screen with the physical wand as a distant referent, so tolerance is probably looser than for inking on a screen. The 1 s hold and any audio or servo delay are likely to matter more than classifier time.
- **Show the state machine:** wand seen → ready → tracing → hold → recognised or rejected. A short sound or LED cue would suit users who watch the wand or room rather than a screen. The project already has audio and an optional LED strip, which also serves as non-screen feedback.
- **Feedforward at low cost:** a static idle-screen gesture card showing shape, start point and direction. Full OctoPocus-style dynamic guides need incremental prefix scoring, which templates support well but SVM-on-image does not.
- **Specific failure feedback:** "too small", "too short", "lost tracking" and "not recognised, closest was X" come straight from the geometric gates and N-best list. Offer "add this as an example of X?" for recovery. Near-miss overlay of the attempt on the closest template should be the most informative option.
- **Enrolment UX:** prompting 5 repeats with a live trace, plus an immediate warning when a new spell is too close to an existing one (cross-template distance), helps users avoid colliding spells. This follows from the template-recogniser design rather than a study.
- **Gesture set advice:** prefer distinct shapes tested against logged idle motion, and avoid simple swipes or holds, as in Freeman's results.

### Gaps
- No controlled study of guides, failure feedback or latency budgets for wand-like single-point air input, and none on Kano or Magic Caster products. Feedback claims here extrapolate from mouse, stylus and Kinect work.
- I found no measured Pi 5 glass-to-glass latency for picamera2 plus display. Measure it with an LED toggle and a high-speed phone video.
- No evidence comparing screen trace with audio or light-only feedback for wand users. No retention figures were extracted from OctoPocus beyond the error rates above.

## Q5. Most usability gain for least engineering effort

### Takeaway
Fix the deterministic capture and timing problems first, since they are small, make everything else measurable, and may remove a share of today's misfires. Then log real wand traces, add rejection, and move to a template recogniser, which also unlocks 3-10 example custom spells. Pulsed differencing and neural models should come last.

### Cited Findings
Effort and gain are my judgement. The evidence links point to the supporting findings above.

| # | Change | Effort | Expected gain | Basis |
|---|---|---|---|---|
| 1 | Apply fixed exposure, gain, frame rate and manual focus in the main app | Under 1 hr | Stable blob brightness, no AE or AF drift | [REPO](../../harry_potter_wand_cv.py), [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf) |
| 2 | Make stillness and start logic time-based (seconds, px/s), and fix the `0.05` assumption | 1-2 hrs | Consistent end-of-gesture, fewer premature cuts | [REPO](../../harry_potter_wand_cv.py) |
| 3 | Add geometric gates (minimum length, size, duration) | 1-2 hrs | Removes stray flicks and tiny traces | [REPO](../../harry_potter_wand_cv.py), [Freeman et al.](https://arxiv.org/pdf/1509.06109) |
| 4 | Log raw `(x, y, t)`, outcome and exposure per attempt | 1-2 hrs | Enables all later tuning and comparison | Gap noted in Q1 |
| 5 | Show ready, tracing and failure states, plus a gesture card | About 0.5 day | Lower learning cost, fewer blind retries | [Bau & Mackay](https://www.lri.fr/~mbl/FundHCI/papers/Octopocus-UIST2008.pdf) [MOUSE], [Arif et al.](https://www.asarif.com/pub/Arif_CHI2014b.pdf) [KINECT] |
| 6 | Trajectory template recogniser with score threshold and margin | 1-2 days | Reject outcome, 3-10 example spell enrolment, faster inference | [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf), [Li](https://research.google.com/pubs/archive/36269.pdf) [both STYLUS/TOUCH] |
| 7 | Armed "pause then move" start, and shorter hold | About 0.5 day, plus tuning | Fewer accidental starts, less delay | [Freeman et al.](https://arxiv.org/pdf/1509.06109) [KINECT] |
| 8 | 5 s auto-calibration: background mask, then wave test | 1-2 days | Fewer manual tuning steps, room warnings | Inference in Q3. No direct study |
| 9 | Bandpass filter | Under 1 hr once purchased, plus testing | Better daylight and remote rejection | [Reolink](https://reolink.com/blog/infrarot-led-850nm-und-940nm-im-vergleich/) [LOW QUALITY], [core.ac.uk](https://core.ac.uk/works/15263429) |
| 10 | Spell enrolment UI with collision warning and "add this example" | 1-2 days after #6 | Direct user-added spells and recovery | [Wobbrock et al.](http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf) |
| 11 | Synthetic-negative threshold calibration | 1-2 days | Better per-spell thresholds, especially for small template sets | [VKM](https://www.eecs.ucf.edu/isuelab/research/vkm/), [Jackknife](https://www.eecs.ucf.edu/isuelab/research/jackknife) [SNIPPET] |
| 12 | Higher frame rate pipeline (120 fps mode, Y-plane, `queue=False`) | 1-2 days, after profiling | Lower latency, denser traces | [Raspberry Pi docs](https://www.raspberrypi.com/documentation/accessories/camera.html), [Picamera2 manual](https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf) |
| 13 | Pulsed illuminator differencing | Several days, uncertain | Strong ambient rejection for reflector mode only | [US 10949647](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10949647) |
| 14 | Small CNN or TCN | Days, plus data | Possibly better on large logged sets, little at 3-10 examples | [Allan](https://github.com/aallan/benchmarking-ml-on-the-edge) for inference cost only |

### Inferences
- Items 1-4 are prerequisites because they make the input stable and observable. Without them any recogniser comparison is confounded by capture variation.
- Item 6 is the main architectural step, since it addresses three problems at once (no rejection, retraining, and direction and timing loss). The mouse-drawn training mismatch disappears because templates come from the wand. Keep the SVM running in shadow mode on logged traces to compare fairly.
- A sensible acceptance test: over a fixed logged set, target ≥97% true-spell recognition (the threshold cited by Arif et al., secondary) and report misfires per hour of idle waving. Both need measuring on this hardware. Published stylus numbers are not a forecast.
- Differencing and neural models are the two items most often assumed to be needed. Neither looks like the current limiter based on the code.

### Gaps
- None of the ranking has been validated on the actual hardware. No Pi run was performed for these notes, and current misfire and miss rates are unknown.
- Engineering estimates assume familiarity with this codebase. They are not derived from any source.
