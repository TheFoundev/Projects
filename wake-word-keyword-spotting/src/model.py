"""Binary classifier for the wake phrase."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

def train(data, quick=False):
    model = RandomForestClassifier(n_estimators=60 if quick else 180, max_depth=10, random_state=4)
    model.fit(data["X_train"], data["y_train"])
    prediction = model.predict(data["X_test"])
    negatives = data["y_test"] == 0
    false_positive_rate = float(np.mean(prediction[negatives] == 1)) if negatives.any() else 0.0
    return model, {
        "accuracy": round(float(accuracy_score(data["y_test"], prediction)), 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "positive_clips": int((data["y_train"] == 1).sum()),
        "negative_clips": int((data["y_train"] == 0).sum()),
    }

def demo(data):
    from src.data import features, wake_clip, negative_clip

    model, metrics = train(data, quick=True)
    positive = model.predict(features(wake_clip(seed=999)).reshape(1, -1))[0]
    negative = model.predict(features(negative_clip(seed=1000)).reshape(1, -1))[0]
    print(f"Wake clip detected: {bool(positive)}")
    print(f"Background clip detected: {bool(negative)}")
    print(f"Test accuracy: {metrics['accuracy']:.3f}, false-positive rate: {metrics['false_positive_rate']:.3f}")
