"""
Spell prediction using scikit-learn classifier.

Performance optimizations:
- Model caching to avoid repeated disk I/O
- Direct array prediction to skip image file roundtrip
"""

from PIL import Image
import numpy as np
import joblib

# Model cache - avoids reloading from disk on every prediction
_model_cache = {}


def get_model(model_path):
    """Load and cache the sklearn model."""
    if model_path not in _model_cache:
        _model_cache[model_path] = joblib.load(model_path)
    return _model_cache[model_path]


def predict_spell_from_array(img_array, model_path):
    """
    Predict spell from numpy array directly (avoids disk I/O).

    Args:
        img_array: Grayscale numpy array (any shape, will be flattened)
        model_path: Path to the sklearn model file

    Returns:
        Prediction result (0 = open spell, 1 = close spell)
    """
    clf = get_model(model_path)
    # Flatten to 1D vector for sklearn
    img = img_array.reshape(1, -1)
    prediction = clf.predict(img)
    return prediction[0]


def predict_spell(img_path, model_path):
    """
    Predict spell from image file (original API, kept for compatibility).

    Args:
        img_path: Path to grayscale image file
        model_path: Path to the sklearn model file

    Returns:
        Prediction result (0 = open spell, 1 = close spell)
    """
    # Open the image from the given path and convert it to grayscale
    img = Image.open(img_path).convert("L")

    # Convert the image to a NumPy array and flatten it to a 1D vector
    img = np.array(img).reshape(1, -1)

    # Load the pre-trained classifier model (cached)
    clf = get_model(model_path)

    # Predict the class and return the result
    prediction = clf.predict(img)
    return prediction[0]


# === Script entry point (used when run directly) ===
if __name__ == "__main__":
    # Load configuration or use dynamic paths
    try:
        from config_loader import get_config
        config = get_config()
        img_path = str(config.paths.lastframe)
        model_path = str(config.paths.model)
    except (ImportError, SystemExit):
        # Fallback to dynamic path resolution
        from pathlib import Path
        project_root = Path(__file__).parent.resolve()
        img_path = str(project_root / "lastframe.jpg")
        model_path = str(project_root / "new_custom_classifier.pkl")

    # Call the prediction function and print the result
    result = predict_spell(img_path, model_path)
    print(result)
