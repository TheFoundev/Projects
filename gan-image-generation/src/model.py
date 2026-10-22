"""A compact Keras GAN for 16x16 shapes."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


def build_generator(latent=12):
    return models.Sequential([
        layers.Input(shape=(latent,)),
        layers.Dense(4 * 4 * 64),
        layers.LeakyReLU(negative_slope=0.2),
        layers.Reshape((4, 4, 64)),
        layers.Conv2DTranspose(32, 3, strides=2, padding="same"),
        layers.LeakyReLU(negative_slope=0.2),
        layers.Conv2DTranspose(1, 3, strides=2, padding="same", activation="tanh"),
    ], name="generator")


def build_discriminator(size=16):
    return models.Sequential([
        layers.Input(shape=(size, size, 1)),
        layers.Conv2D(32, 3, strides=2, padding="same"),
        layers.LeakyReLU(negative_slope=0.2),
        layers.Conv2D(64, 3, strides=2, padding="same"),
        layers.LeakyReLU(negative_slope=0.2),
        layers.Flatten(),
        layers.Dense(1, activation="sigmoid"),
    ], name="discriminator")


def train(data, quick=False):
    tf.random.set_seed(7)
    images = data["images"]
    latent = 12
    steps = 6 if quick else 90
    batch_size = 16

    generator = build_generator(latent)
    discriminator = build_discriminator(data["size"])

    discriminator.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3, beta_1=0.5),
        loss="binary_crossentropy",
    )

    discriminator.trainable = False
    gan = models.Sequential([generator, discriminator])
    gan.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3, beta_1=0.5),
        loss="binary_crossentropy",
    )

    rng = np.random.default_rng(1)
    d_loss = g_loss = 0.0
    for step in range(steps):
        indices = rng.integers(0, len(images), batch_size)
        real = images[indices]
        noise = rng.normal(0, 1, (batch_size, latent)).astype("float32")
        fake = generator.predict(noise, verbose=0)

        discriminator.trainable = True
        d_real = discriminator.train_on_batch(real, np.ones((batch_size, 1)))
        d_fake = discriminator.train_on_batch(fake, np.zeros((batch_size, 1)))
        d_loss = 0.5 * (d_real + d_fake)

        discriminator.trainable = False
        noise = rng.normal(0, 1, (batch_size, latent)).astype("float32")
        g_loss = gan.train_on_batch(noise, np.ones((batch_size, 1)))

    samples = generator.predict(rng.normal(0, 1, (8, latent)).astype("float32"), verbose=0)
    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 4, figsize=(8, 4))
    for axis, sample in zip(axes.ravel(), samples):
        axis.imshow(sample[:, :, 0], cmap="gray", vmin=-1, vmax=1)
        axis.axis("off")
    fig.suptitle("Generated shapes")
    fig.tight_layout()
    fig.savefig("artifacts/gan_samples.png", dpi=110)
    plt.close(fig)

    return generator, {
        "discriminator_loss": round(float(d_loss), 4),
        "generator_loss": round(float(g_loss), 4),
        "steps": steps,
        "training_images": int(len(images)),
    }


def demo(data):
    images = data["images"]
    print(f"Training set: {images.shape[0]} images of {data['size']}x{data['size']}.")
    print("Shapes are circles and rectangles; pixel values are scaled to [-1, 1].")
    print("Run `python main.py train` to train and write artifacts/gan_samples.png.")
