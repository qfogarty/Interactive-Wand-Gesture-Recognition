#!/usr/bin/env python3
"""
Casting Logic Tests

Trace timing, spell decisions, attempt logging and camera controls.
Needs no camera, cv2 or GUI, because hardware starts when the main script is imported.
"""

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.camera import build_camera_controls
from utils.casting import (
    BUSY_OUTCOME,
    COMPLETE,
    TOO_SHORT,
    TOO_SMALL,
    WAND_LEFT,
    CastOutcome,
    TraceEnd,
    TraceTracker,
    decide_spell,
    format_attempt,
    rejected_outcome,
)

STILLNESS = 1.0
ALL_CONTROLS = {
    "AeEnable", "ExposureTime", "AnalogueGain", "FrameDurationLimits",
    "Brightness", "AfMode", "LensPosition",
}
FULL_CAMERA = {
    "exposure_time": 9000, "analogue_gain": 7.5, "brightness": -0.2,
    "frame_rate": 50, "lens_position": 2.0,
}


def make_tracker():
    return TraceTracker(
        presence_duration=0.6,
        stillness_duration=STILLNESS,
        motion_radius=15,
        min_trace_size=40,
    )


class Script:
    """Feeds a tracker a timed sequence of positions at a fixed update rate."""

    def __init__(self, tracker, fps=30, start=100.0):
        self.tracker = tracker
        self.dt = 1.0 / fps
        self.now = start
        self.ends = []

    def step(self, position):
        end = self.tracker.update(position, self.now)
        if end:
            self.ends.append((end, self.now))
        self.now += self.dt
        return end

    def hold(self, position, seconds):
        for _ in range(int(round(seconds / self.dt))):
            if self.step(position):
                return

    def move(self, start, end, speed):
        """Move in a straight line at speed pixels per second."""
        distance = math.hypot(end[0] - start[0], end[1] - start[1])
        updates = max(1, int(distance / (speed * self.dt)))
        for i in range(1, updates + 1):
            self.step((start[0] + (end[0] - start[0]) * i / updates,
                       start[1] + (end[1] - start[1]) * i / updates))

    def start_trace(self, position=(100, 100)):
        """Show the wand long enough, then move it until the trace starts."""
        self.hold(position, 0.7)
        x, y = position
        self.move((x, y), (x + 20, y), speed=100)
        assert self.tracker.tracing, "trace should have started"
        return (x + 20, y)


def test_slow_stroke_starts_and_completes():
    # 3 px per update at 30 updates per second never passed the old speed gate.
    script = Script(make_tracker(), fps=30)
    script.hold((100, 100), 0.7)
    script.move((100, 100), (300, 100), speed=90)
    assert script.tracker.tracing, "slow stroke should start a trace"
    script.hold((300, 100), STILLNESS + 0.1)
    assert len(script.ends) == 1
    assert script.ends[0][0].reason == COMPLETE


def test_end_time_does_not_depend_on_frame_rate():
    end_times = {}
    for fps in (15, 30, 60):
        script = Script(make_tracker(), fps=fps)
        script.hold((100, 100), 0.7)
        script.move((100, 100), (300, 100), speed=200)
        moved_until = script.now
        script.hold((300, 100), STILLNESS + 0.5)
        assert script.ends, f"no end at {fps} updates per second"
        assert script.ends[0][0].reason == COMPLETE
        end_times[fps] = script.ends[0][1] - moved_until

    for fps, elapsed in end_times.items():
        assert abs(elapsed - STILLNESS) <= 2.0 / fps, f"{fps} updates/s ended after {elapsed}"


def test_wand_vanishing_after_start_is_too_short():
    # This path built a mask from a None frame and crashed.
    script = Script(make_tracker())
    script.start_trace()
    script.hold(None, STILLNESS + 0.1)
    assert len(script.ends) == 1
    assert script.ends[0][0].reason == TOO_SHORT


def test_second_trace_has_none_of_the_first_traces_points():
    # This path classified the previous gesture's frame again.
    script = Script(make_tracker())
    position = script.start_trace()
    script.move(position, (300, 300), speed=300)
    script.hold((300, 300), STILLNESS + 0.1)
    assert script.ends[0][0].reason == COMPLETE
    first_points = script.ends[0][0].points

    script.hold(None, 1.1)  # cooldown
    script.start_trace((400, 50))
    script.hold(None, STILLNESS + 0.1)

    assert len(script.ends) == 2
    second = script.ends[1][0]
    assert second.reason == TOO_SHORT
    assert not set(second.points) & set(first_points)


def test_wand_leaving_mid_gesture_is_classified():
    script = Script(make_tracker())
    position = script.start_trace()
    script.move(position, (300, 300), speed=300)
    script.hold(None, STILLNESS + 0.1)
    assert len(script.ends) == 1
    assert script.ends[0][0].reason == WAND_LEFT


def test_short_pause_mid_gesture_does_not_end_it():
    script = Script(make_tracker())
    position = script.start_trace()
    script.move(position, (200, 100), speed=300)
    script.hold((200, 100), STILLNESS - 0.3)
    script.move((200, 100), (200, 300), speed=300)
    assert not script.ends, "a pause under stillness_duration must not end the trace"
    script.hold((200, 300), STILLNESS + 0.1)
    assert len(script.ends) == 1
    assert script.ends[0][0].reason == COMPLETE
    assert max(p[1] for p in script.ends[0][0].points) == 300


def test_brief_detection_loss_mid_gesture_does_not_end_it():
    script = Script(make_tracker())
    position = script.start_trace()
    script.move(position, (200, 100), speed=300)
    script.hold(None, STILLNESS - 0.3)
    script.move((200, 100), (200, 300), speed=300)
    assert not script.ends


def test_small_flick_is_too_small():
    script = Script(make_tracker())
    script.hold((100, 100), 0.7)
    script.move((100, 100), (125, 100), speed=30)
    script.hold((125, 100), STILLNESS + 0.1)
    assert len(script.ends) == 1
    assert script.ends[0][0].reason == TOO_SMALL


def test_cooldown_starts_nothing_and_does_not_restart_on_a_hold():
    script = Script(make_tracker())
    position = script.start_trace()
    script.move(position, (300, 300), speed=300)
    script.hold((300, 300), STILLNESS + 0.1)
    assert len(script.ends) == 1

    # Waving during the cooldown is ignored.
    script.move((300, 300), (100, 100), speed=800)
    assert not script.tracker.tracing

    # Holding still after the cooldown never starts another trace.
    script.hold((100, 100), 3.0)
    assert not script.tracker.tracing
    assert len(script.ends) == 1


def test_presence_is_required_before_a_trace_starts():
    script = Script(make_tracker())
    script.move((100, 100), (130, 100), speed=300)
    assert not script.tracker.tracing, "fast motion before presence_duration must not start"
    script.hold(None, 0.1)
    script.move((100, 100), (130, 100), speed=300)
    assert not script.tracker.tracing, "losing the wand restarts the presence time"


def test_nan_position_counts_as_no_detection():
    script = Script(make_tracker())
    script.start_trace()
    before = list(script.tracker.points)
    script.step((float("nan"), float("nan")))
    assert script.tracker.points == before


def test_every_prediction_and_state_combination():
    assert decide_spell("0", 0) == ("spell", "Alohamora!", 1)
    assert decide_spell("1", 1) == ("spell", "Colloportus!", 0)
    assert decide_spell("0", 1) == ("ignored", "Already open: cast Colloportus", 1)
    assert decide_spell("1", 0) == ("ignored", "Already closed: cast Alohamora", 0)


def test_unknown_prediction_is_an_error():
    try:
        decide_spell("2", 0)
    except ValueError as e:
        assert "2" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_rejected_traces_have_messages_and_classifiable_traces_do_not():
    assert rejected_outcome(TraceEnd([], TOO_SHORT)).message == "Too short: draw the whole shape"
    assert rejected_outcome(TraceEnd([], TOO_SMALL)).message == "Too small: draw bigger"
    assert rejected_outcome(TraceEnd([], COMPLETE)) is None
    assert rejected_outcome(TraceEnd([], WAND_LEFT)) is None
    assert BUSY_OUTCOME.message == "Busy: try again"


def test_attempt_line_keeps_what_tuning_needs():
    trace = TraceEnd([(1, 2, 3.5), (4, 5, 3.6)], COMPLETE)
    outcome = CastOutcome("spell", "Alohamora!", prediction="0")
    line = format_attempt(trace, outcome, {"exposure_time": 8000}, wall_time=12.0)
    assert "\n" not in line
    parsed = json.loads(line)
    assert parsed == {
        "time": 12.0,
        "reason": COMPLETE,
        "outcome": "spell",
        "prediction": "0",
        "points": [[1, 2, 3.5], [4, 5, 3.6]],
        "camera": {"exposure_time": 8000},
    }


def test_camera_config_values_reach_the_controls():
    controls = build_camera_controls(FULL_CAMERA, ALL_CONTROLS)
    assert controls["AeEnable"] is False
    assert controls["ExposureTime"] == 9000
    assert controls["AnalogueGain"] == 7.5
    assert controls["Brightness"] == -0.2
    assert controls["FrameDurationLimits"] == (20000, 20000)
    assert controls["AfMode"] == 0
    assert controls["LensPosition"] == 2.0


def test_null_exposure_restores_auto_exposure():
    controls = build_camera_controls({**FULL_CAMERA, "exposure_time": None}, ALL_CONTROLS)
    for name in ("AeEnable", "ExposureTime", "AnalogueGain"):
        assert name not in controls, f"{name} should be left to auto exposure"
    assert controls["Brightness"] == -0.2


def test_camera_without_autofocus_gets_no_focus_controls():
    controls = build_camera_controls(FULL_CAMERA, ALL_CONTROLS - {"AfMode", "LensPosition"})
    assert "AfMode" not in controls
    assert "LensPosition" not in controls
    assert controls["ExposureTime"] == 9000


def test_config_missing_newer_keys_still_builds():
    controls = build_camera_controls({"exposure_time": 8000}, ALL_CONTROLS)
    assert controls["FrameDurationLimits"] == (33333, 33333)
    assert controls["LensPosition"] == 1.0


def main():
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, test in tests:
        try:
            test()
            print(f"✓ {name}")
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
    print(f"\nSummary: {len(tests) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
