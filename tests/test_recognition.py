#!/usr/bin/env python3
"""
Recognition Tests

Proves the classifier sees the same input at any on-screen size or position,
and that an outdated model is refused. Needs cv2 and scikit-learn, so it skips
outside Docker; `make test-docker` is the authoritative run.
"""

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cv2
    import joblib
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    from harry_potter_wand_sklearn import _model_cache, get_model, predict_spell
except ImportError:
    print("SKIPPED: tests/test_recognition.py needs cv2 and scikit-learn")
    sys.exit(0)

from utils.casting import PREPROCESS_VERSION, normalize_ink, trace_to_input

DATASET = PROJECT_ROOT / "DatasetCreation"
FRAME = (480, 640)
MIN_ACCURACY = 0.95
SIZES = (60, 100, 150, 300, 480)
# Largest mean pixel difference (out of 255) allowed between renders of one shape.
MAX_RENDER_DIFFERENCE = 3.5


def load_samples():
    return np.load(DATASET / "X_spells.npy"), np.load(DATASET / "y_spells.npy")


def normalized(samples):
    return np.array([normalize_ink(s.reshape(28, 28)).ravel() for s in samples])


def train(samples, labels):
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="poly", C=0.1, gamma=0.01, degree=2)),
    ])
    model.fit(normalized(samples), labels)
    return model


def place_on_frame(sample, size, top, left):
    """Draw a dataset sample at a given on-screen size and position."""
    frame = np.zeros(FRAME, dtype=np.uint8)
    frame[top:top + size, left:left + size] = cv2.resize(
        sample.reshape(28, 28), (size, size), interpolation=cv2.INTER_LINEAR)
    return frame


def placements(size):
    max_top, max_left = FRAME[0] - size, FRAME[1] - size
    return {
        "centred": (max_top // 2, max_left // 2),
        "top-left": (0, 0),
        "bottom-right": (max_top, max_left),
    }


def test_accuracy_holds_at_every_size_and_position():
    X, y = load_samples()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = train(X_train, y_train)

    worst = 1.0
    for size in SIZES:
        for name, (top, left) in placements(size).items():
            inputs = np.array([
                normalize_ink(place_on_frame(s, size, top, left)).ravel() for s in X_test
            ])
            accuracy = (model.predict(inputs) == y_test).mean()
            print(f"  {size:>3} px {name:<13} accuracy {accuracy:.3f}")
            assert accuracy >= MIN_ACCURACY, f"{accuracy:.3f} at {size} px {name}"
            worst = min(worst, accuracy)
    print(f"  worst accuracy {worst:.3f}")


def test_same_shape_gives_same_input_at_any_scale_and_offset():
    angles = np.linspace(0, 2 * np.pi, 60)
    shape = np.stack([np.cos(angles), np.sin(angles) * 0.7], axis=1)

    def render(scale, offset_x, offset_y):
        points = [(int(x * scale + offset_x), int(y * scale + offset_y), 0.0) for x, y in shape]
        return trace_to_input(points).astype(float)

    reference = render(200, 300, 240)
    worst = 0.0
    for scale, offset_x, offset_y in ((40, 60, 60), (70, 500, 400), (120, 200, 150), (230, 320, 240)):
        worst = max(worst, np.abs(render(scale, offset_x, offset_y) - reference).mean())
    print(f"  worst mean difference {worst:.2f}")
    assert worst < MAX_RENDER_DIFFERENCE, f"inputs differ by {worst:.2f}"


def expect_refused(path):
    _model_cache.clear()
    try:
        get_model(path)
    except ValueError as e:
        assert "train_spell_classifier.py" in str(e), f"no training command in: {e}"
    else:
        raise AssertionError("outdated model should be refused")


def test_outdated_models_are_refused_and_current_models_load():
    X, y = load_samples()
    model = train(X[::10], y[::10])

    with tempfile.TemporaryDirectory() as tmp:
        unwrapped = Path(tmp) / "unwrapped.pkl"
        joblib.dump(model, unwrapped)
        expect_refused(unwrapped)

        wrong = Path(tmp) / "wrong.pkl"
        joblib.dump({"model": model, "preprocess_version": PREPROCESS_VERSION - 1}, wrong)
        expect_refused(wrong)

        current = Path(tmp) / "current.pkl"
        joblib.dump({"model": model, "preprocess_version": PREPROCESS_VERSION}, current)
        _model_cache.clear()
        assert get_model(current) is not None

        png = Path(tmp) / "sample.png"
        cv2.imwrite(str(png), X[0].reshape(28, 28))
        assert predict_spell(str(png), current) in (0, 1)


def test_blank_image_is_refused():
    try:
        normalize_ink(np.zeros((28, 28), dtype=np.uint8))
    except ValueError:
        return
    raise AssertionError("blank input should raise ValueError")


def test_trace_with_no_extent_renders_without_error():
    image = trace_to_input([(50, 50, 0.0)] * 3)
    assert image.shape == (28, 28)


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
