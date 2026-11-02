"""
Renders docs/images/gesture-card.png from real training samples.

The image is committed so the docs need no runtime dependency. Rerun this after
changing the dataset: python3 DatasetCreation/render_gesture_card.py
"""

from pathlib import Path

import cv2
import numpy as np

DATASET_DIR = Path(__file__).parent.resolve()
OUTPUT = DATASET_DIR.parent / "docs" / "images" / "gesture-card.png"

SPELLS = [(0, "Alohamora (open) - cast first"), (1, "Colloportus (close)")]
SAMPLES_PER_SPELL = 4
SAMPLE_SIZE = 168
GAP = 12
LABEL_HEIGHT = 44


def main():
    X = np.load(DATASET_DIR / "X_spells.npy")
    y = np.load(DATASET_DIR / "y_spells.npy")

    width = SAMPLES_PER_SPELL * SAMPLE_SIZE + (SAMPLES_PER_SPELL + 1) * GAP
    row_height = LABEL_HEIGHT + SAMPLE_SIZE + GAP
    card = np.full((row_height * len(SPELLS), width), 255, dtype=np.uint8)

    for row, (label, name) in enumerate(SPELLS):
        top = row * row_height
        cv2.putText(card, name, (GAP, top + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2, cv2.LINE_AA)

        samples = X[y == label]
        picks = np.linspace(0, len(samples) - 1, SAMPLES_PER_SPELL).astype(int)
        for column, pick in enumerate(picks):
            image = cv2.resize(samples[pick].reshape(28, 28), (SAMPLE_SIZE, SAMPLE_SIZE),
                               interpolation=cv2.INTER_NEAREST)
            left = GAP + column * (SAMPLE_SIZE + GAP)
            card[top + LABEL_HEIGHT:top + LABEL_HEIGHT + SAMPLE_SIZE, left:left + SAMPLE_SIZE] = image

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT), card)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
