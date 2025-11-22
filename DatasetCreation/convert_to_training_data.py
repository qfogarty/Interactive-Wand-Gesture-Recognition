import os
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# === Load configuration or use dynamic paths ===
try:
    # Add parent directory to path to import config_loader
    parent_dir = Path(__file__).parent.parent.resolve()
    sys.path.insert(0, str(parent_dir))
    from config_loader import get_config
    config = get_config()
    dataset_dir = Path(config.paths.dataset_dir)
except (ImportError, SystemExit):
    # Fallback to dynamic path resolution
    dataset_dir = Path(__file__).parent.resolve()

# Folder containing your drawn spell images
INPUT_DIR = str(dataset_dir / "spells_dataset")
IMG_SIZE = 28

# Storage for image data and labels
data = []
labels = []

# Loop through all images in the folder
for file in os.listdir(INPUT_DIR):
    if file.endswith(".png"):
        # Assign labels: 0 = open, 1 = close
        label = 0 if "open" in file.lower() else 1
        path = os.path.join(INPUT_DIR, file)

        # Read and flatten image
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue  # Skip unreadable files
        flat = img.flatten()
        data.append(flat)
        labels.append(label)

# Convert to NumPy arrays
X = np.array(data)
y = np.array(labels)

# Save as .npy
np.save(str(dataset_dir / "X_spells.npy"), X)
np.save(str(dataset_dir / "y_spells.npy"), y)

# Optionally save as CSV (for inspection or SVM training)
df = pd.DataFrame(X)
df.insert(0, "label", y)
df.to_csv(str(dataset_dir / "spells_dataset.csv"), index=False)

print(f"✅ Saved: {len(X)} samples")
print("🧠 Training data saved as X_spells.npy, y_spells.npy, and spells_dataset.csv")
