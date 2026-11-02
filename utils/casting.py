"""
Spell casting logic that needs no camera, GUI or audio.

The point list is the single source of truth for a trace: TraceTracker decides
when a trace starts and ends, trace_to_input turns its points into the
classifier's image, and every ended trace becomes one CastOutcome.

cv2 is imported inside the image functions so the tracker runs without it.
"""

import json
import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Stored in the model file by train_spell_classifier.py. Bump it whenever the
# classifier's input changes, so older models are refused at launch.
PREPROCESS_VERSION = 2

INPUT_SIZE = 28
# Matches the drawing canvas and stroke in DatasetCreation/draw_spell_data.py.
CANVAS_SIZE = 300
STROKE_THICKNESS = 7
# Fraction of the larger side left empty around the ink.
INK_MARGIN = 0.1

COMPLETE = "complete"
WAND_LEFT = "wand_left"
TOO_SHORT = "too_short"
TOO_SMALL = "too_small"

Point = Tuple[int, int, float]


@dataclass(frozen=True)
class TraceEnd:
    """A finished trace: its (x, y, t) points and why it ended."""

    points: List[Point]
    reason: str


class TraceTracker:
    """Turns a stream of wand positions into traces, using real timestamps."""

    def __init__(self, presence_duration, stillness_duration, motion_radius,
                 min_trace_size, min_points=10, cooldown=1.0):
        self.presence_duration = presence_duration
        self.stillness_duration = stillness_duration
        self.motion_radius = motion_radius
        self.min_trace_size = min_trace_size
        self.min_points = min_points
        self.cooldown = cooldown

        self.points: List[Point] = []
        self.tracing = False
        self._first_seen = None  # (x, y, t) of the current continuous presence
        self._anchor = None      # (x, y, t) the wand has stayed near
        self._last_seen = None
        self._cooldown_until = None

    def update(self, position, now) -> Optional[TraceEnd]:
        """Feed one frame's position (or None). Returns a TraceEnd when a trace ends."""
        if self._cooldown_until is not None:
            if now < self._cooldown_until:
                return None
            self._cooldown_until = None

        if position is not None and any(math.isnan(v) for v in position):
            position = None

        if self.tracing:
            return self._update_tracing(position, now)
        self._update_waiting(position, now)
        return None

    def _update_waiting(self, position, now):
        if position is None:
            self._first_seen = None
            return

        x, y = position
        if self._first_seen is None:
            self._first_seen = (x, y, now)
            return

        first_x, first_y, first_t = self._first_seen
        present_long_enough = now - first_t >= self.presence_duration
        if present_long_enough and math.hypot(x - first_x, y - first_y) > self.motion_radius:
            self.tracing = True
            self.points = [(int(x), int(y), now)]
            self._anchor = (x, y, now)
            self._last_seen = now

    def _update_tracing(self, position, now):
        if position is None:
            if now - self._last_seen >= self.stillness_duration:
                return self._end(WAND_LEFT, now)
            return None

        x, y = position
        self.points.append((int(x), int(y), now))
        self._last_seen = now

        anchor_x, anchor_y, anchor_t = self._anchor
        if math.hypot(x - anchor_x, y - anchor_y) > self.motion_radius:
            self._anchor = (x, y, now)
        elif now - anchor_t >= self.stillness_duration:
            return self._end(COMPLETE, now)
        return None

    def _end(self, reason, now):
        points = self.points
        if len(points) < self.min_points:
            reason = TOO_SHORT
        elif _larger_side(points) < self.min_trace_size:
            reason = TOO_SMALL

        self.points = []
        self.tracing = False
        self._first_seen = None
        self._anchor = None
        self._last_seen = None
        self._cooldown_until = now + self.cooldown
        return TraceEnd(points=points, reason=reason)


def _larger_side(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def normalize_ink(image):
    """Centre a grayscale image's ink in a square and resize it to the model's input.

    Training and live casting both pass through here, so the classifier only
    ever sees shape, never on-screen size or position.
    """
    import cv2
    import numpy as np

    rows = np.any(image > 0, axis=1)
    cols = np.any(image > 0, axis=0)
    if not rows.any():
        raise ValueError("Cannot normalize a blank image")

    top, bottom = np.where(rows)[0][[0, -1]]
    left, right = np.where(cols)[0][[0, -1]]
    ink = image[top:bottom + 1, left:right + 1]

    height, width = ink.shape
    side = max(height, width)
    margin = max(1, int(round(side * INK_MARGIN)))
    full = side + 2 * margin
    square = np.zeros((full, full), dtype=image.dtype)
    y = (full - height) // 2
    x = (full - width) // 2
    square[y:y + height, x:x + width] = ink

    return cv2.resize(square, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_AREA)


def trace_to_input(points):
    """Render trace points the way training samples were drawn, then normalize.

    Scaling to a fixed canvas before drawing keeps the stroke thickness relative
    to the gesture the same at any on-screen size.
    """
    import cv2
    import numpy as np

    canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8)
    if not points:
        raise ValueError("Cannot render a trace with no points")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    usable = CANVAS_SIZE - 2 * STROKE_THICKNESS
    scale = usable / max(max(xs) - min(xs), max(ys) - min(ys), 1)

    pixels = [
        (int(round(STROKE_THICKNESS + (x - min(xs)) * scale)),
         int(round(STROKE_THICKNESS + (y - min(ys)) * scale)))
        for x, y in zip(xs, ys)
    ]
    for start, end in zip(pixels, pixels[1:] or pixels):
        cv2.line(canvas, start, end, 255, STROKE_THICKNESS)

    return normalize_ink(canvas)


@dataclass(frozen=True)
class CastOutcome:
    """What the person sees for one ended trace."""

    kind: str  # spell, ignored, rejected, busy or error
    message: str
    input_image: object = None
    prediction: Optional[str] = None


REJECTED_MESSAGES = {
    TOO_SHORT: "Too short: draw the whole shape",
    TOO_SMALL: "Too small: draw bigger",
}

BUSY_OUTCOME = CastOutcome("busy", "Busy: try again")


def rejected_outcome(trace_end) -> Optional[CastOutcome]:
    """The outcome for a trace that never reaches the classifier, or None if it should."""
    message = REJECTED_MESSAGES.get(trace_end.reason)
    return CastOutcome("rejected", message) if message else None


def decide_spell(prediction, last_move):
    """Apply the open-then-close order. Returns (kind, message, new_last_move)."""
    if prediction == "0":
        if last_move == 0:
            return "spell", "Alohamora!", 1
        return "ignored", "Already open: cast Colloportus", last_move
    if prediction == "1":
        if last_move == 1:
            return "spell", "Colloportus!", 0
        return "ignored", "Already closed: cast Alohamora", last_move
    raise ValueError(f"Unknown prediction: {prediction}")


def format_attempt(trace_end, outcome, camera_settings, wall_time=None) -> str:
    """One JSON line describing an ended trace, for tuning from real wand data."""
    return json.dumps({
        "time": time.time() if wall_time is None else wall_time,
        "reason": trace_end.reason,
        "outcome": outcome.kind,
        "prediction": outcome.prediction,
        "points": trace_end.points,
        "camera": camera_settings,
    })
