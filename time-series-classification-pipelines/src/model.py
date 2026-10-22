"""Features plus a random forest."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix


def extract(series):
    spectrum = np.abs(np.fft.rfft(series))
    frequencies = np.fft.rfftfreq(len(series))
    dominant = float(frequencies[int(np.argmax(spectrum[1:]) + 1)]) if len(spectrum) > 1 else 0.0
    return [
        float(series.mean()),
        float(series.std()),
        float(np.max(series) - np.min(series)),
        float(np.mean(np.abs(np.diff(series)))),
        float(np.mean(np.abs(np.diff(np.sign(series))))),
        dominant,
        float(np.max(spectrum) / (np.sum(spectrum) + 1e-9)),
    ]


def featurize(X):
    return np.asarray([extract(series) for series in X])


def train(data, quick=False):
    model = RandomForestClassifier(n_estimators=50 if quick else 160, max_depth=8, random_state=9)
    model.fit(featurize(data["X_train"]), data["y_train"])
    prediction = model.predict(featurize(data["X_test"]))
    matrix = confusion_matrix(data["y_test"], prediction)
    return model, {
        "accuracy": round(float(accuracy_score(data["y_test"], prediction)), 4),
        "sine_correct": int(matrix[0, 0]),
        "square_correct": int(matrix[1, 1]),
        "trend_correct": int(matrix[2, 2]),
        "test_series": int(len(data["y_test"])),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    sample = data["X_test"][0]
    prediction = model.predict(featurize([sample]))[0]
    print(f"Predicted {data['classes'][int(prediction)]}; true {data['classes'][int(data['y_test'][0])]}")
    print(f"Test accuracy: {metrics['accuracy']:.2f}")
    print("Per-class correct:", metrics["sine_correct"], metrics["square_correct"], metrics["trend_correct"])

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(9, 2.8))
    for label, axis in enumerate(axes):
        sample_index = int(np.where(data["y_test"] == label)[0][0])
        axis.plot(data["X_test"][sample_index])
        axis.set_title(data["classes"][label])
    fig.tight_layout()
    fig.savefig("artifacts/series_classes.png", dpi=110)
    plt.close(fig)
