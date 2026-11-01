# Comparable wand projects and Pi appliance practices

Researched 2026-11-01. Repo stars, licences and last-push dates come from the GitHub API on that date. "Last push" can include bot or trivial commits, so it is only a rough sign of activity.

Evidence labels used below:
- **(read)**: I read the page, README or issue directly.
- **(search summary)**: I saw it only in a search-result summary, not on the page itself. Treat these as leads.

## What do other wand projects do, and what do users struggle with?

### Takeaway
Almost all Pi wand builds use the same recipe: an IR lamp, a NoIR camera, a retroreflective tip, a blob tracker and a classifier. They differ mainly in setup, not recognition. Reported problems are mostly install rot, ambient IR and silent non-recognition. The newest projects answer these with a live threshold view, phone training and MQTT, but they have almost no users yet, so their claims are untested.

### Cited Findings

**Comparison**

| Project | Status (last push, stars, licence) | Detection and classifier | Spells | Setup and UX | Integrations |
|---|---|---|---|---|---|
| [Gloworm72/InteractiveWand](https://github.com/Gloworm72/InteractiveWand) (upstream) (read) | 2025-05, 6, **no licence** | OpenCV blob, scikit-learn SVM with GridSearchCV, 400+ traces, self-reported 99%+ accuracy, ships a `.pkl` | 2 | Scripts; no install steps in the page content I read | Local only: LEDs through Pi5Neo over SPI, servo, pygame audio |
| [sean-obrien/rpotter](https://github.com/sean-obrien/rpotter) (read) | 2018-02, 60, MIT; **abandoned** | NoIR camera, IR LEDs and OpenCV; the method isn't described on the page | Not listed on the page | Issues mention disk images and a website, now down | GPIO; Arduino sketch in the repo |
| [mamacker/pi_to_potter](https://github.com/mamacker/pi_to_potter) (read) | 2024-02, 19, MIT; stale | Background subtraction and ML on Pi 3/4 | User-trainable | Long `steps_taken.txt`; separate Node support webpage | GPIO and pins |
| [Esiravegna/pipotter](https://github.com/Esiravegna/pipotter) (read) | 2026-10, 7, no licence; alive but small | EfficientNet B0 (TensorFlow/Keras) trained on a separate machine | Trainable; count not stated | `config.json`, `run.sh`, web server on port 8000 | NeoPixels, sound, servo |
| [mtaylor45/-SpellSight, "Wand Portal"](https://github.com/mtaylor45/-SpellSight) (read) | Created 2026-09, 1, no licence; **very new** | Template matching with 64-point resampling, about 5 samples per spell | 45 in catalogue; author puts the reliable limit at 6–10 | Docker Compose or venv; phone console with Tune, Train and Cast modes; env overrides | MQTT with Home Assistant discovery |
| [DanStach/WandGestureDetector](https://github.com/DanStach/WandGestureDetector) (read) | Created 2026-09, 0, no licence; **very new** | Deterministic gesture matching, no ML, Pi 3B+ | 5 gesture types | Setup script and venv; FastAPI admin with `/health` and `/api/stats`; runs without a camera; systemd unit | MP3, video, GPIO, webhook |
| [Mootado/wand-spell](https://github.com/Mootado/wand-spell) (read) | Created 2026-10, 0, no licence; **very new** | Stroke shape from a thresholded NoIR image, Universal wand | 4 | apt packages only; camera check is the first screen; `--keyboard` mode for PC | Self-contained game |
| [terra819/lumos-the-christmas-tree](https://github.com/terra819/lumos-the-christmas-tree) (search summary) | 2019-12, 5, no licence; stale | OpenCV, `trainer.py` for own spells | Lumos, Nox, Incendio named | README covers training | NeoPixels through FadeCandy |
| [bigweale/magicwand](https://github.com/bigweale/magicwand) (search summary) | 2020-05, 1, MIT; stale | k-nearest neighbours | Not found | Not checked | Goal is an IoT bulb |
| [jsuereth/raspberry-potter](https://github.com/jsuereth/raspberry-potter) (search summary) | 2019-02, 6, no licence; stale | IR positioning camera, OpenCV shape matching, Pi 3 | Not found | Parts listed as pending | Home automation goal |
| [jasmeet0915/Interactive-Harry-Potter-Wand](https://github.com/jasmeet0915/Interactive-Harry-Potter-Wand) (search summary) | 2020-03, 13, no licence; stale | NoIR camera, trained classifier on Pi 3 | Letters A and C per [Hackster](https://www.hackster.io/jasmeet-singh/real-harry-potter-wand-with-computer-vision-520e3b) | Not checked | Servo box |
| [aman-katyal/harry-potter-wand-duel](https://github.com/aman-katyal/harry-potter-wand-duel) (search summary) | 2026-10, 1, no licence | RP2040 with on-device TinyML gesture recognition, not camera-based | Not found | Custom PCB | 38 kHz IR combat |

The GitHub API returned the same stats for `Gloworm72/InteractiveWand` and `Gloworm72/Interactive-Wand-Gesture-Recognition`, which suggests one repo under a renamed path. The API showed the same star count and last push for both, but I did not confirm the redirect.

**Commercial reference points**
- Kano launched its licensed Harry Potter wand in 2018, says it sold about 180,000, and was no longer actively marketing it by January 2023 — [TechCrunch](https://techcrunch.com/2023/01/27/warner-bros-swiped-our-harry-potter-wand-ip-says-kano/)
- A wand-to-app Bluetooth connection is described as "very temperamental" in a launch-era review, and the review reports repeated reconnecting — [Gearbrain](https://www.gearbrain.com/amp/harry-potter-coding-toy-review-2638689055) (search summary, stale)
- A Ward's Science listing marks the Kano kit as discontinued — [Ward's](https://www.wardsci.com/us/en/product/24720669/kano-harry-potter-coding-kit) (search summary)
- Warner Bros. shipped the Magic Caster Wand in 2022 at $150, aimed at controlling TVs, lights and speakers — [TechCrunch](https://techcrunch.com/2023/01/27/warner-bros-swiped-our-harry-potter-wand-ip-says-kano/)
- Sales of the Magic Caster Wand were reportedly suspended, "possibly" because of the Kano dispute — [MuggleNet](https://mugglenet.com/?p=1388139) (search summary; current status not checked)

**What users actually struggle with**
- **Install rot:** following the instructions on Bookworm fails because the apt line names packages such as `libqt4-test` and `libjasper1`, and the user could not get past it — [pi_to_potter #7](https://github.com/mamacker/pi_to_potter/issues/7), with a follow-up request for updated instructions in [#8](https://github.com/mamacker/pi_to_potter/issues/8)
- **Dependency and runtime breakage:** issue titles include "Code is for Python 2", "ImportError: No module named pigpio", "Complete disk images are corrupt" and "Not able to get rpotter-startup to work" — [rpotter issues](https://github.com/sean-obrien/rpotter/issues) (titles only)
- **Crash on a normal condition:** "FindWand() crashing if no points found" and a GTK "cannot open display" warning on what looks like a headless run — [rpotter issues](https://github.com/sean-obrien/rpotter/issues) (titles only)
- **Ambient light:** a user asks whether it works in daylight or a lit room, and the thread has no replies — [rpotter #5](https://github.com/sean-obrien/rpotter/issues/5)
- **Silent non-recognition:** a user with a tracked wand and a working pipeline reports that drawn shapes do not trigger spells — [pi_to_potter #3](https://github.com/mamacker/pi_to_potter/issues/3)
- **Choice paralysis:** "Not sure which one to use" — [rpotter #10](https://github.com/sean-obrien/rpotter/issues/10) (title only)
- **Wanting to run off-Pi:** "is there a way to run this on a pc" — [pi_to_potter #4](https://github.com/mamacker/pi_to_potter/issues/4) (title only)
- **Docs defects:** the README's install line is `pip install requirements.txt`, missing `-r` — [pipotter](https://github.com/Esiravegna/pipotter)

**Patterns in the newer projects**
- Wand Portal orders setup as tune the blob, wire up Home Assistant, train, check separation, cast. It says the first step "decides whether everything downstream works" — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- Its separation check runs leave-one-out over stored samples and names confusable pairs. Its Cast log shows what fired, what was rejected and why — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- It advises redrawing a confused gesture rather than lowering the confidence threshold, and says gestures that differ in direction separate best (author's opinion) — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- Wand Spell makes the camera check its first screen, where "only the wand tip should be white", and changes the threshold with `[` and `]` — [Wand Spell](https://github.com/Mootado/wand-spell)
- Two independent READMEs say the lamp must sit tight against the lens because retroreflection is directional — [Wand Portal](https://github.com/mtaylor45/-SpellSight); [Wand Spell](https://github.com/Mootado/wand-spell)
- WandGestureDetector's admin server starts with no camera attached, so the API can be exercised off-Pi — [WandGestureDetector](https://github.com/DanStach/WandGestureDetector)
- Wand Portal states 640×480 at 30 fps costs about 15% of one Pi 4 core (author's claim, method not given) — [Wand Portal](https://github.com/mtaylor45/-SpellSight)

### Inferences
- Upstream's weak spot is adaptability, not accuracy. Its SVM needs 400+ traces per its own description, while Wand Portal claims about 5 samples per spell with user-drawn gestures. In-browser user training could be this project's largest usability gain, either through a template-matching fallback or by adding a user's samples to the SVM. Measure this on real traces first, because the 5-sample claim is untested.
- Copy the setup order from Wand Portal, and make "only the tip is white" a pass/fail first step. This answers the unanswered ambient-light question directly.
- Show rejected casts and the reason. That is the direct remedy for the pi_to_potter #3 experience.
- Pin versions and test the install on each new OS release. pi_to_potter shows that a long list of apt packages breaks when the OS moves on.
- Treat 6–10 spells as a planning figure only. It comes from one author.
- The three newest projects have 0–1 stars and were created in the last few months. Wand Portal's repo includes a `CLAUDE.md`, and WandGestureDetector's README refers to one, so they may be largely AI-assisted. Copy their design ideas, not their claims.

### Gaps
- **Hardware costs:** I found no reliable bill-of-materials totals. The only figures are the "$35 raspberry pi" in [pi_to_potter](https://github.com/mamacker/pi_to_potter), which is dated, and the $150 Magic Caster. Current Universal wand prices were not found.
- **Spell counts:** rpotter's list was not on the page I read. Kano's spell count and sensor type (likely IMU) were not confirmed. The search showed only that it uses an [nRF52832 over Bluetooth](https://www.nordicsemi.com/Nordic-news/2018/10/Harry-Potter-Kano-Coding-Kit-employs-nRF52832-to-wirelessly-connect-magic-wand-with-app).
- **ESP32 and OpenMV builds:** I found no notable examples. This reflects a limited search rather than proof that none exist.
- **Kano app:** I found no official end-of-support notice and could not establish whether the app still works today.
- **Forums:** Reddit and Raspberry Pi forum threads about wands were not reviewed, so the user-problem list rests on GitHub issues from a few repos, and it is a small sample.

## How do polished Pi and maker appliances handle usability?

### Takeaway
Polished appliances share a pattern: one obvious install path, a known local URL, first-run setup in the browser, a recovery path, and clear separation of config and data from code. Flashable images suit a later stage, because they carry an ongoing build and update burden that a small project may not want at first.

### Cited Findings

**Comparison**

| Project | Install | First-run and network | Updates | Reliability and diagnostics |
|---|---|---|---|---|
| WLED | [Browser-based flasher](https://kno.wled.ge/basics/getting-started/) at install.wled.me | Joins `WLED-AP` by password or QR code, then opens `wled.me` or `4.3.2.1`; picks home Wi-Fi and sets an mDNS hostname; [app auto-discovers devices](https://kno.wled.ge/basics/getting-started/) | [OTA upload in the web UI](https://kno.wled.ge/basics/getting-started/), behind an "OTA locked" flag and passphrase | Docs tell users to change the shared default AP password |
| Home Assistant OS | [Listed inside Raspberry Pi Imager](https://www.home-assistant.io/installation/raspberrypi) | [Ethernet required for install](https://www.home-assistant.io/installation/raspberrypi); opens `homeassistant.local`, then browser onboarding | [Supervisor keeps the system updated](https://www.home-assistant.io/installation/raspberrypi) | Docs give concrete timings: about a minute to respond, reflash or check HDMI console after five |
| Pi-hole | [One-step curl-to-bash, with alternatives](https://docs.pi-hole.net/main/basic-install/): clone, download and inspect, or Docker | Not covered on the page I read | Separate page, not read | The docs acknowledge that piping to bash is controversial |
| OctoPrint / OctoPi | Flashable image | [Wi-Fi set by editing `wifi.nmconnection` on the card](https://github.com/guysoft/OctoPi/blob/devel/README.rst) (search summary) | Not researched | [Camera auto-detected, streamer auto-started, URLs preconfigured](https://github.com/guysoft/OctoPi/blob/devel/README.rst) (search summary); [safe mode disables third-party plugins](https://docs.octoprint.org/en/dev/features/safemode.html) (search summary) |
| Frigate | [Docker Compose recommended](https://docs.frigate.video/frigate/installation/), also a Home Assistant App | [Authenticated UI on 8971; port 5000 unauthenticated and should be restricted](https://docs.frigate.video/frigate/installation/) | Not researched | [`/config` and `/media/frigate` separated; Logs API endpoint](https://docs.frigate.video/frigate/installation/); docs map symptoms such as bus errors to causes |

**Image building and Wi-Fi**
- rpi-image-gen builds custom images from pre-built packages using YAML, layers and hooks. It is under active development, lists no releases, wants a Debian arm64 host, and its sample image disables login passwords — [rpi-image-gen](https://github.com/raspberrypi/rpi-image-gen)
- pi-gen is the tool that creates Raspberry Pi OS itself — [rpi-image-gen](https://github.com/raspberrypi/rpi-image-gen). Both repos had pushes in October 2026 (GitHub API).
- The Trixie release ships cloud-init, beginning a move away from `firstrun.sh`, and Imager 2.0 generates cloud-init config by default — [Raspberry Pi](https://raspberrypi.com/news/cloud-init-on-raspberry-pi-os) (search summary)
- Imager customisation reportedly works only with official OS downloads, so users of a custom image lose it and must write cloud-init files to the boot partition by hand — [DEV Community](https://dev.to/ktauchathuranga/generate-cloud-init-files-for-raspberry-pi-os-without-re-downloading-images-51go) (search summary; single developer post, not confirmed officially)
- [balena-os/wifi-connect](https://github.com/balena-os/wifi-connect) is a maintained captive-portal candidate (Apache-2.0, pushed October 2026). I only confirmed repo activity, not Pi 5 or Trixie compatibility.

### Inferences
Practices to copy, highest value and lowest effort first:
1. **Autostart with `systemd`.** Run one long-lived service with restart-on-failure, and send logs to the journal. [WandGestureDetector](https://github.com/DanStach/WandGestureDetector) and Wand Portal both ship a systemd path.
2. **A known URL.** Set an mDNS hostname such as `wand.local`, following [WLED](https://kno.wled.ge/basics/getting-started/) and [Home Assistant](https://www.home-assistant.io/installation/raspberrypi).
3. **Setup in the browser.** Replace CLI steps with a guided check: camera found, tip visible, LEDs respond, sound plays.
4. **A diagnostics view.** Show `/health`, recent logs and detection stats, following [Frigate](https://docs.frigate.video/frigate/installation/) and WandGestureDetector.
5. **Separate config and data from code.** Keep `config.yaml`, trained models and user samples outside the checkout so updates can't overwrite them, as Frigate does with its mounts.
6. **A safe mode.** Offer a way to start with effects and integrations disabled, in the spirit of [OctoPrint](https://docs.octoprint.org/en/dev/features/safemode.html).
7. **Inspectable installer.** Offer a script plus an inspect-first alternative, as [Pi-hole](https://docs.pi-hole.net/main/basic-install/) does.
8. **Symptom-to-fix docs.** Give timings and specific next steps, as [Home Assistant](https://www.home-assistant.io/installation/raspberrypi) does.

Defer these:
- **Flashable image:** worth doing only after the installer is stable, since it adds a release pipeline. Users would also lose Imager customisation if the DEV Community report holds, so Wi-Fi setup would need another route.
- **Captive-portal Wi-Fi:** on a Pi, Imager can already preconfigure Wi-Fi with a standard OS image, so this matters only if a custom image ships.
- **WLED-style OTA:** a Pi service can update through git or apt-style packaging with a rollback tag, so firmware-style OTA isn't needed.

Security: a web UI that can change config or restart services should not be left open by default. Frigate's split between authenticated and unauthenticated ports shows that even mature projects treat this explicitly.

### Gaps
- **Volumio and ESPHome** were not researched. I have no sourced findings for them.
- **systemd watchdogs:** I found no primary source in this pass for `WatchdogSec` or `sd_notify` use in these appliances. Recommending a heartbeat from the frame loop is reasonable, but it is my own suggestion rather than an observed practice. A hung camera loop can leave a process alive, which plain restart-on-failure would not catch.
- **Raspberry Pi Imager custom repositories** (listing a project in Imager as Home Assistant is listed): the process and eligibility were not found.

## What's a lightweight way to add a phone-accessible web UI?

### Takeaway
Start with a small FastAPI or Flask app in the same process, streaming MJPEG on demand from one shared encoded frame. Every comparable project with a web UI that I could read in detail uses a simple HTTP server. **I found no reliable Pi 5 CPU benchmark for MJPEG versus WebRTC**, so this has to be measured on the target hardware.

### Cited Findings
- Wand Portal offers a phone console on port 8080, including a raw threshold-mask view for tuning — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- WandGestureDetector uses a FastAPI admin server on port 8000 — [WandGestureDetector](https://github.com/DanStach/WandGestureDetector)
- pipotter activates a web server by default at port 8000 — [pipotter](https://github.com/Esiravegna/pipotter)
- OctoPi's camera default is MJPG-streamer — [OctoPi README](https://github.com/guysoft/OctoPi/blob/devel/README.rst) (search summary)
- picamera2-webstream is a Flask MJPEG streamer that says higher resolutions and frame rates raise CPU and bandwidth needs. It was tested on a Pi 4 — [PyPI](https://pypi.org/project/picamera2-webstream/0.1.4) (search summary)
- aitoolkit-cam added a JPEG cache so several users can view a stream at once — [PyPI](https://pypi.org/project/aitoolkit-cam/) (search summary)
- A Raspberry Pi white paper from April 2026 says the Pi 5 uses the software libx264 encoder for H.264 — [Raspberry Pi white paper](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf) (search summary). The summary's CPU figures contradicted each other (60% versus 100–150% of a core), so **I do not cite a number**.
- A Luxonis forum poster preferred MJPEG with a REST API as the stable choice over WebRTC. This was a different platform and is one person's opinion — [Luxonis forum](https://discuss.luxonis.com/d/453-depthai-demo-on-raspberry-pi-qt-vs-all-in-one/15) (search summary)
- Frigate exposes WebRTC through go2rtc on port 8555 — [Frigate](https://docs.frigate.video/frigate/installation/)
- NiceGUI (MIT, about 16,300 stars), go2rtc (about 14,500), MediaMTX (about 20,600) and aiortc (about 5,100) were all pushed in October 2026 or later (GitHub API: [NiceGUI](https://github.com/zauberzeug/nicegui), [go2rtc](https://github.com/AlexxIT/go2rtc), [MediaMTX](https://github.com/bluenviron/mediamtx), [aiortc](https://github.com/aiortc/aiortc)). I found no Pi evidence for NiceGUI with OpenCV.

### Inferences
- **Recommended shape:** FastAPI or Flask serving static HTML and a little JS, with a `multipart/x-mixed-replace` MJPEG endpoint plus a WebSocket or SSE channel for spell events and status.
- **Protect the detection loop.** This is the key design rule:
  - Run streaming outside the capture and detection path, using a latest-frame buffer.
  - Encode only while a viewer is connected.
  - Encode once per frame, shared across viewers.
  - Use a small size and low frame rate (for example 320×240 at 10–15 fps) as a starting point. These numbers are a suggestion to test, not a measured result.
- **Stream the thresholded mask and tracked trail.** For tuning, these show more than the full picture, and they compress small.
- **WebRTC is likely overkill.** A wand tuning preview doesn't need the bandwidth savings. With no hardware H.264 encoder on the Pi 5, it would add CPU load and setup complexity to a realtime detection pipeline. A LAN MJPEG preview also needs no signalling or NAT handling.
- **NiceGUI is a reasonable second choice** if the project wants Python-only UI code, but test its overhead before committing.
- **Benchmark to run:** record detection loop FPS and per-core CPU with the preview off, with one phone viewing, and with three viewing, at two preview sizes.

### Gaps
- **No Pi 5 numbers** for MJPEG or WebRTC streaming from Python were found. Pi 4 notes and forum opinions are only indirect.
- **picamera2 encoders on Pi 5:** I could not confirm whether `MJPEGEncoder` is hardware-backed on Pi 5. A [fork's example](https://github.com/woutersf/picamera2/blob/main/examples/mjpeg_server_2.py) refers to a "h/w MJPEG encoder", but it does not establish Pi 5 behaviour. Assume software JPEG until measured. The project can also encode with `cv2.imencode`.
- **Official MJPEG example:** my attempts to fetch `mjpeg_server.py` from the main picamera2 repo failed (the path returned 404), so I can't describe it.
- **NiceGUI memory footprint** on a Pi was not found.

## What are the current packaging norms, and what is the state of WS2812B on Pi 5?

### Takeaway
Use apt for picamera2 and a venv created with `--system-site-packages` for everything else. Native install is easier than Docker for a CSI camera. For LEDs, staying on SPI with Pi5Neo is the lowest-risk path today and matches current code. The kernel PIO driver and Adafruit's PIO library are worth a spike, but the sources don't establish a clear winner.

### Cited Findings

**Packaging**
- The latest Raspberry Pi OS is based on Debian Trixie, and from Bookworm onwards pip installs only into a venv; otherwise it fails with `externally-managed-environment` — [Raspberry Pi docs](https://www.raspberrypi.com/documentation/computers/os.html)
- The docs say to pass `--system-site-packages` to inherit system packages — [Raspberry Pi docs](https://www.raspberrypi.com/documentation/computers/os.html)
- picamera2 recommends apt because it guarantees compatible picamera2 and libcamera versions, with `--no-install-recommends` as a reduced install for Lite — [picamera2](https://github.com/raspberrypi/picamera2)
- Wand Spell installs its full stack from apt, so `picamera2` can see system NumPy — [Wand Spell](https://github.com/Mootado/wand-spell)

**Docker and the camera**
- A libcamera developer said `/dev/media*` and `/dev/v4l-subdev*` must be passed into the container, though the reporter still couldn't enumerate cameras in that thread — [libcamera issue](https://github.com/kbingham/libcamera/issues/35) (search summary)
- Community images mount `/run/udev` read-only and pass media, video, subdev and `dma_heap` nodes, typically with `privileged: true` — [Docker Hub example](https://hub.docker.com/r/dnovischi/rpicamv3-ros-humble-node) (search summary)
- A Pi 5 user on balenaOS got "No buffers available for capture" even in privileged mode, with no answer found — [balena forum](https://forums.balena.io/t/configuring-cma-memory-and-device-access-so-an-arducam-owlsight-ov64a40-camera-works-with-libcamera-inside-a-docker-container-on-balenaos-running-on-raspberry-pi/374742) (search summary)
- I found no official Raspberry Pi guide for this setup. Wand Portal's Docker route is built around a USB camera, which sidesteps libcamera — [Wand Portal](https://github.com/mtaylor45/-SpellSight)

**WS2812B on Pi 5**

| Route | Status | Mechanism | Caveats |
|---|---|---|---|
| [Pi5Neo](https://github.com/vanshksingh/Pi5Neo) (current choice: `pi5neo` is in this repo's `install.sh`) | MIT, 52 stars, pushed 2026-03, v1.1.0 | SPI on GPIO 10 | Depends only on `spidev`; offers a context manager with cleanup and a quiet mode; high counts need a larger kernel SPI buffer (170+ LEDs) |
| [Adafruit_Blinka_Raspberry_Pi5_Neopixel](https://github.com/adafruit/Adafruit_Blinka_Raspberry_Pi5_Neopixel) | **GPL-2.0**, 5 stars, pushed 2026-10 | RP1 PIO through `/dev/pio0` | Needs recent firmware and kernel; udev rule needed if the device is root-owned |
| [`ws2812-pio` kernel overlay](https://github.com/awawa-dev/hyperhdr/wiki/Raspberry-Pi-5-PWM) | Wiki updated 2026-01-09 | `dtoverlay=ws2812-pio,gpio=18,num_leds=30`, exposes `/dev/leds0` | Wiki says root is required and that a fixed module was needed; as of Oct 2025 that meant a testing kernel via `rpi-update`, with the fix expected after 6.12.55. Verify on the current kernel |
| [rpi_ws281x](https://github.com/jgarff/rpi_ws281x) | BSD-2, 1,888 stars, pushed 2026-05 | PWM/PCM/SPI; Pi 5 needs an RP1 kernel module | Pi 5 not mentioned in the README I read; [issue #528 is still open](https://github.com/jgarff/rpi_ws281x/issues/528) |

- In #528, a September 2024 tester saw it work on 27 LEDs, but memory stress caused white flicker. Isolating a core did not help, the oscilloscope showed "huge jitter", and they concluded "LKM is probably the only way" — [issue #528](https://github.com/jgarff/rpi_ws281x/issues/528). This is two years old.
- Open follow-ups include a [Pi 5 Rev 1.1 "HW revision not supported" error (#555)](https://github.com/jgarff/rpi_ws281x/issues/555) and an [RP1 driver build failure on non-16K page kernels (#554)](https://github.com/jgarff/rpi_ws281x/issues/554) (titles only).
- The Python bindings at [rpi-ws281x-python](https://github.com/rpi-ws281x/rpi-ws281x-python) were last pushed in November 2024 (GitHub API). Beta Pi 5 bindings by Philip Howard were reported by [Hackster](https://hackster.io/news/userspace-ws281x-control-on-the-raspberry-pi-5-inches-closer-with-new-python-library-release-6c8af3e50d9e) (search summary only; the page returned 403).
- The HyperHDR wiki recommends a 3.3V-to-5V level shifter to be fully compliant with the LED spec — [HyperHDR wiki](https://github.com/awawa-dev/hyperhdr/wiki/Raspberry-Pi-5-PWM)
- A roughly 2024 thread reports that Adafruit's NeoPixel library failed on Pi 5 and that SPI was suggested as a workaround. This may predate the PIO library — [Core Electronics forum](https://forum.core-electronics.com.au/t/ws2812b-rgb-led-strips-raspberry-pi-python-issues/20458) (search summary)

### Inferences
- **Keep Pi5Neo over SPI as the default**, but hide it behind a small LED interface so PIO can be swapped in.
- **Avoid rpi_ws281x on Pi 5.** A CV workload is memory-heavy, and that is the exact condition reported to cause flicker, although that report is old.
- **Spike PIO only for a specific need**, such as using a GPIO pin other than 10. Check the strip under a real CV load for each route. Note Adafruit's GPL-2.0 licence before adopting it, since it may affect the project's licence choice.
- **Add the level shifter to the hardware docs**, since a 3.3V data line is a plausible cause of flaky strips.
- **Check SPI as an install step:** the installer should enable SPI, confirm group membership and light a test pattern, then report a clear pass or fail.
- **Avoid Docker for production use on a CSI camera.** Device passthrough is fiddly, community guidance leans on privileged mode, and there is an unresolved Pi 5 buffer report. The existing `Dockerfile.test` for tests seems fine because it doesn't need real hardware, though I did not audit it.
- **Add off-Pi modes.** A simulator or `--keyboard` mode, as in Wand Spell, lets people try the UI and integrations without hardware.

### Gaps
- **uv:** I found no sourced guidance for uv with Raspberry Pi OS and picamera2. Its handling of system site packages should be tested before it is recommended.
- **No head-to-head test** of SPI versus PIO stability under CV load on Pi 5 was found.
- **`/dev/leds0` details:** the data format and whether non-root access can be arranged were not established. "Requires root" comes from HyperHDR's wiki and may be specific to its usage.
- **Fix status:** I did not confirm which current kernel includes the `ws2812-pio` fix.
- **rpi_ws281x Pi 5 status today:** the module's current state is unclear. Issue #528's latest comments that I read are from 2024.
- **Trixie compatibility of Pi5Neo** was not separately confirmed.

## What integrations make this more useful, and what's the simplest action architecture?

### Takeaway
MQTT with Home Assistant discovery gives the widest reach for the least code, because Home Assistant then handles bulbs, Hue and everything else. Add a generic webhook and a direct WLED call, and represent everything as a small YAML mapping from spell to a list of actions.

### Cited Findings
- Home Assistant's discovery topic format is `<discovery_prefix>/<component>/[<node_id>/]<object_id>/config`, with the prefix defaulting to `homeassistant` — [HA MQTT](https://www.home-assistant.io/integrations/mqtt/)
- The MQTT `event` platform is built for stateless events. It requires `state_topic` and `event_types`, the JSON payload must contain `event_type`, extra fields become attributes, and replayed retained messages are discarded — [HA MQTT event](https://www.home-assistant.io/integrations/event.mqtt/)
- MQTT also has a `device_automation` trigger component, which suits events that only need to drive automations — [HA MQTT](https://www.home-assistant.io/integrations/mqtt/)
- Wand Portal uses a pulsing `binary_sensor.wand_<id>` per spell, a `sensor.wand_last_spell`, a retained `wand/status` with LWT, and a non-retained `wand/event` carrying JSON — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- Wand Portal warns that renaming or removing spells leaves stale retained discovery configs behind — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- Its "Send to Home Assistant" button fires an entity on demand, so an automation can be built before any training — [Wand Portal](https://github.com/mtaylor45/-SpellSight)
- WLED accepts `POST /json/state` with bodies such as `{"ps":3}` for a preset, `{"on":"t"}` to toggle and `{"seg":[{"id":0,"fx":0}]}` for an effect — [WLED JSON API](https://kno.wled.ge/interfaces/json-api/)
- WandGestureDetector's action types are MP3, video, GPIO and webhook — [WandGestureDetector](https://github.com/DanStach/WandGestureDetector)
- Frigate treats MQTT as optional, though its Home Assistant integration needs it — [Frigate](https://docs.frigate.video/frigate/installation/)

### Inferences
Suggested priority:
1. **Local effects** (LED, sound, servo), as now.
2. **MQTT with Home Assistant discovery.** Prefer a single `event` entity with spells as `event_types`, because that is what the platform is designed for. Keep a raw JSON topic for non-Home-Assistant users. Wand Portal's `binary_sensor` pulses are an alternative that makes state triggers easy, at the cost of an entity per spell and a timer.
3. **Generic webhook.** This covers IFTTT, Node-RED and custom scripts with very little code.
4. **WLED preset call.** This takes one HTTP POST, and it lets a user light up a room without wiring the Pi directly to a large strip.
5. **Hue and other smart bulbs through Home Assistant first.** Add direct support only if users without Home Assistant ask for it.

Simplest architecture:
- A cast yields one immutable event such as `{spell, confidence, duration, cast_at}`.
- A dispatcher looks up the spell in config and runs its actions from a small registry of action types.
- Actions run off the detection thread, each with a timeout, and a failure is logged without blocking other actions. A dead smart bulb must never stall recognition.
- Add a per-spell cooldown so one gesture can't fire twice.
- Provide a "Test" button for each mapping, as Wand Portal does.

```yaml
spells:
  lumos:
    min_confidence: 0.8
    cooldown_s: 2
    actions:
      - {type: led, effect: warm_glow}
      - {type: sound, file: lumos.ogg}
      - {type: mqtt_event}
      - {type: wled, host: wled-lounge.local, preset: 3}
      - {type: webhook, url: "http://nodered.local/wand"}
```

This schema is my own illustration, not taken from a project. Avoid a general rules engine or plugin system at this stage, since Home Assistant or Node-RED already covers conditional logic.

### Gaps
- **Philips Hue:** the developer page returned a login wall, so local API authentication and any current limits are unverified.
- **MQTT broker for non-HA users:** whether to bundle Mosquitto was not researched.
- **Evidence of demand:** I found no data on which integrations users actually want. This ranking is a judgment based on reach and effort.

## What are the licensing and IP considerations? (Not legal advice)

### Takeaway
**This is not legal advice; consult a lawyer before any commercial release.** The most concrete problem is not Harry Potter but licensing: the README defers to an upstream project that has no licence, which leaves redistribution permission unclear. For branding, staying non-commercial and avoiding franchise names in the project name and any audio from the films reduces risk but does not remove it.

### Cited Findings
- The upstream repo has no licence: the GitHub licence API returned 404 for [Gloworm72/InteractiveWand](https://github.com/Gloworm72/InteractiveWand). This repo has no LICENSE file at its root, and its README says "See the original project for license details" (checked locally, README.md line 291).
- GitHub's terms let others view and fork a public repo, but "this does not imply that you are permitted to use, modify, or share the software for any purpose". Without a licence, users generally lack that permission and should ask the maintainers to add one — [Choose a License](https://choosealicense.com/no-permission/)
- Warner Bros. filed a DMCA notice against a 2018 Kickstarter for its use of a book title from the films, and the campaign was renamed afterwards — [TorrentFreak](https://torrentfreak.com/?p=165478) (search summary)
- An unauthorised Harry Potter-themed game project was removed from crowdfunding after a takedown notice in 2015 — [World IP Review](https://www.worldipreview.com/news/warner-bros-sees-no-magic-in-unauthorised-harry-potter-game-8016) (search summary)
- Warner Bros. has said it objects when fan gatherings become a vehicle for unauthorised commercial activity — [Above the Law](https://abovethelaw.com/2018/06/warner-bros-turns-harry-potter-fan-events-into-events-for-the-franchise-that-must-not-be-named/) (search summary)
- Kano's wand was sold under a brand licence with Warner Bros., so the official-looking route was licensed. Kano's CEO was also granted a patent in April 2022 covering the wand's gesture recognition system, and Warner Bros. called Kano's claims "without merit" — [TechCrunch](https://techcrunch.com/2023/01/27/warner-bros-swiped-our-harry-potter-wand-ip-says-kano/)
- Wand Spell uses its own spell names (Tide, Flame, Frost, Strike) and generated tones, with `.ogg` drop-ins for users' own audio — [Wand Spell](https://github.com/Mootado/wand-spell). Other projects use the franchise spell names openly, such as [Wand Portal](https://github.com/mtaylor45/-SpellSight).

### Inferences
- **First step:** ask Andrew Congdon (Gloworm72) to add a licence or give written permission, covering code, the dataset, the `.pkl` model and sounds. If he declines, the derived parts can't be clearly redistributed, and a clean rewrite and a new dataset may be needed. This also matters for any Python file derived from upstream.
- **Audit `Sounds/` for provenance.** Clips from the films or games would be the clearest risk, so replace them with original or properly licensed audio. Keep a record of each file's source. I did not inspect these files.
- **Lower-risk theming:** use a neutral project name such as the existing "Interactive Wand", and call gestures something generic, with user-editable display names. Avoid franchise logos and images. Add a line saying the project is unofficial and unaffiliated. A disclaimer doesn't grant rights, but it does reduce confusion.
- **Commercial use changes the picture.** Selling kits, images or a crowdfunded version attracts more attention than a free hobby repo, based on the takedown examples above.
- **Third-party wands:** instructions for use with a Universal wand seem lower-risk than using its brand in the project's name, but no source I found addresses this directly.

### Gaps
- **Spell names:** I found no authoritative source on whether individual spell names are protected or how a hobby project's use of them is treated. Takedown evidence involves titles and commercial crowdfunding.
- **No takedowns of wand repos were found.** Several wand repos with franchise wording are public, but that does not show they are permitted.
- **Patent scope:** the Kano patent's claims, jurisdiction and current status were not reviewed. They may be irrelevant to camera-based systems, but this has not been established.
- **Jurisdiction:** these notes draw mainly on US and UK examples.
