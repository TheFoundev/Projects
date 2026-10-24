"""Random forest digit classifier over synthetic audio features."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

from src.data import DIGITS, features, synthesize


def train(data, quick=False):
    model = RandomForestClassifier(
        n_estimators=60 if quick else 180,
        max_depth=10,
        random_state=3,
    )
    model.fit(data["X_train"], data["y_train"])
    predictions = model.predict(data["X_test"])
    accuracy = accuracy_score(data["y_test"], predictions)
    matrix = confusion_matrix(data["y_test"], predictions, labels=list(range(len(DIGITS))))
    per_class = np.diag(matrix) / np.maximum(1, matrix.sum(axis=1))
    return model, {
        "accuracy": round(float(accuracy), 4),
        "worst_digit": DIGITS[int(np.argmin(per_class))],
        "train_samples": int(len(data["y_train"])),
        "test_samples": int(len(data["y_test"])),
    }


def demo(data):
    model, metrics = train(data, quick=True)
    signal = synthesize("seven", seed=999)
    prediction = model.predict(features(signal).reshape(1, -1))[0]
    print(f"Generated the word 'seven'. Predicted: {DIGITS[int(prediction)]}")
    print(f"Quick-test accuracy: {metrics['accuracy']:.3f}")
    print("(Synthetic tones only; this is not a general speech recognizer.)")
