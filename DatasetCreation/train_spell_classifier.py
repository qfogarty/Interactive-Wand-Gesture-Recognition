import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

# === Load configuration or use dynamic paths ===
try:
    # Add parent directory to path to import config_loader
    parent_dir = Path(__file__).parent.parent.resolve()
    sys.path.insert(0, str(parent_dir))
    from config_loader import get_config
    config = get_config()
    dataset_dir = Path(config.paths.dataset_dir)
    output_path = config.paths.model
except (ImportError, SystemExit):
    # Fallback to dynamic path resolution
    dataset_dir = Path(__file__).parent.resolve()
    output_path = dataset_dir.parent / "new_custom_classifier.pkl"

# === Load saved training data ===
X = np.load(str(dataset_dir / "X_spells.npy"))  # shape: (num_samples, 784)
y = np.load(str(dataset_dir / "y_spells.npy"))  # labels: 0 = open, 1 = close

# === Split into training and testing sets ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# === Define a pipeline with scaling and classifier ===
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', SVC())
])

# === Define a hyperparameter grid for tuning ===
param_grid = {
    'clf__kernel': ['rbf', 'poly', 'sigmoid'],
    'clf__C': [0.1, 1, 10, 100],
    'clf__gamma': ['scale', 'auto', 0.01, 0.001, 0.0001],
    'clf__degree': [2, 3, 4]  # Only used for 'poly' kernel
}

# === Perform grid search ===
print("Performing hyperparameter tuning with GridSearchCV...")
grid = GridSearchCV(pipeline, param_grid, cv=5, n_jobs=-1, verbose=2)
grid.fit(X_train, y_train)

# === Evaluate performance ===
y_pred = grid.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nBest Parameters: {grid.best_params_}")
print(f"Model accuracy: {accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# === Save the best model ===
joblib.dump(grid.best_estimator_, str(output_path), compress=3)
print(f"Model saved as {output_path}")
