from PIL import Image
import numpy as np
import joblib

# === Function to perform spell prediction ===
def predict_spell(img_path, model_path):
    # Open the image from the given path and convert it to grayscale
    img = Image.open(img_path).convert("L")
    
    # Convert the image to a NumPy array and flatten it to a 1D vector (shape: 1 x 784)
    img = np.array(img).reshape(1, -1)
    
    # Load the pre-trained classifier model from disk
    clf = joblib.load(model_path)
    
    # Predict the class (0 = open spell, 1 = close spell) and return the result
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
