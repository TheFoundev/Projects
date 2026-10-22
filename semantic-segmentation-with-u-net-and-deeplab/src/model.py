"""A small U-Net and a short training loop."""
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


def build_unet(size=32):
    inputs = layers.Input((size, size, 1))
    c1 = layers.Conv2D(8, 3, activation="relu", padding="same")(inputs)
    c1 = layers.Conv2D(8, 3, activation="relu", padding="same")(c1)
    p1 = layers.MaxPooling2D()(c1)

    c2 = layers.Conv2D(16, 3, activation="relu", padding="same")(p1)
    p2 = layers.MaxPooling2D()(c2)

    c3 = layers.Conv2D(32, 3, activation="relu", padding="same")(p2)
    u1 = layers.UpSampling2D()(c3)
    u1 = layers.Concatenate()([u1, c2])
    u1 = layers.Conv2D(16, 3, activation="relu", padding="same")(u1)

    u2 = layers.UpSampling2D()(u1)
    u2 = layers.Concatenate()([u2, c1])
    u2 = layers.Conv2D(8, 3, activation="relu", padding="same")(u2)

    outputs = layers.Conv2D(1, 1, activation="sigmoid")(u2)
    return models.Model(inputs, outputs, name="tiny_unet")


def dice_score(truth, prediction, threshold=0.5):
    predicted = prediction > threshold
    truth = truth > 0.5
    intersection = np.logical_and(predicted, truth).sum()
    total = predicted.sum() + truth.sum()
    return float(2 * intersection / total) if total else 1.0


def train(data, quick=False):
    tf.random.set_seed(3)
    model = build_unet(data["size"])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.fit(
        data["X_train"], data["y_train"],
        epochs=1 if quick else 5,
        batch_size=8,
        verbose=0,
    )

    prediction = model.predict(data["X_test"], verbose=0)
    dice = float(np.mean([dice_score(truth, pred) for truth, pred in zip(data["y_test"], prediction)]))
    pixel_accuracy = float(np.mean((prediction > 0.5) == (data["y_test"] > 0.5)))
    return model, {
        "dice": round(dice, 4),
        "pixel_accuracy": round(pixel_accuracy, 4),
        "test_images": int(len(data["X_test"])),
        "epochs": 1 if quick else 5,
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    prediction = model.predict(data["X_test"][:3], verbose=0)
    print(f"Dice: {metrics['dice']:.3f}, pixel accuracy: {metrics['pixel_accuracy']:.3f}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(7, 7))
    for row in range(3):
        axes[row, 0].imshow(data["X_test"][row, :, :, 0], cmap="gray")
        axes[row, 1].imshow(data["y_test"][row, :, :, 0], cmap="gray")
        axes[row, 2].imshow(prediction[row, :, :, 0], cmap="gray")
        for axis in axes[row]:
            axis.axis("off")
    axes[0, 0].set_title("image")
    axes[0, 1].set_title("truth")
    axes[0, 2].set_title("prediction")
    fig.tight_layout()
    fig.savefig("artifacts/unet_predictions.png", dpi=110)
    plt.close(fig)
