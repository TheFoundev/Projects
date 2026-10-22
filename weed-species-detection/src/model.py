"""Random forest over hand-built leaf features."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

def train(data, quick=False):
    model = RandomForestClassifier(n_estimators=60 if quick else 180, max_depth=8, random_state=8)
    model.fit(data["X_train"], data["y_train"])
    prediction = model.predict(data["X_test"])
    matrix = confusion_matrix(data["y_test"], prediction, labels=list(range(len(data["species"]))))
    per_class = np.diag(matrix) / np.maximum(1, matrix.sum(axis=1))
    return model, {
        "accuracy": round(float(accuracy_score(data["y_test"], prediction)), 4),
        "worst_species": data["species"][int(np.argmin(per_class))],
        "best_species": data["species"][int(np.argmax(per_class))],
        "test_leaves": int(len(data["y_test"])),
    }

def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    sample = data["X_test"][0].reshape(1, -1)
    prediction = model.predict(sample)[0]
    print(f"Predicted species: {data['species'][int(prediction)]}")
    print(f"Test accuracy: {metrics['accuracy']:.3f}, weakest: {metrics['worst_species']}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(8, 2.4))
    for axis, image in zip(axes, data["images"][:4]):
        axis.imshow(image, cmap="gray")
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/leaf_samples.png", dpi=110)
    plt.close(fig)
