"""Multi-output random forest for two face attributes."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.multioutput import MultiOutputClassifier


def train(data, quick=False):
    targets_train = np.column_stack([data["y_glasses_train"], data["y_smile_train"]])
    targets_test = np.column_stack([data["y_glasses_test"], data["y_smile_test"]])

    model = MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=50 if quick else 160,
            max_depth=8,
            random_state=11,
        )
    )
    model.fit(data["X_train"], targets_train)
    predictions = model.predict(data["X_test"])

    return model, {
        "glasses_accuracy": round(float(accuracy_score(targets_test[:, 0], predictions[:, 0])), 4),
        "smile_accuracy": round(float(accuracy_score(targets_test[:, 1], predictions[:, 1])), 4),
        "samples": int(len(data["X_test"])),
    }


def demo(data):
    model, metrics = train(data, quick=True)
    sample = data["sample_image"].reshape(1, -1)
    prediction = model.predict(sample)[0]
    print(f"Sample truth: {data['sample_true']}")
    print(f"Prediction: glasses={bool(prediction[0])}, smiling={bool(prediction[1])}")
    print(f"Test accuracy: glasses={metrics['glasses_accuracy']:.2f}, smile={metrics['smile_accuracy']:.2f}")
